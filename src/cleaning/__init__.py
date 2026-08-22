"""Data cleaning, normalization, and deduplication package."""

from src.cleaning.category_normalization import (
    CANONICAL_CATEGORIES,
    CATEGORY_ALIAS_MAP,
    PRIORITY_ALIAS_MAP,
    STATUS_ALIAS_MAP,
    CategoryNormalizer,
    NormalizationRecord,
    normalize_categories,
)

__all__ = [
    "CategoryNormalizer",
    "NormalizationRecord",
    "normalize_categories",
    "CANONICAL_CATEGORIES",
    "CATEGORY_ALIAS_MAP",
    "PRIORITY_ALIAS_MAP",
    "STATUS_ALIAS_MAP",
]
