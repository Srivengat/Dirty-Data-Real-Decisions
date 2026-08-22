"""Defensive date parsing, temporal consistency validation, and duration calculation module."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

CURRENT_REFERENCE_CUTOFF = pd.Timestamp("2026-08-22")


@dataclass
class DateValidationResult:
    """Detailed temporal validation metrics for a single record."""

    row_index: int
    raw_intake: str
    parsed_intake: Optional[pd.Timestamp]
    raw_closure: str
    parsed_closure: Optional[pd.Timestamp]
    raw_triage: str
    parsed_triage: Optional[pd.Timestamp]
    duration_days: Optional[float]
    is_valid: bool
    error_flags: List[str] = field(default_factory=list)


@dataclass
class DateValidationSummary:
    """Aggregate summary of dataset date validation."""

    total_records: int
    valid_date_records: int
    unparseable_intake_count: int
    unparseable_closure_count: int
    future_date_count: int
    negative_duration_count: int
    triage_order_violation_count: int
    open_cases_count: int
    mean_duration_days: Optional[float]
    median_duration_days: Optional[float]
    results: List[DateValidationResult] = field(default_factory=list)


class DateValidator:
    """Defensive date validator handling heterogeneous timestamp formats and temporal anomalies."""

    def __init__(self, reference_cutoff: pd.Timestamp = CURRENT_REFERENCE_CUTOFF) -> None:
        """Initialize DateValidator with reference date cutoff.

        Args:
            reference_cutoff: Latest allowable intake timestamp.
        """
        self.reference_cutoff = reference_cutoff

    def parse_single_date(self, date_val: Any) -> Optional[pd.Timestamp]:
        """Robustly parse a single date string into a UTC-normalized pd.Timestamp.

        Supports ISO-8601 (YYYY-MM-DD), US Slash (MM/DD/YYYY), European Slash (DD/MM/YYYY),
        and dot-delimited (YYYY.MM.DD) formats.

        Args:
            date_val: Raw date input (string, Timestamp, or NaN).

        Returns:
            Optional[pd.Timestamp]: Parsed timestamp or None if invalid/empty.
        """
        if pd.isna(date_val):
            return None

        clean_str = str(date_val).strip()
        if not clean_str or clean_str.lower() in ("nan", "none", "null", "nat", ""):
            return None

        # Check for obvious impossible month/day combinations before pandas parsing
        # (e.g., 2024-13-45)
        iso_match = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", clean_str)
        if iso_match:
            year, month, day = map(int, iso_match.groups())
            if month < 1 or month > 12 or day < 1 or day > 31:
                return None
            try:
                return pd.Timestamp(year=year, month=month, day=day)
            except ValueError:
                return None

        # Check slash format (e.g. 15/05/2024 vs 06/15/2024)
        slash_match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", clean_str)
        if slash_match:
            p1, p2, year = map(int, slash_match.groups())
            # If p1 > 12, it must be DD/MM/YYYY
            if p1 > 12 and 1 <= p2 <= 12 and 1 <= p1 <= 31:
                try:
                    return pd.Timestamp(year=year, month=p2, day=p1)
                except ValueError:
                    return None
            # If p2 > 12, it must be MM/DD/YYYY
            elif p2 > 12 and 1 <= p1 <= 12 and 1 <= p2 <= 31:
                try:
                    return pd.Timestamp(year=year, month=p1, day=p2)
                except ValueError:
                    return None
            # If both <= 12, default to MM/DD/YYYY standard
            elif 1 <= p1 <= 12 and 1 <= p2 <= 31:
                try:
                    return pd.Timestamp(year=year, month=p1, day=p2)
                except ValueError:
                    return None

        # Fallback to general pandas mixed parser
        try:
            ts = pd.to_datetime(clean_str, format="mixed", errors="coerce")
            if pd.isna(ts):
                return None
            return pd.Timestamp(ts)
        except Exception:
            return None

    def validate_record(
        self,
        row_index: int,
        intake_str: Any,
        closure_str: Any,
        triage_str: Any = None,
    ) -> DateValidationResult:
        """Validate temporal consistency and duration metrics for a single case record.

        Args:
            row_index: Positional index of record.
            intake_str: Raw intake date.
            closure_str: Raw closure date.
            triage_str: Optional raw triage date.

        Returns:
            DateValidationResult: Record validation verdict.
        """
        error_flags: List[str] = []

        parsed_intake = self.parse_single_date(intake_str)
        parsed_closure = self.parse_single_date(closure_str)
        parsed_triage = self.parse_single_date(triage_str)

        raw_intake_str = "" if pd.isna(intake_str) else str(intake_str).strip()
        raw_closure_str = "" if pd.isna(closure_str) else str(closure_str).strip()
        raw_triage_str = "" if pd.isna(triage_str) else str(triage_str).strip()

        # 1. Validate Intake Date
        if raw_intake_str and parsed_intake is None:
            error_flags.append("INVALID_INTAKE_FORMAT")
        elif not raw_intake_str:
            error_flags.append("MISSING_INTAKE_DATE")
        elif parsed_intake and parsed_intake > self.reference_cutoff:
            error_flags.append("FUTURE_INTAKE_DATE")

        # 2. Validate Closure Date
        if raw_closure_str and parsed_closure is None:
            error_flags.append("INVALID_CLOSURE_FORMAT")

        # 3. Calculate Duration & Chronological Order
        duration_days: Optional[float] = None
        if parsed_intake is not None and parsed_closure is not None:
            delta_seconds = (parsed_closure - parsed_intake).total_seconds()
            duration_days = round(delta_seconds / 86400.0, 2)

            if duration_days < 0:
                error_flags.append("NEGATIVE_DURATION")

        # 4. Validate Triage Timing
        if raw_triage_str and parsed_triage is None:
            error_flags.append("INVALID_TRIAGE_FORMAT")
        elif parsed_triage is not None and parsed_intake is not None:
            if parsed_triage < parsed_intake:
                error_flags.append("TRIAGE_BEFORE_INTAKE")
            if parsed_closure is not None and parsed_triage > parsed_closure:
                error_flags.append("TRIAGE_AFTER_CLOSURE")

        is_valid = len(error_flags) == 0

        return DateValidationResult(
            row_index=row_index,
            raw_intake=raw_intake_str,
            parsed_intake=parsed_intake,
            raw_closure=raw_closure_str,
            parsed_closure=parsed_closure,
            raw_triage=raw_triage_str,
            parsed_triage=parsed_triage,
            duration_days=duration_days,
            is_valid=is_valid,
            error_flags=error_flags,
        )

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        intake_col: str = "intake_date",
        closure_col: str = "closure_date",
        triage_col: str = "triage_date",
    ) -> DateValidationSummary:
        """Run date validation across an entire DataFrame.

        Args:
            df: Input pandas DataFrame.
            intake_col: Column name for intake dates.
            closure_col: Column name for closure dates.
            triage_col: Column name for triage dates.

        Returns:
            DateValidationSummary: Aggregate temporal validation statistics.
        """
        logger.info(f"Validating dates across {len(df)} records...")
        results: List[DateValidationResult] = []

        unparseable_intake = 0
        unparseable_closure = 0
        future_dates = 0
        negative_durations = 0
        triage_violations = 0
        open_cases = 0
        valid_durations: List[float] = []

        for idx, row in df.iterrows():
            intake_val = row.get(intake_col, None)
            closure_val = row.get(closure_col, None)
            triage_val = row.get(triage_col, None) if triage_col in df.columns else None

            res = self.validate_record(int(idx), intake_val, closure_val, triage_val)
            results.append(res)

            if "INVALID_INTAKE_FORMAT" in res.error_flags:
                unparseable_intake += 1
            if "INVALID_CLOSURE_FORMAT" in res.error_flags:
                unparseable_closure += 1
            if "FUTURE_INTAKE_DATE" in res.error_flags:
                future_dates += 1
            if "NEGATIVE_DURATION" in res.error_flags:
                negative_durations += 1
            if any(flag in res.error_flags for flag in ("TRIAGE_BEFORE_INTAKE", "TRIAGE_AFTER_CLOSURE")):
                triage_violations += 1
            if res.parsed_intake is not None and res.parsed_closure is None and "INVALID_CLOSURE_FORMAT" not in res.error_flags:
                open_cases += 1
            if res.is_valid and res.duration_days is not None and res.duration_days >= 0:
                valid_durations.append(res.duration_days)

        valid_count = sum(1 for r in results if r.is_valid)
        mean_dur = round(float(np.mean(valid_durations)), 2) if valid_durations else None
        median_dur = round(float(np.median(valid_durations)), 2) if valid_durations else None

        summary = DateValidationSummary(
            total_records=len(df),
            valid_date_records=valid_count,
            unparseable_intake_count=unparseable_intake,
            unparseable_closure_count=unparseable_closure,
            future_date_count=future_dates,
            negative_duration_count=negative_durations,
            triage_order_violation_count=triage_violations,
            open_cases_count=open_cases,
            mean_duration_days=mean_dur,
            median_duration_days=median_dur,
            results=results,
        )

        logger.info(
            f"Date validation complete: {valid_count}/{len(df)} records valid. "
            f"Anomalies: {unparseable_intake} bad intake, {unparseable_closure} bad closure, "
            f"{future_dates} future, {negative_durations} negative duration. "
            f"Mean closure duration: {mean_dur} days."
        )
        return summary


def validate_dates(
    df: pd.DataFrame,
    intake_col: str = "intake_date",
    closure_col: str = "closure_date",
    triage_col: str = "triage_date",
) -> DateValidationSummary:
    """Convenience helper to validate dataset dates and compute resolution durations.

    Args:
        df: Input DataFrame.
        intake_col: Intake date column name.
        closure_col: Closure date column name.
        triage_col: Triage date column name.

    Returns:
        DateValidationSummary: Structured date audit summary.
    """
    validator = DateValidator()
    return validator.validate_dataframe(df, intake_col, closure_col, triage_col)
