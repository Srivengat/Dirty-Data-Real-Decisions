"""Unit tests for Module 6: Date Validation."""

import pandas as pd
import pytest

from src.data.load_data import load_raw_data
from src.quality.date_validation import (
    DateValidationResult,
    DateValidationSummary,
    DateValidator,
    validate_dates,
)


def test_parse_multi_format_dates() -> None:
    """Verify parsing ISO, US slash, European slash, and dot formats."""
    validator = DateValidator()

    # ISO
    ts_iso = validator.parse_single_date("2024-05-15")
    assert ts_iso == pd.Timestamp("2024-05-15")

    # European DD/MM/YYYY (day > 12)
    ts_eu = validator.parse_single_date("25/05/2024")
    assert ts_eu == pd.Timestamp("2024-05-25")

    # US MM/DD/YYYY (month <= 12, day > 12)
    ts_us = validator.parse_single_date("06/28/2024")
    assert ts_us == pd.Timestamp("2024-06-28")

    # Dot format YYYY.MM.DD
    ts_dot = validator.parse_single_date("2024.07.01")
    assert ts_dot == pd.Timestamp("2024-07-01")


def test_impossible_dates_rejection() -> None:
    """Verify rejection of non-existent calendar dates."""
    validator = DateValidator()

    assert validator.parse_single_date("2024-13-45") is None
    assert validator.parse_single_date("2024-02-31") is None
    assert validator.parse_single_date("not-a-date") is None
    assert validator.parse_single_date("") is None


def test_future_date_detection() -> None:
    """Verify detection of dates exceeding reference cutoff."""
    validator = DateValidator(reference_cutoff=pd.Timestamp("2026-01-01"))
    result = validator.validate_record(0, intake_str="2099-01-01", closure_str="2099-01-05")

    assert not result.is_valid
    assert "FUTURE_INTAKE_DATE" in result.error_flags


def test_negative_duration_detection() -> None:
    """Verify detection when closure occurs before intake."""
    validator = DateValidator()
    result = validator.validate_record(0, intake_str="2024-03-10", closure_str="2024-03-05")

    assert not result.is_valid
    assert "NEGATIVE_DURATION" in result.error_flags
    assert result.duration_days == -5.0


def test_triage_sequence_validation() -> None:
    """Verify triage timing validation relative to intake and closure."""
    validator = DateValidator()

    # Triage before intake
    bad_triage = validator.validate_record(
        0, intake_str="2024-01-10", closure_str="2024-01-20", triage_str="2024-01-05"
    )
    assert "TRIAGE_BEFORE_INTAKE" in bad_triage.error_flags

    # Triage after closure
    late_triage = validator.validate_record(
        1, intake_str="2024-01-10", closure_str="2024-01-20", triage_str="2024-01-25"
    )
    assert "TRIAGE_AFTER_CLOSURE" in late_triage.error_flags

    # Valid triage
    valid_triage = validator.validate_record(
        2, intake_str="2024-01-10", closure_str="2024-01-20", triage_str="2024-01-12"
    )
    assert valid_triage.is_valid
    assert valid_triage.duration_days == 10.0


def test_dataframe_date_validation_on_raw_data() -> None:
    """Verify full date validation on raw case management dataset."""
    df = load_raw_data("data/raw/case_management_raw.csv")
    summary = validate_dates(df)

    assert summary.total_records == len(df)
    assert summary.future_date_count >= 1
    assert summary.negative_duration_count >= 1
    assert summary.mean_duration_days is not None
    assert summary.mean_duration_days > 0
