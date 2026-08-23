"""Data quality assessment module for rule-based error detection and quality scoring."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Union

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Canonical domain values
VALID_STATUSES: Set[str] = {"closed", "open", "pending", "in progress", "resolved"}
VALID_PRIORITIES: Set[str] = {"low", "medium", "high", "critical", "urgent"}
CANONICAL_CATEGORIES: Set[str] = {
    "technical support",
    "billing",
    "hardware",
    "general inquiry",
    "security alert",
    "account access",
}

# Current reference timestamp for detecting future dates
CURRENT_REFERENCE_DATE = pd.Timestamp("2026-08-22")


@dataclass
class QualityAnomaly:
    """Represents an identified data quality defect."""

    rule_name: str
    severity: str  # 'CRITICAL', 'MAJOR', 'MINOR'
    affected_rows: List[int]
    column: str
    description: str
    sample_values: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Complete summary of quality audit findings and composite score."""

    dataset_name: str
    total_records: int
    quality_score: float  # 0.0 to 100.0
    anomalies: List[QualityAnomaly] = field(default_factory=list)
    total_anomalies: int = 0
    clean_records_count: int = 0
    clean_records_pct: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DataQualityAssessor:
    """Production quality assessment engine executing deterministic quality rules."""

    def __init__(
        self,
        df: pd.DataFrame,
        dataset_name: str = "case_management_raw.csv",
        reference_date: pd.Timestamp = CURRENT_REFERENCE_DATE,
    ) -> None:
        """Initialize the quality assessor with target dataset.

        Args:
            df: Raw DataFrame to assess.
            dataset_name: Human-readable dataset identifier.
            reference_date: Benchmark timestamp for temporal bounds.
        """
        self.df = df.copy()
        self.dataset_name = dataset_name
        self.reference_date = reference_date

    def _get_clean_str_series(self, col_name: str) -> pd.Series:
        """Helper to return trimmed string series with NaN handled."""
        if col_name not in self.df.columns:
            return pd.Series([""] * len(self.df), index=self.df.index)
        return self.df[col_name].fillna("").astype(str).str.strip()

    def check_missing_identifiers(self) -> Optional[QualityAnomaly]:
        """Detect records with missing or empty case_id primary keys."""
        if "case_id" not in self.df.columns:
            return None
        series = self._get_clean_str_series("case_id")
        bad_mask = series.eq("") | series.str.lower().isin(["nan", "none", "null"])
        bad_indices = self.df.index[bad_mask].tolist()

        if bad_indices:
            return QualityAnomaly(
                rule_name="missing_case_id",
                severity="CRITICAL",
                affected_rows=bad_indices,
                column="case_id",
                description=f"Found {len(bad_indices)} records missing required primary key `case_id`.",
                sample_values=[f"Row {idx}" for idx in bad_indices[:5]],
            )
        return None

    def check_duplicate_case_ids(self) -> Optional[QualityAnomaly]:
        """Detect duplicate non-empty case_id values."""
        if "case_id" not in self.df.columns:
            return None
        series = self._get_clean_str_series("case_id")
        non_empty = series[series != ""]
        dupe_mask = non_empty.duplicated(keep=False)
        bad_indices = non_empty.index[dupe_mask].tolist()

        if bad_indices:
            sample_ids = non_empty.loc[bad_indices].unique()[:5].tolist()
            return QualityAnomaly(
                rule_name="duplicate_case_id",
                severity="MAJOR",
                affected_rows=bad_indices,
                column="case_id",
                description=f"Found {len(bad_indices)} records with non-unique `case_id` values.",
                sample_values=[str(v) for v in sample_ids],
            )
        return None

    def check_duplicate_cases(self) -> Optional[QualityAnomaly]:
        """Detect semantic duplicate cases based on normalized client, category, and intake date."""
        req_cols = ["client_name", "category", "intake_date"]
        if not all(col in self.df.columns for col in req_cols):
            return None

        # Normalized tuple for semantic matching
        norm_client = self._get_clean_str_series("client_name").str.lower().str.replace(r"\s+", " ", regex=True)
        norm_cat = self._get_clean_str_series("category").str.lower().str.replace(r"[\s_-]+", "", regex=True)
        norm_date = self._get_clean_str_series("intake_date")

        combined = pd.DataFrame({"client": norm_client, "cat": norm_cat, "date": norm_date})
        # Filter out empty records
        valid_mask = (norm_client != "") & (norm_cat != "") & (norm_date != "")
        dupes = combined[valid_mask].duplicated(keep=False)
        bad_indices = combined[valid_mask].index[dupes].tolist()

        if bad_indices:
            return QualityAnomaly(
                rule_name="semantic_duplicate_case",
                severity="MAJOR",
                affected_rows=bad_indices,
                column="client_name + category + intake_date",
                description=f"Found {len(bad_indices)} records representing duplicate case submissions.",
                sample_values=[f"Row {idx}" for idx in bad_indices[:5]],
            )
        return None

    def check_dates_validity(self) -> List[QualityAnomaly]:
        """Check for unparseable dates, impossible dates, future dates, and negative durations."""
        anomalies: List[QualityAnomaly] = []
        intake_raw = self._get_clean_str_series("intake_date")
        closure_raw = self._get_clean_str_series("closure_date")

        # 1. Parse intake dates
        parsed_intake = pd.to_datetime(intake_raw, format="mixed", errors="coerce")
        intake_unparseable = intake_raw.index[(intake_raw != "") & parsed_intake.isna()].tolist()
        if intake_unparseable:
            anomalies.append(
                QualityAnomaly(
                    rule_name="invalid_intake_date_format",
                    severity="CRITICAL",
                    affected_rows=intake_unparseable,
                    column="intake_date",
                    description=f"Found {len(intake_unparseable)} records with unparseable or impossible `intake_date`.",
                    sample_values=intake_raw.loc[intake_unparseable].unique()[:5].tolist(),
                )
            )

        # 2. Parse closure dates
        parsed_closure = pd.to_datetime(closure_raw, format="mixed", errors="coerce")
        closure_unparseable = closure_raw.index[(closure_raw != "") & parsed_closure.isna()].tolist()
        if closure_unparseable:
            anomalies.append(
                QualityAnomaly(
                    rule_name="invalid_closure_date_format",
                    severity="CRITICAL",
                    affected_rows=closure_unparseable,
                    column="closure_date",
                    description=f"Found {len(closure_unparseable)} records with unparseable or impossible `closure_date`.",
                    sample_values=closure_raw.loc[closure_unparseable].unique()[:5].tolist(),
                )
            )

        # 3. Future dates
        future_intake = parsed_intake.index[parsed_intake > self.reference_date].tolist()
        if future_intake:
            anomalies.append(
                QualityAnomaly(
                    rule_name="future_intake_date",
                    severity="CRITICAL",
                    affected_rows=future_intake,
                    column="intake_date",
                    description=f"Found {len(future_intake)} records with intake date beyond current reference date ({self.reference_date.date()}).",
                    sample_values=intake_raw.loc[future_intake].unique()[:5].tolist(),
                )
            )

        # 4. Negative duration (closure < intake)
        valid_both = parsed_intake.notna() & parsed_closure.notna()
        negative_dur = self.df.index[valid_both & (parsed_closure < parsed_intake)].tolist()
        if negative_dur:
            anomalies.append(
                QualityAnomaly(
                    rule_name="negative_resolution_duration",
                    severity="CRITICAL",
                    affected_rows=negative_dur,
                    column="intake_date -> closure_date",
                    description=f"Found {len(negative_dur)} records where closure date precedes intake date.",
                    sample_values=[f"Row {idx} (Intake: {intake_raw.loc[idx]}, Closure: {closure_raw.loc[idx]})" for idx in negative_dur[:5]],
                )
            )

        return anomalies

    def check_invalid_status(self) -> Optional[QualityAnomaly]:
        """Detect records with invalid status enumeration values."""
        if "status" not in self.df.columns:
            return None
        series = self._get_clean_str_series("status")
        lower_series = series.str.lower()
        invalid_mask = (series != "") & (~lower_series.isin(VALID_STATUSES))
        bad_indices = self.df.index[invalid_mask].tolist()

        if bad_indices:
            sample_vals = series.loc[bad_indices].unique()[:5].tolist()
            return QualityAnomaly(
                rule_name="invalid_status_enum",
                severity="MAJOR",
                affected_rows=bad_indices,
                column="status",
                description=f"Found {len(bad_indices)} records with invalid status values.",
                sample_values=sample_vals,
            )
        return None

    def check_invalid_priority(self) -> Optional[QualityAnomaly]:
        """Detect records with invalid priority enumeration values."""
        if "priority" not in self.df.columns:
            return None
        series = self._get_clean_str_series("priority")
        lower_series = series.str.lower()
        invalid_mask = (series != "") & (~lower_series.isin(VALID_PRIORITIES))
        bad_indices = self.df.index[invalid_mask].tolist()

        if bad_indices:
            sample_vals = series.loc[bad_indices].unique()[:5].tolist()
            return QualityAnomaly(
                rule_name="invalid_priority_enum",
                severity="MAJOR",
                affected_rows=bad_indices,
                column="priority",
                description=f"Found {len(bad_indices)} records with invalid priority values.",
                sample_values=sample_vals,
            )
        return None

    def check_category_problems(self) -> Optional[QualityAnomaly]:
        """Detect unstandardized category strings (missing, dirty casing, irregular separators)."""
        if "category" not in self.df.columns:
            return None
        series = self._get_clean_str_series("category")
        missing_cat = series.eq("")
        # Clean canonical form
        clean_cat = series.str.lower().str.replace(r"[\s_-]+", " ", regex=True).str.strip()
        unrecognized = ~clean_cat.isin(CANONICAL_CATEGORIES)

        bad_mask = missing_cat | unrecognized
        bad_indices = self.df.index[bad_mask].tolist()

        if bad_indices:
            sample_vals = series.loc[bad_indices].unique()[:5].tolist()
            return QualityAnomaly(
                rule_name="unstandardized_or_missing_category",
                severity="MINOR",
                affected_rows=bad_indices,
                column="category",
                description=f"Found {len(bad_indices)} records with unstandardized, dirty, or missing category values.",
                sample_values=sample_vals,
            )
        return None

    def check_contact_counts(self) -> Optional[QualityAnomaly]:
        """Detect negative or impossible outlier contact count metrics."""
        if "contact_count" not in self.df.columns:
            return None
        series = self._get_clean_str_series("contact_count")
        numeric_contacts = pd.to_numeric(series, errors="coerce")
        bad_mask = (series != "") & (numeric_contacts.isna() | (numeric_contacts < 0) | (numeric_contacts > 1000))
        bad_indices = self.df.index[bad_mask].tolist()

        if bad_indices:
            sample_vals = series.loc[bad_indices].unique()[:5].tolist()
            return QualityAnomaly(
                rule_name="invalid_contact_count_bounds",
                severity="MAJOR",
                affected_rows=bad_indices,
                column="contact_count",
                description=f"Found {len(bad_indices)} records with negative, non-numeric, or extreme outlier contact counts.",
                sample_values=sample_vals,
            )
        return None

    def assess(self) -> QualityReport:
        """Run the comprehensive quality assessment rules engine.

        Returns:
            QualityReport: Generated diagnostic audit report.
        """
        logger.info(f"Executing Data Quality Rules Engine on '{self.dataset_name}' ({len(self.df)} records)...")
        anomalies: List[QualityAnomaly] = []

        # Run checks
        for check_fn in [
            self.check_missing_identifiers,
            self.check_duplicate_case_ids,
            self.check_duplicate_cases,
            self.check_invalid_status,
            self.check_invalid_priority,
            self.check_category_problems,
            self.check_contact_counts,
        ]:
            anomaly = check_fn()
            if anomaly:
                anomalies.append(anomaly)

        # Date checks return a list
        anomalies.extend(self.check_dates_validity())

        # Calculate affected unique row indices
        all_affected_rows: Set[int] = set()
        for anom in anomalies:
            all_affected_rows.update(anom.affected_rows)

        total_records = len(self.df)
        clean_records_count = max(0, total_records - len(all_affected_rows))
        clean_pct = round((clean_records_count / total_records) * 100.0, 2) if total_records > 0 else 0.0

        # Calculate weighted quality score (0 to 100)
        # Penalties: Critical = 3.0, Major = 1.5, Minor = 0.5 per defect instance
        total_penalty = 0.0
        for anom in anomalies:
            weight = 3.0 if anom.severity == "CRITICAL" else (1.5 if anom.severity == "MAJOR" else 0.5)
            total_penalty += len(anom.affected_rows) * weight

        max_penalty = max(1.0, total_records * 3.0)
        quality_score = max(0.0, round(100.0 - (total_penalty / max_penalty) * 100.0, 2))

        report = QualityReport(
            dataset_name=self.dataset_name,
            total_records=total_records,
            quality_score=quality_score,
            anomalies=anomalies,
            total_anomalies=len(anomalies),
            clean_records_count=clean_records_count,
            clean_records_pct=clean_pct,
        )

        logger.info(
            f"Quality Assessment completed: {len(anomalies)} anomaly rules triggered. "
            f"Quality Score: {quality_score}/100. Clean records: {clean_records_count}/{total_records} ({clean_pct}%)."
        )
        return report

    def export_markdown(
        self, report: QualityReport, output_path: Union[str, Path] = "reports/exports/data_quality_report.md"
    ) -> Path:
        """Export data quality findings and recommendations as a structured Markdown document.

        Args:
            report: QualityReport object.
            output_path: Target file destination.

        Returns:
            Path: Written markdown file path.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = [
            f"# Data Quality Assessment Report: `{report.dataset_name}`",
            "",
            f"**Audit Timestamp:** {report.generated_at}",
            "",
            "## 1. Executive Quality Scorecard",
            "",
            "| Metric | Assessment Result | Status |",
            "| :--- | :--- | :--- |",
            f"| **Overall Quality Score** | **{report.quality_score} / 100.0** | {'🟢 HEALTHY' if report.quality_score >= 85 else ('🟡 ACTION REQUIRED' if report.quality_score >= 60 else '🔴 CRITICAL DEGRADATION')} |",
            f"| **Total Evaluated Records** | {report.total_records:,} | Base cohort |",
            f"| **Clean / Flawless Records** | {report.clean_records_count:,} ({report.clean_records_pct}%) | Verified intact |",
            f"| **Defect Rules Triggered** | {report.total_anomalies} anomaly types | Actionable findings |",
            "",
            "## 2. Identified Data Quality Anomalies",
            "",
            "| Severity | Anomaly Rule | Target Column | Affected Rows | Description |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for anom in sorted(report.anomalies, key=lambda x: (0 if x.severity == "CRITICAL" else (1 if x.severity == "MAJOR" else 2))):
            severity_badge = f"**{anom.severity}**"
            lines.append(
                f"| {severity_badge} | `{anom.rule_name}` | `{anom.column}` | {len(anom.affected_rows)} | {anom.description} |"
            )

        lines.extend([
            "",
            "## 3. Deep-Dive Anomaly Breakdown & Samples",
            "",
        ])

        for anom in report.anomalies:
            lines.append(f"### Rule: `{anom.rule_name}` (Severity: {anom.severity})")
            lines.append(f"- **Target Column:** `{anom.column}`")
            lines.append(f"- **Impact:** {len(anom.affected_rows)} rows affected ({round((len(anom.affected_rows)/report.total_records)*100, 2)}% of dataset)")
            lines.append(f"- **Finding:** {anom.description}")
            if anom.sample_values:
                lines.append(f"- **Sample Values Identified:** {', '.join([f'`{s}`' for s in anom.sample_values])}")
            lines.append("")

        lines.extend([
            "## 4. Remediation & Defensive Cleaning Protocol",
            "",
            "1. **Immutability Protection:** Retain raw dataset without direct alteration.",
            "2. **Primary Key Sanitation:** Flag or drop records with missing `case_id` during cleaning pipeline while logging row drops in `cleaning_log.csv`.",
            "3. **Date Harmonization:** Parse multi-format dates to ISO standard (`YYYY-MM-DD`); reject impossible dates or negative durations.",
            "4. **Categorical Normalization:** Canonicalize casing/whitespace for known categories and preserve unresolved novel categories explicitly.",
            "5. **Numeric Bounding:** Clamp or nullify impossible negative or spam contact counts.",
            "",
        ])

        content = "\n".join(lines)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Exported data quality markdown report to: {path.resolve()}")
        return path


def run_quality_assessment(
    df: pd.DataFrame,
    dataset_name: str = "case_management_raw.csv",
    output_path: Union[str, Path] = "reports/exports/data_quality_report.md",
) -> QualityReport:
    """Convenience helper to run quality assessment and export markdown report.

    Args:
        df: Input DataFrame.
        dataset_name: Identifier for dataset.
        output_path: Target report path.

    Returns:
        QualityReport: Structured quality assessment report.
    """
    assessor = DataQualityAssessor(df=df, dataset_name=dataset_name)
    report = assessor.assess()
    assessor.export_markdown(report=report, output_path=output_path)
    return report
