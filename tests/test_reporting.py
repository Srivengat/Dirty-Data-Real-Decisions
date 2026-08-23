"""Unit tests for Module 14: Reporting Engine."""

from pathlib import Path

import pandas as pd
import pytest

from src.cleaning.pipeline import run_cleaning_pipeline
from src.data.load_data import load_raw_data
from src.reporting.reports import run_reporting


@pytest.fixture(scope="module")
def raw_df() -> pd.DataFrame:
    """Raw dataset fixture."""
    return load_raw_data("data/raw/case_management_raw.csv")


@pytest.fixture(scope="module")
def clean_df() -> pd.DataFrame:
    """Cleaned dataset fixture."""
    raw = load_raw_data("data/raw/case_management_raw.csv")
    return run_cleaning_pipeline(raw_df=raw).cleaned_df


def test_run_reporting_generates_all_reports(raw_df, clean_df, tmp_path, monkeypatch):
    """Verify the reporting engine generates all expected markdown files."""
    import src.reporting.reports as rep_module
    monkeypatch.setattr(rep_module, "REPORTS_DIR", tmp_path)
    
    manifest = run_reporting(
        raw_df=raw_df,
        cleaned_df=clean_df,
        quality_score=91.11,
        raw_count=len(raw_df),
        clean_count=len(clean_df),
        quarantined=4,
        deduplicated=3,
        audit_entries=156,
    )

    assert len(manifest.all_paths) == 4
    for path in manifest.all_paths:
        assert path.exists()
        assert path.suffix == ".md"
        assert path.stat().st_size > 100  # Ensure report is not empty

def test_executive_summary_content(raw_df, clean_df, tmp_path, monkeypatch):
    """Check key content elements in executive summary."""
    import src.reporting.reports as rep_module
    monkeypatch.setattr(rep_module, "REPORTS_DIR", tmp_path)
    
    manifest = run_reporting(
        raw_df=raw_df,
        cleaned_df=clean_df,
    )
    
    content = manifest.executive_summary.read_text(encoding="utf-8")
    assert "# Executive Summary" in content
    assert "Data Quality Score:" in content
    assert "## Key Findings" in content
    assert "## Critical Limitations" in content

def test_quality_report_content(raw_df, clean_df, tmp_path, monkeypatch):
    """Check key content elements in quality report."""
    import src.reporting.reports as rep_module
    monkeypatch.setattr(rep_module, "REPORTS_DIR", tmp_path)
    
    manifest = run_reporting(
        raw_df=raw_df,
        cleaned_df=clean_df,
    )
    
    content = manifest.quality_report.read_text(encoding="utf-8")
    assert "## Dataset Overview" in content
    assert "## Column-Level Missingness" in content
    assert "## Cleaning Pipeline Stages" in content
