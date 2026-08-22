"""Unit tests for Module 12: Analytical Limitations Documentation."""

import pytest
import pandas as pd
from pathlib import Path

from src.analysis.limitations import (
    AnalyticalLimitationsReport,
    LimitationItem,
    LimitationsAnalyzer,
    generate_limitations_report,
)
from src.cleaning.pipeline import run_cleaning_pipeline
from src.data.load_data import load_raw_data


@pytest.fixture
def clean_df() -> pd.DataFrame:
    """Fixture providing cleaned analytical dataset."""
    raw_df = load_raw_data("data/raw/case_management_raw.csv")
    return run_cleaning_pipeline(raw_df=raw_df).cleaned_df


@pytest.fixture
def limitations_analyzer(clean_df) -> LimitationsAnalyzer:
    """Fixture providing a LimitationsAnalyzer instance."""
    return LimitationsAnalyzer(
        cleaned_df=clean_df,
        raw_record_count=120,
        clean_record_count=len(clean_df),
    )


def test_limitations_report_has_all_scopes(limitations_analyzer: LimitationsAnalyzer) -> None:
    """Verify report contains limitations across all four scopes."""
    report = limitations_analyzer.generate_report()
    assert len(report.dataset_limitations) > 0
    assert len(report.q1_limitations) > 0
    assert len(report.q2_limitations) > 0
    assert len(report.q3_limitations) > 0


def test_limitations_report_has_unsupported_conclusions(limitations_analyzer: LimitationsAnalyzer) -> None:
    """Verify at least 3 explicitly unsupported conclusions are documented."""
    report = limitations_analyzer.generate_report()
    assert len(report.unsupported_conclusions) >= 3
    for conclusion in report.unsupported_conclusions:
        assert "CANNOT CONCLUDE" in conclusion


def test_high_severity_items_present(limitations_analyzer: LimitationsAnalyzer) -> None:
    """Verify at least 3 HIGH severity limitations are documented."""
    report = limitations_analyzer.generate_report()
    assert report.high_severity_count >= 3


def test_all_limitations_have_valid_severity(limitations_analyzer: LimitationsAnalyzer) -> None:
    """Verify every LimitationItem has a valid severity level."""
    report = limitations_analyzer.generate_report()
    for item in report.all_limitations:
        assert item.severity in ("HIGH", "MEDIUM", "LOW")
        assert item.category in ("DATA_GAP", "CONFOUNDING", "INFERENCE_BOUNDARY", "MISSING_VARIABLE")


def test_all_limitations_affect_known_questions(limitations_analyzer: LimitationsAnalyzer) -> None:
    """Verify all affected_questions fields reference valid question IDs."""
    report = limitations_analyzer.generate_report()
    valid_qids = {"Q1", "Q2", "Q3"}
    for item in report.all_limitations:
        for qid in item.affected_questions:
            assert qid in valid_qids


def test_markdown_export(limitations_analyzer: LimitationsAnalyzer, tmp_path: Path) -> None:
    """Verify Markdown export writes a readable structured file."""
    report = limitations_analyzer.generate_report()
    out_file = tmp_path / "limitations.md"
    limitations_analyzer.export_markdown(report, output_path=str(out_file))

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Analytical Limitations" in content
    assert "CANNOT CONCLUDE" in content
    assert "HIGH" in content


def test_convenience_function(clean_df: pd.DataFrame, tmp_path: Path) -> None:
    """Verify generate_limitations_report works end-to-end."""
    out_file = tmp_path / "limitations.md"
    report = generate_limitations_report(
        cleaned_df=clean_df,
        raw_record_count=120,
        output_path=str(out_file),
    )
    assert report.total_limitation_count > 0
    assert out_file.exists()
