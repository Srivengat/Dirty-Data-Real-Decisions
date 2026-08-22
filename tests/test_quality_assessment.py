"""Unit tests for Module 4: Data Quality Assessment."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.load_data import load_raw_data
from src.quality.assessment import (
    DataQualityAssessor,
    QualityAnomaly,
    QualityReport,
    run_quality_assessment,
)


def test_check_missing_case_id() -> None:
    """Verify detection of missing case_id values."""
    df = pd.DataFrame({"case_id": ["C1", "", "None", "C4"], "status": ["Closed"] * 4})
    assessor = DataQualityAssessor(df)
    anomaly = assessor.check_missing_identifiers()

    assert anomaly is not None
    assert anomaly.rule_name == "missing_case_id"
    assert anomaly.severity == "CRITICAL"
    assert len(anomaly.affected_rows) == 2  # indices 1 and 2


def test_check_duplicate_case_id() -> None:
    """Verify detection of duplicate case_id values."""
    df = pd.DataFrame({"case_id": ["C1", "C2", "C1", "C3"]})
    assessor = DataQualityAssessor(df)
    anomaly = assessor.check_duplicate_case_ids()

    assert anomaly is not None
    assert anomaly.rule_name == "duplicate_case_id"
    assert len(anomaly.affected_rows) == 2  # indices 0 and 2


def test_check_dates_anomalies() -> None:
    """Verify detection of future dates, negative duration, and impossible dates."""
    df = pd.DataFrame({
        "intake_date": ["2024-01-10", "2024-03-10", "2099-01-01", "2024-05-01"],
        "closure_date": ["2024-01-15", "2024-03-05", "2099-01-05", "2024-13-45"],
    })
    assessor = DataQualityAssessor(df, reference_date=pd.Timestamp("2026-01-01"))
    anomalies = assessor.check_dates_validity()
    rule_names = [a.rule_name for a in anomalies]

    assert "negative_resolution_duration" in rule_names
    assert "future_intake_date" in rule_names
    assert "invalid_closure_date_format" in rule_names


def test_check_invalid_enums() -> None:
    """Verify detection of non-standard status and priority enums."""
    df = pd.DataFrame({
        "status": ["Closed", "Open", "INVALID_STATUS"],
        "priority": ["High", "Medium", "URGENT_CUSTOM"],
    })
    assessor = DataQualityAssessor(df)
    status_anom = assessor.check_invalid_status()
    prio_anom = assessor.check_invalid_priority()

    assert status_anom is not None
    assert status_anom.rule_name == "invalid_status_enum"
    assert prio_anom is not None
    assert prio_anom.rule_name == "invalid_priority_enum"


def test_check_contact_counts() -> None:
    """Verify detection of negative or extreme outlier contact counts."""
    df = pd.DataFrame({"contact_count": ["3", "-5", "99999", "abc", "2"]})
    assessor = DataQualityAssessor(df)
    anomaly = assessor.check_contact_counts()

    assert anomaly is not None
    assert anomaly.rule_name == "invalid_contact_count_bounds"
    assert len(anomaly.affected_rows) == 3  # -5, 99999, abc


def test_full_quality_assessment_on_raw_dataset(tmp_path: Path) -> None:
    """Verify end-to-end quality assessment and report export on the raw case export."""
    df = load_raw_data("data/raw/case_management_raw.csv")
    out_file = tmp_path / "data_quality_report.md"

    report = run_quality_assessment(df, dataset_name="case_management_raw.csv", output_path=out_file)

    assert report.total_records == len(df)
    assert report.total_anomalies > 0
    assert 0.0 <= report.quality_score <= 100.0
    assert out_file.exists()

    content = out_file.read_text(encoding="utf-8")
    assert "# Data Quality Assessment Report" in content
    assert "Executive Quality Scorecard" in content
