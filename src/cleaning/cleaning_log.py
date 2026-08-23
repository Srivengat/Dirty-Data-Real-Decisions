"""Immutable audit logging module tracking every data transformation and record decision."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CleaningAuditEntry:
    """Represents a single atomic modification or decision in the cleaning pipeline."""

    row_index: int
    case_id: str
    column_name: str
    old_value: str
    new_value: str
    transformation_rule: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AuditLogger:
    """Centralized audit logger capturing row-level transformations for compliance and reproducibility."""

    def __init__(self) -> None:
        """Initialize an empty audit log repository."""
        self._entries: List[CleaningAuditEntry] = []

    def log(
        self,
        row_index: int,
        case_id: str,
        column_name: str,
        old_value: Any,
        new_value: Any,
        transformation_rule: str,
        reason: str,
    ) -> None:
        """Record an atomic transformation entry.

        Args:
            row_index: Positional index in raw dataset.
            case_id: Unique case identifier or empty string if missing.
            column_name: Target column name (or 'RECORD' for row-level lifecycle actions).
            old_value: Raw value prior to modification.
            new_value: Cleaned value post modification.
            transformation_rule: Machine-readable rule identifier.
            reason: Human-readable analytical justification.
        """
        old_str = "" if pd.isna(old_value) else str(old_value)
        new_str = "" if pd.isna(new_value) else str(new_value)

        # Do not log no-ops if value was completely unchanged (unless it's a record lifecycle action)
        if old_str == new_str and column_name != "RECORD":
            return

        entry = CleaningAuditEntry(
            row_index=row_index,
            case_id=str(case_id),
            column_name=column_name,
            old_value=old_str,
            new_value=new_str,
            transformation_rule=transformation_rule,
            reason=reason,
        )
        self._entries.append(entry)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert accumulated audit entries into a pandas DataFrame.

        Returns:
            pd.DataFrame: Tabular cleaning log.
        """
        if not self._entries:
            return pd.DataFrame(
                columns=[
                    "row_index",
                    "case_id",
                    "column_name",
                    "old_value",
                    "new_value",
                    "transformation_rule",
                    "reason",
                    "timestamp",
                ]
            )
        return pd.DataFrame([asdict(e) for e in self._entries])

    def export_csv(
        self, output_path: Union[str, Path] = "data/logs/cleaning_log.csv"
    ) -> Path:
        """Write the audit log to a CSV file.

        Args:
            output_path: Target destination path.

        Returns:
            Path: Written file path.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df_log = self.to_dataframe()
        df_log.to_csv(path, index=False, encoding="utf-8")
        logger.info(
            f"Exported cleaning audit log ({len(self._entries)} entries) to: {path.resolve()}"
        )
        return path

    def summary(self) -> Dict[str, Any]:
        """Generate high-level summary statistics of applied transformations.

        Returns:
            Dict[str, Any]: Summary dictionary with transformation breakdown.
        """
        df_log = self.to_dataframe()
        if df_log.empty:
            return {
                "total_modifications": 0,
                "affected_rows": 0,
                "rules_breakdown": {},
                "columns_breakdown": {},
            }

        return {
            "total_modifications": len(df_log),
            "affected_rows": int(df_log["row_index"].nunique()),
            "rules_breakdown": df_log["transformation_rule"].value_counts().to_dict(),
            "columns_breakdown": df_log["column_name"].value_counts().to_dict(),
        }

    @property
    def entries(self) -> List[CleaningAuditEntry]:
        """Read-only view of recorded audit entries."""
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
