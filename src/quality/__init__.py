"""Data quality assessment and validation package."""

from src.quality.assessment import (
    DataQualityAssessor,
    QualityAnomaly,
    QualityReport,
    run_quality_assessment,
)
from src.quality.duplicates import (
    DuplicateDetector,
    DuplicateGroup,
    DuplicateMatch,
    DuplicateReport,
    detect_duplicates,
)

__all__ = [
    "DataQualityAssessor",
    "QualityAnomaly",
    "QualityReport",
    "run_quality_assessment",
    "DuplicateDetector",
    "DuplicateGroup",
    "DuplicateMatch",
    "DuplicateReport",
    "detect_duplicates",
]
