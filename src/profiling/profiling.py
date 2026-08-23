"""Dataset profiling module for structural, statistical, and missingness analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ColumnProfile:
    """Detailed profile metrics for a single DataFrame column."""

    name: str
    dtype: str
    inferred_type: str
    total_count: int
    missing_count: int
    missing_percentage: float
    blank_string_count: int
    unique_count: int
    unique_ratio: float
    memory_bytes: int
    sample_values: List[str] = field(default_factory=list)
    top_frequencies: Dict[str, int] = field(default_factory=dict)


@dataclass
class DatasetProfile:
    """Comprehensive diagnostic profile of a dataset."""

    file_name: str
    row_count: int
    column_count: int
    total_memory_kb: float
    exact_duplicate_rows: int
    exact_duplicate_percentage: float
    columns: Dict[str, ColumnProfile] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DataProfiler:
    """Production analytical profiler computing structural and statistical data summaries."""

    def __init__(self, df: pd.DataFrame, source_name: str = "case_management_raw.csv") -> None:
        """Initialize the profiler with target dataset.

        Args:
            df: Raw or processed pandas DataFrame.
            source_name: Human-readable identifier of the data source.
        """
        self.df = df.copy()
        self.source_name = source_name

    def _infer_column_type(self, series: pd.Series) -> str:
        """Infer the underlying semantic type of a series.

        Args:
            series: Target pandas Series.

        Returns:
            str: Inferred type ('numeric', 'datetime', 'boolean', 'categorical', or 'text').
        """
        clean_series = series.dropna().astype(str).str.strip()
        clean_series = clean_series[clean_series != ""]
        if clean_series.empty:
            return "empty"

        # Check numeric
        try:
            pd.to_numeric(clean_series, errors="raise")
            return "numeric"
        except (ValueError, TypeError):
            pass

        # Check boolean-like
        unique_vals = set(clean_series.str.lower().unique())
        if unique_vals.issubset({"yes", "no", "y", "n", "true", "false", "1", "0"}):
            return "boolean"

        # Check datetime heuristic
        sample_subset = clean_series.iloc[: min(20, len(clean_series))]
        try:
            pd.to_datetime(sample_subset, format="mixed", errors="raise")
            return "datetime"
        except (ValueError, TypeError):
            pass

        # Categorical vs free text based on cardinality ratio
        unique_count = len(unique_vals)
        unique_ratio = unique_count / len(clean_series)
        if unique_count <= 10 or (unique_count < 50 and unique_ratio < 0.5):
            return "categorical"

        return "text"

    def profile_column(self, col_name: str) -> ColumnProfile:
        """Compute detailed profiling metrics for a specific column.

        Args:
            col_name: Name of the column in the dataset.

        Returns:
            ColumnProfile: Computed metrics for the column.
        """
        series = self.df[col_name]
        total_count = len(series)
        raw_values = series.astype(str)

        # Count true nulls and blank whitespace strings
        is_null = series.isna()
        is_blank = raw_values.str.strip().eq("") | raw_values.str.lower().eq("nan") | raw_values.str.lower().eq("none")
        missing_count = int((is_null | is_blank).sum())
        missing_pct = round((missing_count / total_count) * 100.0, 2) if total_count > 0 else 0.0

        # Unique values among non-blank entries
        valid_values = raw_values[~is_blank]
        unique_count = int(valid_values.nunique())
        unique_ratio = round(unique_count / total_count, 4) if total_count > 0 else 0.0

        # Top frequencies
        top_freq_series = valid_values.value_counts().head(5)
        top_frequencies = {str(k): int(v) for k, v in top_freq_series.items()}

        # Sample values
        sample_vals = [str(v) for v in valid_values.head(5).tolist()]

        # Memory usage
        memory_bytes = int(series.memory_usage(deep=True))

        return ColumnProfile(
            name=col_name,
            dtype=str(series.dtype),
            inferred_type=self._infer_column_type(series),
            total_count=total_count,
            missing_count=missing_count,
            missing_percentage=missing_pct,
            blank_string_count=int(is_blank.sum()),
            unique_count=unique_count,
            unique_ratio=unique_ratio,
            memory_bytes=memory_bytes,
            sample_values=sample_vals,
            top_frequencies=top_frequencies,
        )

    def profile(self) -> DatasetProfile:
        """Run full dataset profiling across all columns and dataset-level dimensions.

        Returns:
            DatasetProfile: Structured diagnostic summary object.
        """
        logger.info(f"Generating profiling report for '{self.source_name}' ({len(self.df)} rows)...")

        row_count = int(len(self.df))
        col_count = int(len(self.df.columns))
        total_memory_kb = round(self.df.memory_usage(deep=True).sum() / 1024.0, 2)

        # Calculate exact duplicate rows
        exact_dupes = int(self.df.duplicated().sum())
        exact_dupe_pct = round((exact_dupes / row_count) * 100.0, 2) if row_count > 0 else 0.0

        column_profiles: Dict[str, ColumnProfile] = {}
        for col in self.df.columns:
            column_profiles[col] = self.profile_column(col)

        profile_obj = DatasetProfile(
            file_name=self.source_name,
            row_count=row_count,
            column_count=col_count,
            total_memory_kb=total_memory_kb,
            exact_duplicate_rows=exact_dupes,
            exact_duplicate_percentage=exact_dupe_pct,
            columns=column_profiles,
        )

        logger.info(
            f"Profiling complete: {row_count} rows, {col_count} columns, "
            f"{exact_dupes} duplicate rows ({exact_dupe_pct}%), Memory: {total_memory_kb} KB."
        )
        return profile_obj

    def export_markdown(
        self, profile: DatasetProfile, output_path: Union[str, Path] = "reports/exports/profiling_summary.md"
    ) -> Path:
        """Format and write the profiling summary as a clean Markdown report.

        Args:
            profile: Generated DatasetProfile object.
            output_path: Target destination file path.

        Returns:
            Path: Absolute path of written report file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = [
            f"# Dataset Profiling Summary: `{profile.file_name}`",
            "",
            f"**Generated:** {profile.generated_at}",
            "",
            "## 1. High-Level Dataset Dimensions",
            "",
            "| Metric | Value |",
            "| :--- | :--- |",
            f"| **Total Rows** | {profile.row_count:,} |",
            f"| **Total Columns** | {profile.column_count} |",
            f"| **Total Memory Usage** | {profile.total_memory_kb:,.2f} KB |",
            f"| **Exact Duplicate Rows** | {profile.exact_duplicate_rows:,} ({profile.exact_duplicate_percentage}%) |",
            "",
            "## 2. Column-Level Attribute Summary",
            "",
            "| Column Name | Inferred Type | Missing Count | Missing % | Unique Values | Cardinality Ratio | Memory (KB) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for col_name, cp in profile.columns.items():
            mem_kb = round(cp.memory_bytes / 1024.0, 2)
            lines.append(
                f"| `{col_name}` | {cp.inferred_type} | {cp.missing_count:,} | {cp.missing_percentage}% | "
                f"{cp.unique_count:,} | {cp.unique_ratio:.4f} | {mem_kb} KB |"
            )

        lines.extend([
            "",
            "## 3. Value Distributions & Top Frequencies",
            "",
        ])

        for col_name, cp in profile.columns.items():
            lines.append(f"### Column: `{col_name}` ({cp.inferred_type})")
            if cp.top_frequencies:
                lines.append("| Value | Count |")
                lines.append("| :--- | :--- |")
                for val, cnt in cp.top_frequencies.items():
                    safe_val = val.replace("\n", " ").replace("|", "\\|")
                    lines.append(f"| `{safe_val}` | {cnt:,} |")
            else:
                lines.append("*No valid values found.*")
            lines.append("")

        content = "\n".join(lines)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Exported profiling summary markdown to: {path.resolve()}")
        return path


def generate_profiling_report(
    df: pd.DataFrame,
    source_name: str = "case_management_raw.csv",
    output_path: Union[str, Path] = "reports/exports/profiling_summary.md",
) -> DatasetProfile:
    """Helper function to profile a DataFrame and export markdown summary report.

    Args:
        df: Input pandas DataFrame.
        source_name: Identifier for data source.
        output_path: Path to export markdown report.

    Returns:
        DatasetProfile: Generated profile object.
    """
    profiler = DataProfiler(df=df, source_name=source_name)
    profile = profiler.profile()
    profiler.export_markdown(profile=profile, output_path=output_path)
    return profile
