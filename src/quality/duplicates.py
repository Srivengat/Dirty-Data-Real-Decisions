"""Multi-strategy duplicate detection engine supporting exact, normalized, and RapidFuzz fuzzy matching."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set

import pandas as pd
from rapidfuzz import fuzz

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DuplicateMatch:
    """Pairwise duplicate record association."""

    index_a: int
    index_b: int
    match_type: str  # 'EXACT', 'NORMALIZED', 'FUZZY'
    similarity_score: float
    matched_fields: List[str]
    description: str


@dataclass
class DuplicateGroup:
    """Consolidated cluster of duplicate records mapped to a canonical primary record."""

    group_id: int
    canonical_index: int
    duplicate_indices: List[int]
    total_records: int
    match_type: str
    sample_identifier: str


@dataclass
class DuplicateReport:
    """Comprehensive summary of all duplicate detection passes."""

    total_records: int
    exact_duplicate_count: int
    normalized_duplicate_count: int
    fuzzy_duplicate_count: int
    total_unique_records_affected: int
    duplicate_groups: List[DuplicateGroup] = field(default_factory=list)
    pairwise_matches: List[DuplicateMatch] = field(default_factory=list)


class DuplicateDetector:
    """Production duplicate detection engine executing multi-tier resolution."""

    def __init__(
        self,
        df: pd.DataFrame,
        fuzzy_threshold: float = 85.0,
    ) -> None:
        """Initialize DuplicateDetector with input dataset.

        Args:
            df: Input pandas DataFrame.
            fuzzy_threshold: Minimum string similarity percentage (0-100) for fuzzy matches.
        """
        self.df = df.copy()
        self.fuzzy_threshold = fuzzy_threshold

    def _normalize_string(self, text: Any) -> str:
        """Helper to trim, lowercase, and collapse whitespace."""
        if pd.isna(text):
            return ""
        return " ".join(str(text).strip().lower().split())

    def detect_exact_duplicates(self) -> List[DuplicateMatch]:
        """Detect completely identical rows across all columns.

        Returns:
            List[DuplicateMatch]: Pairwise exact duplicate matches.
        """
        matches: List[DuplicateMatch] = []
        dupe_mask = self.df.duplicated(keep=False)
        if not dupe_mask.any():
            return matches

        dupe_df = self.df[dupe_mask]
        grouped = dupe_df.groupby(list(self.df.columns))

        for _, group in grouped:
            indices = group.index.tolist()
            canonical = indices[0]
            for dupe_idx in indices[1:]:
                matches.append(
                    DuplicateMatch(
                        index_a=canonical,
                        index_b=dupe_idx,
                        match_type="EXACT",
                        similarity_score=100.0,
                        matched_fields=list(self.df.columns),
                        description=f"Exact match across all {len(self.df.columns)} columns.",
                    )
                )

        logger.debug(f"Detected {len(matches)} pairwise exact duplicate rows.")
        return matches

    def detect_normalized_duplicates(
        self, subset_columns: Optional[Sequence[str]] = None
    ) -> List[DuplicateMatch]:
        """Detect duplicate rows after trimming whitespace and lowercasing strings.

        Args:
            subset_columns: Key columns to evaluate (defaults to core business fields).

        Returns:
            List[DuplicateMatch]: Pairwise normalized duplicate matches.
        """
        matches: List[DuplicateMatch] = []
        target_cols = (
            list(subset_columns)
            if subset_columns is not None
            else [c for c in ["client_name", "category", "intake_date", "closure_date"] if c in self.df.columns]
        )

        if not target_cols:
            return matches

        norm_df = pd.DataFrame(index=self.df.index)
        for col in target_cols:
            norm_df[col] = self.df[col].apply(self._normalize_string)

        # Ignore empty rows
        non_empty = norm_df[(norm_df != "").all(axis=1)]
        dupe_mask = non_empty.duplicated(subset=target_cols, keep=False)

        if not dupe_mask.any():
            return matches

        grouped = non_empty[dupe_mask].groupby(target_cols)
        for _, group in grouped:
            indices = group.index.tolist()
            canonical = indices[0]
            for dupe_idx in indices[1:]:
                matches.append(
                    DuplicateMatch(
                        index_a=canonical,
                        index_b=dupe_idx,
                        match_type="NORMALIZED",
                        similarity_score=100.0,
                        matched_fields=target_cols,
                        description=f"Normalized match on key columns: {target_cols}.",
                    )
                )

        logger.debug(f"Detected {len(matches)} pairwise normalized duplicate records.")
        return matches

    def detect_fuzzy_duplicates(
        self,
        name_column: str = "client_name",
        secondary_column: Optional[str] = "category",
    ) -> List[DuplicateMatch]:
        """Detect near-duplicate records using RapidFuzz string similarity.

        Args:
            name_column: Target column containing client or entity names.
            secondary_column: Optional column required to match or have high similarity.

        Returns:
            List[DuplicateMatch]: Pairwise fuzzy duplicate matches.
        """
        matches: List[DuplicateMatch] = []
        if name_column not in self.df.columns:
            return matches

        records = []
        for idx, row in self.df.iterrows():
            name_norm = self._normalize_string(row.get(name_column, ""))
            sec_norm = self._normalize_string(row.get(secondary_column, "")) if secondary_column else ""
            if name_norm:
                records.append((idx, name_norm, sec_norm))

        num_records = len(records)
        # Pairwise fuzzy comparison
        for i in range(num_records):
            idx_a, name_a, sec_a = records[i]
            for j in range(i + 1, num_records):
                idx_b, name_b, sec_b = records[j]

                # Skip identical normalized names (handled by normalized step)
                if name_a == name_b:
                    continue

                # RapidFuzz token sort ratio handles word re-orderings and slight typos
                score = fuzz.token_sort_ratio(name_a, name_b)
                if score >= self.fuzzy_threshold:
                    # If secondary column is present, ensure it's compatible
                    if secondary_column and sec_a and sec_b and sec_a != sec_b:
                        # Skip if distinct secondary categories
                        sec_score = fuzz.ratio(sec_a, sec_b)
                        if sec_score < 70.0:
                            continue

                    matches.append(
                        DuplicateMatch(
                            index_a=idx_a,
                            index_b=idx_b,
                            match_type="FUZZY",
                            similarity_score=round(float(score), 2),
                            matched_fields=[name_column],
                            description=(
                                f"Fuzzy match on `{name_column}` ('{name_a}' vs '{name_b}') "
                                f"with similarity {score:.1f}%."
                            ),
                        )
                    )

        logger.debug(f"Detected {len(matches)} pairwise fuzzy duplicate records.")
        return matches

    def cluster_duplicate_groups(self, matches: List[DuplicateMatch]) -> List[DuplicateGroup]:
        """Group connected duplicate pairs into disjoint duplicate clusters using Union-Find.

        Args:
            matches: Combined list of pairwise matches.

        Returns:
            List[DuplicateGroup]: Disjoint duplicate clusters with assigned canonical indices.
        """
        parent: Dict[int, int] = {}

        def find(i: int) -> int:
            if parent.setdefault(i, i) == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i: int, j: int) -> None:
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                # Always choose the lower index as canonical root
                if root_i < root_j:
                    parent[root_j] = root_i
                else:
                    parent[root_i] = root_j

        for match in matches:
            union(match.index_a, match.index_b)

        clusters: Dict[int, List[int]] = defaultdict(list)
        for match in matches:
            for idx in (match.index_a, match.index_b):
                root = find(idx)
                if idx not in clusters[root]:
                    clusters[root].append(idx)

        # Match type lookup
        match_type_map = {}
        for match in matches:
            key = tuple(sorted((match.index_a, match.index_b)))
            match_type_map[key] = match.match_type

        groups: List[DuplicateGroup] = []
        for group_id, (canonical, members) in enumerate(clusters.items(), start=1):
            sorted_members = sorted(members)
            dupes = [m for m in sorted_members if m != canonical]
            if not dupes:
                continue

            # Determine dominant match type
            m_types = [
                match_type_map.get(tuple(sorted((canonical, d))), "FUZZY")
                for d in dupes
            ]
            primary_type = "EXACT" if "EXACT" in m_types else ("NORMALIZED" if "NORMALIZED" in m_types else "FUZZY")

            sample_id = (
                str(self.df.loc[canonical, "case_id"])
                if "case_id" in self.df.columns
                else f"Row {canonical}"
            )

            groups.append(
                DuplicateGroup(
                    group_id=group_id,
                    canonical_index=canonical,
                    duplicate_indices=dupes,
                    total_records=len(sorted_members),
                    match_type=primary_type,
                    sample_identifier=sample_id,
                )
            )

        return groups

    def run_detection(self) -> DuplicateReport:
        """Run all duplicate detection passes and compile a comprehensive report.

        Returns:
            DuplicateReport: Full diagnostic duplicate detection report.
        """
        logger.info("Executing Multi-Tier Duplicate Detection Engine...")

        exact_matches = self.detect_exact_duplicates()
        norm_matches = self.detect_normalized_duplicates()
        fuzzy_matches = self.detect_fuzzy_duplicates()

        all_matches = exact_matches + norm_matches + fuzzy_matches
        groups = self.cluster_duplicate_groups(all_matches)

        affected_rows: Set[int] = set()
        for g in groups:
            affected_rows.add(g.canonical_index)
            affected_rows.update(g.duplicate_indices)

        report = DuplicateReport(
            total_records=len(self.df),
            exact_duplicate_count=len(exact_matches),
            normalized_duplicate_count=len(norm_matches),
            fuzzy_duplicate_count=len(fuzzy_matches),
            total_unique_records_affected=len(affected_rows),
            duplicate_groups=groups,
            pairwise_matches=all_matches,
        )

        logger.info(
            f"Duplicate Detection complete: {len(groups)} clusters identified "
            f"({len(affected_rows)} total affected rows). "
            f"[Exact: {len(exact_matches)}, Normalized: {len(norm_matches)}, Fuzzy: {len(fuzzy_matches)}]"
        )
        return report


def detect_duplicates(
    df: pd.DataFrame,
    fuzzy_threshold: float = 85.0,
) -> DuplicateReport:
    """Convenience helper to run multi-pass duplicate detection.

    Args:
        df: Input DataFrame.
        fuzzy_threshold: Minimum string similarity score for fuzzy match.

    Returns:
        DuplicateReport: Diagnostic report of duplicate groups and pairwise matches.
    """
    detector = DuplicateDetector(df=df, fuzzy_threshold=fuzzy_threshold)
    return detector.run_detection()
