"""Unit tests for Module 8: Cleaning Pipeline."""

from pathlib import Path

import pandas as pd
import pytest

from src.cleaning.pipeline import (
    CleaningPipeline,
    CleaningPipelineResult,
    run_cleaning_pipeline,
)
from src.data.load_data import load_raw_data


def test_cleaning_pipeline_synthetic_flow() -> None:
    """Verify cleaning stages, deduplication, and quarantine on controlled test dataset."""
    df_raw = pd.DataFrame({
        "case_id": ["C1", "C2", "C3", "C4", "C5", ""],
        "client_name": ["Alpha Corp", "alpha corp", "Beta LLC", "Gamma Inc", "Delta Co", "Nameless"],
        "category": ["tech-support", "Technical Support", "billng", "Hardware", "Hardware", "General"],
        "priority": ["URGENT_OVERRIDE", "High", "Medium", "Low", "Low", "Low"],
        "intake_date": ["2024-01-01", "2024-01-01", "2024-02-01", "2024-03-10", "2099-01-01", "2024-04-01"],
        "closure_date": ["2024-01-05", "2024-01-05", "2024-02-10", "2024-03-05", "2099-01-05", "2024-04-05"],
        "status": ["RESOLVED", "Closed", "Closed", "Closed", "Closed", "Closed"],
        "contact_count": ["3", "3", "-5", "9999", "2", "1"],
        "triaged": ["Yes", "Y", "No", "No", "No", "No"],
    })

    pipeline = CleaningPipeline(reference_date=pd.Timestamp("2026-01-01"))
    result = pipeline.clean(df_raw)

    assert result.initial_rows == 6
    # C1 and C2 are duplicate -> 1 deduplicated
    # C4 has negative duration (2024-03-10 to 2024-03-05) -> quarantined
    # C5 has future intake date (2099) -> quarantined
    # Row 5 has missing case_id -> quarantined
    assert result.quarantined_rows_count == 3
    assert result.deduplicated_rows_count == 1
    assert result.final_rows == 2

    # Verify cleaned values
    clean_c1 = result.cleaned_df[result.cleaned_df["case_id"] == "C1"].iloc[0]
    assert clean_c1["category"] == "Technical Support"
    assert clean_c1["priority"] == "Critical"
    assert clean_c1["status"] == "Closed"
    assert clean_c1["duration_days"] == 4.0
    assert bool(clean_c1["triaged"]) is True


def test_raw_immutability(tmp_path: Path) -> None:
    """Verify that running the cleaning pipeline never mutates the original raw DataFrame or file."""
    raw_path = Path("data/raw/case_management_raw.csv")
    raw_bytes_before = raw_path.read_bytes()

    df_raw = load_raw_data(raw_path)
    df_raw_copy = df_raw.copy(deep=True)

    out_file = tmp_path / "case_management_cleaned.csv"
    result = run_cleaning_pipeline(raw_path=raw_path, output_cleaned_path=out_file, raw_df=df_raw)

    # Assert raw dataframe was unchanged
    pd.testing.assert_frame_equal(df_raw, df_raw_copy)

    # Assert raw file on disk was unchanged
    raw_bytes_after = raw_path.read_bytes()
    assert raw_bytes_before == raw_bytes_after

    # Assert output cleaned file was created
    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_cleaning_pipeline_on_full_raw_dataset(tmp_path: Path) -> None:
    """Verify cleaning pipeline execution on case_management_raw.csv."""
    df_raw = load_raw_data("data/raw/case_management_raw.csv")
    out_file = tmp_path / "cleaned_full.csv"

    result = run_cleaning_pipeline(raw_df=df_raw, output_cleaned_path=out_file)

    assert result.final_rows > 0
    assert result.final_rows < result.initial_rows
    assert "duration_days" in result.cleaned_df.columns
    # Ensure all duration_days in clean data are non-negative
    valid_durations = result.cleaned_df["duration_days"].dropna()
    assert (valid_durations >= 0).all()
