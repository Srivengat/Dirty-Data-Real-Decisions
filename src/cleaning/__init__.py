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
from src.cleaning.cleaning_log import (
    AuditLogger,
    CleaningAuditEntry,
)
from src.cleaning.pipeline import (
    CleaningPipeline,
    CleaningPipelineResult,
    run_cleaning_pipeline,
)

__all__ = [
    "CategoryNormalizer",
    "NormalizationRecord",
    "normalize_categories",
    "CANONICAL_CATEGORIES",
    "CATEGORY_ALIAS_MAP",
    "PRIORITY_ALIAS_MAP",
    "STATUS_ALIAS_MAP",
    "AuditLogger",
    "CleaningAuditEntry",
    "CleaningPipeline",
    "CleaningPipelineResult",
    "run_cleaning_pipeline",
]
