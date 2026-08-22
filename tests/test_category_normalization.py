"""Unit tests for Module 7: Category Normalization."""

import pandas as pd
import pytest

from src.cleaning.category_normalization import (
    CANONICAL_CATEGORIES,
    CategoryNormalizer,
    NormalizationRecord,
    normalize_categories,
)
from src.data.load_data import load_raw_data


def test_clean_text_token() -> None:
    """Verify string cleaning, punctuation collapsing, and whitespace trimming."""
    assert CategoryNormalizer.clean_text_token("  TECH_SUPPORT  ") == "tech support"
    assert CategoryNormalizer.clean_text_token("hardware-maint/repairs") == "hardware maint repairs"
    assert CategoryNormalizer.clean_text_token("billing..dept") == "billing dept"
    assert CategoryNormalizer.clean_text_token("") == ""


def test_normalize_known_aliases() -> None:
    """Verify alias mapping to canonical taxonomy."""
    normalizer = CategoryNormalizer()

    # Technical Support aliases
    val, is_canon, was_mod, reason = normalizer.normalize_category_value("TECH SUPPORT")
    assert val == "Technical Support"
    assert is_canon and was_mod

    # Billing aliases
    val, is_canon, was_mod, reason = normalizer.normalize_category_value("billng ")
    assert val == "Billing"
    assert is_canon and was_mod

    # Hardware aliases
    val, is_canon, was_mod, reason = normalizer.normalize_category_value("hardware_maint")
    assert val == "Hardware"
    assert is_canon and was_mod


def test_unresolved_category_preservation() -> None:
    """Verify that unrecognized categories are safely preserved without silent deletion."""
    normalizer = CategoryNormalizer()
    val, is_canon, was_mod, reason = normalizer.normalize_category_value("weird_custom_cat_123")

    assert val == "weird_custom_cat_123"
    assert not is_canon
    assert "Retained unmapped" in reason


def test_priority_and_status_normalization() -> None:
    """Verify normalization of priority and status enumeration columns."""
    df = pd.DataFrame({
        "category": ["tech-support", "billing"],
        "priority": ["URGENT_OVERRIDE", "low"],
        "status": ["RESOLVED", "open"],
    })
    df_clean, records = normalize_categories(df)

    assert df_clean["priority"].tolist() == ["Critical", "Low"]
    assert df_clean["status"].tolist() == ["Closed", "Open"]
    assert df_clean["category"].tolist() == ["Technical Support", "Billing"]


def test_normalization_on_raw_dataset() -> None:
    """Verify category normalization over the actual raw case management export."""
    df = load_raw_data("data/raw/case_management_raw.csv")
    df_clean, records = normalize_categories(df)

    assert len(df_clean) == len(df)
    assert len(records) == len(df) * 3  # category, priority, status
    # Verify majority of categories are in canonical set
    canonical_count = sum(1 for val in df_clean["category"] if val in CANONICAL_CATEGORIES)
    assert canonical_count >= len(df) * 0.95
