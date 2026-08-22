"""Unit tests for Module 2: Robust Data Loading."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.data.load_data import (
    DEFAULT_REQUIRED_COLUMNS,
    DataLoader,
    DataLoadingError,
    SchemaValidationError,
    load_raw_data,
)


def test_load_default_raw_dataset() -> None:
    """Verify loading the primary raw case management export."""
    raw_path = Path("data/raw/case_management_raw.csv")
    assert raw_path.exists(), "Raw dataset must exist in data/raw/"

    df = load_raw_data(raw_path)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert all(col in df.columns for col in DEFAULT_REQUIRED_COLUMNS)


def test_encoding_fallback_latin1(tmp_path: Path) -> None:
    """Verify that Latin-1 encoded CSV files load successfully."""
    latin1_file = tmp_path / "latin1_sample.csv"
    content = "case_id,client_name,category,priority,intake_date,closure_date,status\nCS-901,Café Corp,Billing,High,2024-01-01,2024-01-05,Closed\n"
    latin1_file.write_bytes(content.encode("latin1"))

    loader = DataLoader()
    detected_encoding = loader.detect_encoding(latin1_file)
    assert detected_encoding in ("utf-8", "latin1", "cp1252", "iso-8859-1")

    df = loader.load(latin1_file)
    assert len(df) == 1
    assert "Café Corp" in df["client_name"].values


def test_delimiter_auto_detection(tmp_path: Path) -> None:
    """Verify delimiter detection for semicolons, tabs, and pipes."""
    delimiters = [";", "\t", "|"]
    for delim in delimiters:
        file_path = tmp_path / f"delim_{ord(delim)}.csv"
        header = delim.join(DEFAULT_REQUIRED_COLUMNS)
        row = delim.join(["C-01", "Client A", "Tech", "High", "2024-01-01", "2024-01-02", "Closed"])
        file_path.write_text(f"{header}\n{row}\n", encoding="utf-8")

        loader = DataLoader()
        detected = loader.detect_delimiter(file_path, "utf-8")
        assert detected == delim, f"Expected delimiter '{delim}', got '{detected}'"

        df = loader.load(file_path)
        assert len(df) == 1
        assert "client_name" in df.columns


def test_schema_validation_failure(tmp_path: Path) -> None:
    """Verify SchemaValidationError when required columns are absent."""
    bad_schema_file = tmp_path / "missing_cols.csv"
    bad_schema_file.write_text("random_col_a,random_col_b\nval1,val2\n", encoding="utf-8")

    loader = DataLoader(required_columns=["case_id", "client_name"])
    with pytest.raises(SchemaValidationError) as excinfo:
        loader.load(bad_schema_file, validate=True)

    assert "Missing required columns" in str(excinfo.value)


def test_file_not_found() -> None:
    """Verify FileNotFoundError on non-existent file path."""
    loader = DataLoader()
    with pytest.raises(FileNotFoundError):
        loader.load("data/raw/non_existent_dataset_12345.csv")


def test_empty_file_handling(tmp_path: Path) -> None:
    """Verify handling of completely empty file."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")

    loader = DataLoader()
    with pytest.raises(DataLoadingError):
        loader.load(empty_file, validate=False)
