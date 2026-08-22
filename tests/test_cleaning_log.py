"""Unit tests for Module 9: Cleaning Log Generation."""

from pathlib import Path

import pandas as pd
import pytest

from src.cleaning.cleaning_log import AuditLogger, CleaningAuditEntry
from src.cleaning.pipeline import run_cleaning_pipeline
from src.data.load_data import load_raw_data


def test_audit_logger_basic_recording() -> None:
    """Verify recording and structure of audit entries."""
    logger = AuditLogger()
    logger.log(
        row_index=0,
        case_id="CS-101",
        column_name="category",
        old_value="tech-support",
        new_value="Technical Support",
        transformation_rule="CATEGORY_NORMALIZATION",
        reason="Mapped hyphenated alias to canonical taxonomy",
    )

    assert len(logger) == 1
    entry = logger.entries[0]
    assert entry.row_index == 0
    assert entry.case_id == "CS-101"
    assert entry.old_value == "tech-support"
    assert entry.new_value == "Technical Support"


def test_audit_logger_export_csv(tmp_path: Path) -> None:
    """Verify CSV export and schema compliance."""
    logger = AuditLogger()
    logger.log(
        row_index=1,
        case_id="CS-102",
        column_name="priority",
        old_value="URGENT",
        new_value="Critical",
        transformation_rule="PRIORITY_NORMALIZATION",
        reason="Mapped urgent to critical",
    )

    log_file = tmp_path / "cleaning_log.csv"
    logger.export_csv(log_file)

    assert log_file.exists()
    df_log = pd.read_csv(log_file)
    expected_cols = [
        "row_index",
        "case_id",
        "column_name",
        "old_value",
        "new_value",
        "transformation_rule",
        "reason",
        "timestamp",
    ]
    assert list(df_log.columns) == expected_cols
    assert len(df_log) == 1


def test_full_pipeline_audit_log_generation(tmp_path: Path) -> None:
    """Verify end-to-end cleaning log generation on case_management_raw.csv."""
    raw_df = load_raw_data("data/raw/case_management_raw.csv")
    cleaned_out = tmp_path / "cleaned.csv"
    log_out = tmp_path / "cleaning_log.csv"

    result = run_cleaning_pipeline(
        raw_df=raw_df,
        output_cleaned_path=cleaned_out,
        output_log_path=log_out,
    )

    assert log_out.exists()
    assert log_out.stat().st_size > 0

    df_log = pd.read_csv(log_out)
    assert len(df_log) > 0
    assert "PRIMARY_KEY_QUARANTINE" in df_log["transformation_rule"].values
    assert "TEMPORAL_ANOMALY_QUARANTINE" in df_log["transformation_rule"].values
    assert "DEDUPLICATION_MERGE" in df_log["transformation_rule"].values
