"""Analytical limitations boundary analysis module.

Formally documents the inferential boundaries, unmeasured confounders,
missing variables, and unsupported conclusions for each business question.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LimitationItem:
    """Atomic limitation record with category, description, and severity."""

    category: str  # 'DATA_GAP', 'CONFOUNDING', 'INFERENCE_BOUNDARY', 'MISSING_VARIABLE'
    severity: str  # 'HIGH', 'MEDIUM', 'LOW'
    description: str
    affected_questions: List[str]
    mitigation: str
    future_data_needed: Optional[str] = None


@dataclass
class AnalyticalLimitationsReport:
    """Consolidated formal limitations boundary analysis."""

    dataset_limitations: List[LimitationItem] = field(default_factory=list)
    q1_limitations: List[LimitationItem] = field(default_factory=list)
    q2_limitations: List[LimitationItem] = field(default_factory=list)
    q3_limitations: List[LimitationItem] = field(default_factory=list)
    unsupported_conclusions: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: pd.Timestamp.now().isoformat())

    @property
    def all_limitations(self) -> List[LimitationItem]:
        """Aggregate all limitation items across all scopes."""
        return (
            self.dataset_limitations
            + self.q1_limitations
            + self.q2_limitations
            + self.q3_limitations
        )

    @property
    def high_severity_count(self) -> int:
        """Count high severity limitations."""
        return sum(1 for lim in self.all_limitations if lim.severity == "HIGH")

    @property
    def total_limitation_count(self) -> int:
        """Total limitation items across all scopes."""
        return len(self.all_limitations)


class LimitationsAnalyzer:
    """Formal limitations boundary analysis engine.

    Enumerates inferential boundaries, confounders, missing variables,
    and explicitly states which conclusions are NOT supported by the data.
    """

    def __init__(
        self,
        cleaned_df: pd.DataFrame,
        raw_record_count: int = 120,
        clean_record_count: int = 113,
    ) -> None:
        """Initialize with clean analytical dataset.

        Args:
            cleaned_df: Validated, deduplicated analytical DataFrame.
            raw_record_count: Raw input row count before cleaning.
            clean_record_count: Post-cleaning analytical row count.
        """
        self.df = cleaned_df.copy()
        self.raw_count = raw_record_count
        self.clean_count = clean_record_count
        self.attrition_pct = round((raw_record_count - clean_record_count) / max(raw_record_count, 1) * 100, 2)

    def _dataset_limitations(self) -> List[LimitationItem]:
        """Enumerate dataset-level limitations across all questions."""
        items: List[LimitationItem] = []

        items.append(LimitationItem(
            category="DATA_GAP",
            severity="HIGH",
            description=(
                f"Small sample size: only {self.clean_count} usable analytical records after cleaning "
                f"(from {self.raw_count} raw rows with {self.attrition_pct}% attrition). "
                "Sub-group analyses (e.g., category × priority interactions) are underpowered."
            ),
            affected_questions=["Q1", "Q2", "Q3"],
            mitigation="Treated all main effects cautiously; avoided 3-way interaction models.",
            future_data_needed="Minimum 500+ closed cases per sub-group for interaction modelling.",
        ))

        items.append(LimitationItem(
            category="DATA_GAP",
            severity="HIGH",
            description=(
                "Single data snapshot: the dataset is a cross-sectional extract with no versioning. "
                "Historical backfills, retroactive status changes, or agent re-assignments are invisible."
            ),
            affected_questions=["Q1", "Q3"],
            mitigation="Treated intake_date as the analysis anchor; closure_date drives duration computation.",
            future_data_needed="Event log / CDC stream with full lifecycle state transitions.",
        ))

        items.append(LimitationItem(
            category="MISSING_VARIABLE",
            severity="HIGH",
            description=(
                "No agent or team identifier: cases cannot be attributed to individual agents or teams, "
                "preventing isolation of staffing quality, training effects, or queue routing biases from trend signals."
            ),
            affected_questions=["Q1", "Q2", "Q3"],
            mitigation="Aggregated all analyses at case level; treated team variance as residual noise.",
            future_data_needed="Agent ID, team ID, and shift schedule fields.",
        ))

        items.append(LimitationItem(
            category="MISSING_VARIABLE",
            severity="MEDIUM",
            description=(
                "No SLA tier or contractual priority target: the dataset lacks any record of the SLA commitment "
                "for each case, making it impossible to measure SLA breach rates or distinguish latency from breach."
            ),
            affected_questions=["Q2", "Q3"],
            mitigation="Used raw duration_days as a proxy; flagged interpretation as latency, not breach.",
            future_data_needed="SLA tier code, target resolution hours, and breach flag.",
        ))

        items.append(LimitationItem(
            category="MISSING_VARIABLE",
            severity="MEDIUM",
            description=(
                "No queue wait time: duration_days captures total case lifetime from intake to closure, "
                "conflating active agent work time with passive queue wait time, holiday delays, and customer response latency."
            ),
            affected_questions=["Q1", "Q2"],
            mitigation="Reported total lifecycle duration with explicit caveat that it is not pure labor time.",
            future_data_needed="First-touch timestamp, agent-active minutes, customer-response wait minutes.",
        ))

        items.append(LimitationItem(
            category="CONFOUNDING",
            severity="MEDIUM",
            description=(
                "Seasonality and calendar effects are uncontrolled: the 12-month observation window may "
                "contain holiday slowdowns, fiscal quarter surges, or product release incident spikes that "
                "create spurious longitudinal trend signals."
            ),
            affected_questions=["Q1"],
            mitigation=(
                "Linear regression captures an average linear slope; no harmonic seasonal decomposition performed "
                "due to insufficient repeated cycles (< 2 full seasonal periods)."
            ),
            future_data_needed="3+ years of longitudinal data for STL seasonal decomposition.",
        ))

        return items

    def _q1_limitations(self) -> List[LimitationItem]:
        """Enumerate limitations specific to Q1 (Closure Time Trends)."""
        items: List[LimitationItem] = []

        items.append(LimitationItem(
            category="INFERENCE_BOUNDARY",
            severity="HIGH",
            description=(
                "Open/active cases are right-censored: cases still open at data extraction appear in the dataset "
                "without a closure_date. They are correctly excluded from trend analysis, but this creates "
                "an artificial deflation of recent cohort closure times if the latest months have proportionally more open cases."
            ),
            affected_questions=["Q1"],
            mitigation="Explicitly restricted trend analysis to closed cases only; noted potential right-censoring bias.",
            future_data_needed="Survival analysis (Kaplan-Meier) with censoring indicator for open cases.",
        ))

        items.append(LimitationItem(
            category="CONFOUNDING",
            severity="MEDIUM",
            description=(
                "Category mix shift over time: if Hardware cases (highest mean duration ~21 days) became "
                "disproportionately more frequent in later cohorts, the apparent closure time increase may be a "
                "composition effect rather than a true operational slowdown."
            ),
            affected_questions=["Q1"],
            mitigation="Acknowledged in Q2 findings; category-controlled regression was performed in Q2.",
            future_data_needed="Monthly category volume breakdown to detect intake mix drift.",
        ))

        return items

    def _q2_limitations(self) -> List[LimitationItem]:
        """Enumerate limitations specific to Q2 (Duration Drivers)."""
        items: List[LimitationItem] = []

        items.append(LimitationItem(
            category="CONFOUNDING",
            severity="HIGH",
            description=(
                "Hardware RMA (Return Merchandise Authorization) logistics inflate duration independently of agent effort: "
                "Hardware cases require physical device replacement/repair cycles that are constrained by vendor "
                "turnaround time, not agent labor. This external dependency is not captured in the dataset and "
                "artificially elevates the 'Hardware' category coefficient in the OLS model."
            ),
            affected_questions=["Q2"],
            mitigation="Flagged Hardware as a structured external-dependency category in all driver interpretations.",
            future_data_needed="Vendor RMA ticket ID and expected turnaround SLA per Hardware case.",
        ))

        items.append(LimitationItem(
            category="INFERENCE_BOUNDARY",
            severity="MEDIUM",
            description=(
                "OLS regression assumes linear additive effects. Interaction effects between category and priority "
                "(e.g., Critical Hardware vs Critical Billing) are not modelled due to insufficient sample size "
                "in each interaction cell."
            ),
            affected_questions=["Q2"],
            mitigation="Reported main effects only; stated that interaction interpretation requires larger N.",
            future_data_needed="Minimum 30 cases per category × priority interaction cell.",
        ))

        items.append(LimitationItem(
            category="MISSING_VARIABLE",
            severity="MEDIUM",
            description=(
                "Contact count direction is ambiguous: high contact_count may indicate complex cases that naturally "
                "require more interactions, or it may indicate poor first-contact resolution quality. The causal "
                "direction cannot be established without recording whether contacts were initiated by the agent or customer."
            ),
            affected_questions=["Q2"],
            mitigation="Reported Spearman correlation only; explicitly avoided claiming causal direction.",
            future_data_needed="Contact initiator flag (agent vs customer), contact channel, and resolution flag per contact.",
        ))

        return items

    def _q3_limitations(self) -> List[LimitationItem]:
        """Enumerate limitations specific to Q3 (Triage Effectiveness)."""
        items: List[LimitationItem] = []

        items.append(LimitationItem(
            category="CONFOUNDING",
            severity="HIGH",
            description=(
                "Triage assignment is not random: cases were triaged based on undocumented routing criteria. "
                "If triaged cases systematically received lower complexity issues (or conversely, were assigned to "
                "senior agents), the observed duration reduction is confounded by case complexity and agent skill—not "
                "purely triage routing effectiveness."
            ),
            affected_questions=["Q3"],
            mitigation=(
                "Controlled for category distribution within High/Critical priority subset; "
                "explicitly noted non-randomisation as a threat to causal interpretation."
            ),
            future_data_needed="Randomised triage assignment experiment or propensity score matching on case complexity.",
        ))

        items.append(LimitationItem(
            category="DATA_GAP",
            severity="HIGH",
            description=(
                "No triage timestamp: the 'triaged' boolean field indicates whether triage occurred, but not "
                "when triage was completed relative to intake. The routing speed benefit of triage cannot be "
                "isolated from agent work speed on the triaged case."
            ),
            affected_questions=["Q3"],
            mitigation="Treated triage as a binary treatment indicator; cannot decompose triage-routing-time vs agent-time.",
            future_data_needed="triage_completed_at timestamp to compute time-to-triage as a separate metric.",
        ))

        items.append(LimitationItem(
            category="CONFOUNDING",
            severity="MEDIUM",
            description=(
                "Untriaged High/Critical cohort is disproportionately skewed toward Hardware cases: "
                "the observed longer duration in untriaged cases may be driven by vendor RMA delays for Hardware "
                "tickets rather than a genuine absence-of-triage effect on agent efficiency."
            ),
            affected_questions=["Q3"],
            mitigation="Identified and reported category distribution within triaged vs untriaged cohorts; reflected in confidence penalty.",
            future_data_needed="Category-stratified triage comparison with Hardware cases separated.",
        ))

        return items

    def _unsupported_conclusions(self) -> List[str]:
        """Enumerate conclusions that are EXPLICITLY not supported by this data."""
        return [
            "CANNOT CONCLUDE: That agent performance has degraded over the observation period. "
            "The trend increase in closure time is equally consistent with a case complexity mix shift toward Hardware tickets.",

            "CANNOT CONCLUDE: That triage is causally responsible for improved High/Critical resolution speed. "
            "Triage assignment was not randomised; selection bias and agent-skill confounding are plausible alternative explanations.",

            "CANNOT CONCLUDE: That contact_count is a measure of poor service quality or agent inefficiency. "
            "High contact volume may legitimately reflect deep technical troubleshooting on complex cases.",

            "CANNOT CONCLUDE: That the observed trends will persist into the next period. "
            "With fewer than 12 monthly cohorts and no seasonal decomposition, extrapolation is statistically unjustified.",

            "CANNOT CONCLUDE: That Security Alert cases resolve rapidly due to higher prioritisation or staffing. "
            "The low duration may reflect automated resolution tooling or selective case creation bias in this category.",
        ]

    def generate_report(self) -> AnalyticalLimitationsReport:
        """Build the full analytical limitations boundary report.

        Returns:
            AnalyticalLimitationsReport: Complete structured limitations documentation.
        """
        logger.info("Generating formal analytical limitations boundary report...")

        report = AnalyticalLimitationsReport(
            dataset_limitations=self._dataset_limitations(),
            q1_limitations=self._q1_limitations(),
            q2_limitations=self._q2_limitations(),
            q3_limitations=self._q3_limitations(),
            unsupported_conclusions=self._unsupported_conclusions(),
        )

        logger.info(
            f"Limitations report complete: {report.total_limitation_count} items documented "
            f"({report.high_severity_count} HIGH severity), "
            f"{len(report.unsupported_conclusions)} unsupported conclusions stated."
        )
        return report

    def export_markdown(
        self,
        report: AnalyticalLimitationsReport,
        output_path: str = "reports/exports/analytical_limitations.md",
    ) -> str:
        """Export limitations report as a structured Markdown document.

        Args:
            report: The limitations report to export.
            output_path: Destination file path for the Markdown report.

        Returns:
            str: Absolute path of the exported file.
        """
        from pathlib import Path

        lines: List[str] = [
            "# Analytical Limitations & Boundary Analysis",
            "",
            f"**Generated:** {report.generated_at}",
            f"**Dataset:** {self.raw_count} raw records → {self.clean_count} analytical records ({self.attrition_pct}% attrition)",
            f"**Total Limitations Documented:** {report.total_limitation_count} ({report.high_severity_count} HIGH severity)",
            "",
            "---",
            "",
            "## 1. Dataset-Level Limitations",
            "",
        ]

        for i, lim in enumerate(report.dataset_limitations, 1):
            lines += [
                f"### D{i}. [{lim.severity}] {lim.category}",
                "",
                f"**Description:** {lim.description}",
                "",
                f"**Affected Questions:** {', '.join(lim.affected_questions)}",
                "",
                f"**Mitigation Applied:** {lim.mitigation}",
                "",
            ]
            if lim.future_data_needed:
                lines += [f"**Future Data Required:** {lim.future_data_needed}", ""]

        lines += ["---", "", "## 2. Question 1 — Closure Time Trend Limitations", ""]
        for i, lim in enumerate(report.q1_limitations, 1):
            lines += [
                f"### Q1-{i}. [{lim.severity}] {lim.category}",
                "",
                f"**Description:** {lim.description}",
                "",
                f"**Mitigation Applied:** {lim.mitigation}",
                "",
            ]
            if lim.future_data_needed:
                lines += [f"**Future Data Required:** {lim.future_data_needed}", ""]

        lines += ["---", "", "## 3. Question 2 — Duration Driver Limitations", ""]
        for i, lim in enumerate(report.q2_limitations, 1):
            lines += [
                f"### Q2-{i}. [{lim.severity}] {lim.category}",
                "",
                f"**Description:** {lim.description}",
                "",
                f"**Mitigation Applied:** {lim.mitigation}",
                "",
            ]
            if lim.future_data_needed:
                lines += [f"**Future Data Required:** {lim.future_data_needed}", ""]

        lines += ["---", "", "## 4. Question 3 — Triage Effectiveness Limitations", ""]
        for i, lim in enumerate(report.q3_limitations, 1):
            lines += [
                f"### Q3-{i}. [{lim.severity}] {lim.category}",
                "",
                f"**Description:** {lim.description}",
                "",
                f"**Mitigation Applied:** {lim.mitigation}",
                "",
            ]
            if lim.future_data_needed:
                lines += [f"**Future Data Required:** {lim.future_data_needed}", ""]

        lines += [
            "---",
            "",
            "## 5. Explicitly Unsupported Conclusions",
            "",
            "> The following conclusions are **NOT** supported by this dataset "
            "and must NOT be drawn from this analysis.",
            "",
        ]
        for i, conclusion in enumerate(report.unsupported_conclusions, 1):
            lines += [f"**{i}.** {conclusion}", ""]

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Analytical limitations report exported to: {out_path.resolve()}")
        return str(out_path.resolve())


def generate_limitations_report(
    cleaned_df: Optional[pd.DataFrame] = None,
    cleaned_path: str = "data/cleaned/case_management_cleaned.csv",
    raw_record_count: int = 120,
    output_path: str = "reports/exports/analytical_limitations.md",
) -> AnalyticalLimitationsReport:
    """Convenience function to generate and export limitations boundary analysis.

    Args:
        cleaned_df: Optional pre-loaded cleaned DataFrame.
        cleaned_path: Path to cleaned CSV if df not provided.
        raw_record_count: Raw record count for attrition calculation.
        output_path: Markdown export destination.

    Returns:
        AnalyticalLimitationsReport: Structured limitations report.
    """
    if cleaned_df is None:
        cleaned_df = pd.read_csv(cleaned_path)

    analyzer = LimitationsAnalyzer(
        cleaned_df=cleaned_df,
        raw_record_count=raw_record_count,
        clean_record_count=len(cleaned_df),
    )
    report = analyzer.generate_report()
    analyzer.export_markdown(report, output_path=output_path)
    return report
