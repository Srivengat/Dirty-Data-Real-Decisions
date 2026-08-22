"""Unit tests for Module 5: Duplicate Detection."""

import pandas as pd
import pytest

from src.data.load_data import load_raw_data
from src.quality.duplicates import (
    DuplicateDetector,
    DuplicateGroup,
    DuplicateMatch,
    detect_duplicates,
)


def test_exact_duplicates() -> None:
    """Verify detection of strictly identical rows across all columns."""
    df = pd.DataFrame({
        "case_id": ["CS-1", "CS-1", "CS-2"],
        "client": ["Alpha", "Alpha", "Beta"],
        "status": ["Closed", "Closed", "Open"],
    })
    detector = DuplicateDetector(df)
    matches = detector.detect_exact_duplicates()

    assert len(matches) == 1
    assert matches[0].index_a == 0
    assert matches[0].index_b == 1
    assert matches[0].match_type == "EXACT"


def test_normalized_duplicates() -> None:
    """Verify detection of duplicates with whitespace and casing variance."""
    df = pd.DataFrame({
        "case_id": ["CS-1", "CS-2", "CS-3"],
        "client_name": ["Apex Solutions", "  apex   solutions  ", "Beta LLC"],
        "category": ["Tech", "tech", "Tech"],
        "intake_date": ["2024-01-01", "2024-01-01", "2024-01-01"],
    })
    detector = DuplicateDetector(df)
    matches = detector.detect_normalized_duplicates(subset_columns=["client_name", "category", "intake_date"])

    assert len(matches) == 1
    assert matches[0].index_a == 0
    assert matches[0].index_b == 1
    assert matches[0].match_type == "NORMALIZED"


def test_fuzzy_duplicates_rapidfuzz() -> None:
    """Verify RapidFuzz fuzzy duplicate detection on near-identical entity names."""
    df = pd.DataFrame({
        "case_id": ["CS-1", "CS-2", "CS-3"],
        "client_name": ["Fuzzy Matching Co", "Fuzzy Matching Company", "Totally Unrelated Inc"],
        "category": ["Technical Support", "Technical Support", "Billing"],
    })
    detector = DuplicateDetector(df, fuzzy_threshold=80.0)
    matches = detector.detect_fuzzy_duplicates(name_column="client_name", secondary_column="category")

    assert len(matches) >= 1
    assert matches[0].index_a == 0
    assert matches[0].index_b == 1
    assert matches[0].match_type == "FUZZY"
    assert matches[0].similarity_score >= 80.0


def test_cluster_duplicate_groups() -> None:
    """Verify transitive clustering into unified duplicate groups."""
    df = pd.DataFrame({
        "case_id": ["CS-1", "CS-2", "CS-3", "CS-4"],
        "client_name": ["A", "A", "A", "B"],
    })
    matches = [
        DuplicateMatch(0, 1, "EXACT", 100.0, ["client_name"], "match 1"),
        DuplicateMatch(1, 2, "EXACT", 100.0, ["client_name"], "match 2"),
    ]
    detector = DuplicateDetector(df)
    groups = detector.cluster_duplicate_groups(matches)

    assert len(groups) == 1
    assert groups[0].canonical_index == 0
    assert sorted(groups[0].duplicate_indices) == [1, 2]
    assert groups[0].total_records == 3


def test_duplicate_detection_on_raw_dataset() -> None:
    """Verify duplicate detection pipeline on actual case_management_raw.csv dataset."""
    df = load_raw_data("data/raw/case_management_raw.csv")
    report = detect_duplicates(df, fuzzy_threshold=85.0)

    assert report.total_records == len(df)
    assert report.total_unique_records_affected > 0
    assert len(report.duplicate_groups) > 0
