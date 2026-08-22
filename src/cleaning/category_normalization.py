"""Category standardization and alias resolution engine."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Canonical category taxonomy
CANONICAL_CATEGORIES: Set[str] = {
    "Technical Support",
    "Billing",
    "Hardware",
    "General Inquiry",
    "Security Alert",
    "Account Access",
}

# Domain alias dictionary mapping normalized tokens to canonical taxonomy
CATEGORY_ALIAS_MAP: Dict[str, str] = {
    # Technical Support aliases
    "technical support": "Technical Support",
    "tech support": "Technical Support",
    "tech": "Technical Support",
    "techsupport": "Technical Support",
    "it support": "Technical Support",
    # Billing aliases
    "billing": "Billing",
    "billng": "Billing",
    "billing dept": "Billing",
    "invoicing": "Billing",
    "accounts receivable": "Billing",
    # Hardware aliases
    "hardware": "Hardware",
    "hardware maint": "Hardware",
    "hardware maintenance": "Hardware",
    "hardware repairs": "Hardware",
    "hw support": "Hardware",
    # General Inquiry aliases
    "general inquiry": "General Inquiry",
    "gen inquiry": "General Inquiry",
    "general inquiry query": "General Inquiry",
    "general info": "General Inquiry",
    "inquiry": "General Inquiry",
    # Security Alert aliases
    "security alert": "Security Alert",
    "security": "Security Alert",
    "sec alert": "Security Alert",
    "cyber security": "Security Alert",
    # Account Access aliases
    "account access": "Account Access",
    "login access": "Account Access",
    "password reset": "Account Access",
    "user access": "Account Access",
}

# Canonical priority mapping
PRIORITY_ALIAS_MAP: Dict[str, str] = {
    "low": "Low",
    "p4": "Low",
    "medium": "Medium",
    "med": "Medium",
    "p3": "Medium",
    "high": "High",
    "p2": "High",
    "critical": "Critical",
    "urgent": "Critical",
    "p1": "Critical",
    "urgent override": "Critical",
    "urgent_override": "Critical",
}

# Canonical status mapping
STATUS_ALIAS_MAP: Dict[str, str] = {
    "closed": "Closed",
    "resolved": "Closed",
    "open": "Open",
    "in progress": "In Progress",
    "inprogress": "In Progress",
    "pending": "Pending",
    "on hold": "Pending",
}


@dataclass
class NormalizationRecord:
    """Audit metadata for a normalized category or enum field."""

    row_index: int
    column_name: str
    raw_value: str
    cleaned_token: str
    normalized_value: str
    is_canonical: bool
    is_unresolved: bool
    was_modified: bool
    transformation_reason: str


class CategoryNormalizer:
    """Production category normalizer resolving spelling variations, punctuation, and aliases."""

    def __init__(
        self,
        alias_map: Optional[Dict[str, str]] = None,
        canonical_set: Optional[Set[str]] = None,
    ) -> None:
        """Initialize the normalizer with category taxonomy and alias mappings.

        Args:
            alias_map: Optional custom alias mapping dictionary.
            canonical_set: Optional custom canonical categories set.
        """
        self.alias_map = alias_map if alias_map is not None else CATEGORY_ALIAS_MAP
        self.canonical_set = canonical_set if canonical_set is not None else CANONICAL_CATEGORIES

    @staticmethod
    def clean_text_token(raw_text: Any) -> str:
        """Trim whitespace, lowercase, and collapse punctuation separators to single spaces.

        Args:
            raw_text: Raw string value.

        Returns:
            str: Cleaned alphanumeric token.
        """
        if pd.isna(raw_text):
            return ""
        text = str(raw_text).strip().lower()
        # Replace hyphens, underscores, slashes, and periods with single spaces
        text = re.sub(r"[\-_\/\.]+", " ", text)
        # Collapse multi-spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def normalize_category_value(self, raw_value: Any) -> Tuple[str, bool, bool, str]:
        """Normalize a single category string.

        Args:
            raw_value: Raw input category.

        Returns:
            Tuple[str, bool, bool, str]: (normalized_val, is_canonical, was_modified, reason)
        """
        if pd.isna(raw_value) or str(raw_value).strip() == "":
            return "Uncategorized", False, True, "Missing category defaulted to 'Uncategorized'"

        raw_str = str(raw_value).strip()
        token = self.clean_text_token(raw_str)

        # 1. Exact match with canonical set
        if raw_str in self.canonical_set:
            return raw_str, True, False, "Already canonical category"

        # 2. Match token in alias dictionary
        if token in self.alias_map:
            canonical = self.alias_map[token]
            return canonical, True, True, f"Mapped alias '{raw_str}' -> '{canonical}'"

        # 3. Unresolved category: retain original cleaned string without silent data loss
        unresolved_title = raw_str.strip()
        logger.warning(
            f"Unresolved category detected: '{raw_str}' (token: '{token}'). Retaining original label."
        )
        return unresolved_title, False, (raw_str != unresolved_title), f"Retained unmapped category '{raw_str}'"

    def normalize_series(
        self, series: pd.Series, column_name: str = "category"
    ) -> Tuple[pd.Series, List[NormalizationRecord]]:
        """Normalize an entire pandas Series of categories.

        Args:
            series: Input Series.
            column_name: Name of target column.

        Returns:
            Tuple[pd.Series, List[NormalizationRecord]]: Cleaned Series and audit records.
        """
        normalized_values: List[str] = []
        records: List[NormalizationRecord] = []

        for idx, val in series.items():
            raw_str = "" if pd.isna(val) else str(val)
            token = self.clean_text_token(raw_str)
            norm_val, is_canonical, was_mod, reason = self.normalize_category_value(raw_str)

            normalized_values.append(norm_val)
            records.append(
                NormalizationRecord(
                    row_index=int(idx),
                    column_name=column_name,
                    raw_value=raw_str,
                    cleaned_token=token,
                    normalized_value=norm_val,
                    is_canonical=is_canonical,
                    is_unresolved=(not is_canonical and norm_val != "Uncategorized"),
                    was_modified=was_mod,
                    transformation_reason=reason,
                )
            )

        cleaned_series = pd.Series(normalized_values, index=series.index, name=column_name)
        return cleaned_series, records

    def normalize_enum_series(
        self,
        series: pd.Series,
        column_name: str,
        alias_map: Dict[str, str],
        default_unmapped: Optional[str] = None,
    ) -> Tuple[pd.Series, List[NormalizationRecord]]:
        """Normalize an enumeration Series (such as priority or status).

        Args:
            series: Target Series.
            column_name: Name of the column.
            alias_map: Mapping dictionary of lowercased tokens to canonical values.
            default_unmapped: Optional fallback string if unmapped (e.g. 'Unknown').

        Returns:
            Tuple[pd.Series, List[NormalizationRecord]]: Standardized Series and audit records.
        """
        normalized_values: List[str] = []
        records: List[NormalizationRecord] = []

        for idx, val in series.items():
            raw_str = "" if pd.isna(val) else str(val)
            token = self.clean_text_token(raw_str)

            if token in alias_map:
                norm_val = alias_map[token]
                is_canonical = True
                was_mod = raw_str != norm_val
                reason = f"Normalized {column_name} '{raw_str}' -> '{norm_val}'"
            elif default_unmapped:
                norm_val = default_unmapped
                is_canonical = False
                was_mod = True
                reason = f"Unmapped {column_name} '{raw_str}' defaulted to '{default_unmapped}'"
            else:
                norm_val = raw_str
                is_canonical = False
                was_mod = False
                reason = f"Retained unrecognized {column_name} '{raw_str}'"

            normalized_values.append(norm_val)
            records.append(
                NormalizationRecord(
                    row_index=int(idx),
                    column_name=column_name,
                    raw_value=raw_str,
                    cleaned_token=token,
                    normalized_value=norm_val,
                    is_canonical=is_canonical,
                    is_unresolved=(not is_canonical),
                    was_modified=was_mod,
                    transformation_reason=reason,
                )
            )

        cleaned_series = pd.Series(normalized_values, index=series.index, name=column_name)
        return cleaned_series, records


def normalize_categories(
    df: pd.DataFrame,
    category_col: str = "category",
    priority_col: str = "priority",
    status_col: str = "status",
) -> Tuple[pd.DataFrame, List[NormalizationRecord]]:
    """Standardize categories, priorities, and statuses across a DataFrame.

    Args:
        df: Input DataFrame.
        category_col: Category column name.
        priority_col: Priority column name.
        status_col: Status column name.

    Returns:
        Tuple[pd.DataFrame, List[NormalizationRecord]]: Normalized DataFrame and transformation logs.
    """
    normalizer = CategoryNormalizer()
    df_clean = df.copy()
    all_records: List[NormalizationRecord] = []

    # 1. Normalize Category
    if category_col in df_clean.columns:
        clean_cat, cat_records = normalizer.normalize_series(df_clean[category_col], column_name=category_col)
        df_clean[category_col] = clean_cat
        all_records.extend(cat_records)

    # 2. Normalize Priority
    if priority_col in df_clean.columns:
        clean_prio, prio_records = normalizer.normalize_enum_series(
            df_clean[priority_col], column_name=priority_col, alias_map=PRIORITY_ALIAS_MAP
        )
        df_clean[priority_col] = clean_prio
        all_records.extend(prio_records)

    # 3. Normalize Status
    if status_col in df_clean.columns:
        clean_status, status_records = normalizer.normalize_enum_series(
            df_clean[status_col], column_name=status_col, alias_map=STATUS_ALIAS_MAP
        )
        df_clean[status_col] = clean_status
        all_records.extend(status_records)

    modified_count = sum(1 for r in all_records if r.was_modified)
    unresolved_count = sum(1 for r in all_records if r.is_unresolved)
    logger.info(
        f"Category & Enum Normalization complete: {modified_count} fields standardized, "
        f"{unresolved_count} unmapped values preserved safely."
    )
    return df_clean, all_records
