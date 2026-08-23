"""Unit tests for Module 3: Dataset Profiling."""

from pathlib import Path

import pandas as pd

from src.data.load_data import load_raw_data
from src.profiling.profiling import (
    DataProfiler,
    generate_profiling_report,
)


def test_profiler_basic_metrics() -> None:
    """Verify core dimension, missingness, and duplicate calculations on synthetic data."""
    data = {
        "id": ["1", "2", "3", "4", "4"],
        "category": ["Tech", "Billing", "Tech", "Tech", "Tech"],
        "count": ["10", "20", "", "40", "40"],
        "flag": ["Yes", "No", "Yes", "Yes", "Yes"],
    }
    df = pd.DataFrame(data)

    profiler = DataProfiler(df, source_name="test_data.csv")
    profile = profiler.profile()

    assert profile.row_count == 5
    assert profile.column_count == 4
    assert profile.exact_duplicate_rows == 1
    assert profile.exact_duplicate_percentage == 20.0

    # Test count column missingness
    count_profile = profile.columns["count"]
    assert count_profile.missing_count == 1
    assert count_profile.missing_percentage == 20.0

    # Test type inference
    assert profile.columns["flag"].inferred_type == "boolean"
    assert profile.columns["category"].inferred_type == "categorical"


def test_profiler_markdown_export(tmp_path: Path) -> None:
    """Verify generation of valid markdown report."""
    data = {
        "case_id": ["C1", "C2", "C3"],
        "status": ["Open", "Closed", "Pending"],
    }
    df = pd.DataFrame(data)
    out_file = tmp_path / "test_profiling.md"

    profile = generate_profiling_report(df, source_name="mock_cases.csv", output_path=out_file)
    assert out_file.exists()

    content = out_file.read_text(encoding="utf-8")
    assert "# Dataset Profiling Summary: `mock_cases.csv`" in content
    assert "| **Total Rows** | 3 |" in content
    assert "`case_id`" in content
    assert "`status`" in content


def test_profiler_on_raw_dataset(tmp_path: Path) -> None:
    """Verify profiler execution on the actual case_management_raw.csv dataset."""
    df = load_raw_data("data/raw/case_management_raw.csv")
    out_file = tmp_path / "profiling_summary.md"

    profile = generate_profiling_report(df, source_name="case_management_raw.csv", output_path=out_file)

    assert profile.row_count == len(df)
    assert "case_id" in profile.columns
    assert "intake_date" in profile.columns
    assert "closure_date" in profile.columns
    assert out_file.stat().st_size > 500
