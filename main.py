#!/usr/bin/env python3
"""Dirty Data, Real Decisions — Master Pipeline CLI Entrypoint.

Brite Sparks 2026 Hackathon Solution
"""

import argparse
import logging
import sys
from pathlib import Path

from src.data.load_data import load_raw_data
from src.profiling.profiling import generate_profiling_report
from src.utils.logger import get_logger, setup_logging

logger = get_logger("main")


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser with modular subcommands.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="dirty-data-pipeline",
        description="Brite Sparks 2026: Defensive case management cleaning and decision engine.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--raw-path",
        type=Path,
        default=Path("data/raw/case_management_raw.csv"),
        help="Path to the raw input CSV export.",
    )
    parser.add_argument(
        "--cleaned-path",
        type=Path,
        default=Path("data/cleaned/case_management_cleaned.csv"),
        help="Target path for the cleaned CSV dataset.",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=Path("data/logs/cleaning_log.csv"),
        help="Target path for the row-level audit cleaning log.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG level logging output.",
    )
    parser.add_argument(
        "--module",
        "-m",
        type=str,
        choices=[
            "all",
            "load",
            "profile",
            "quality",
            "duplicates",
            "dates",
            "categories",
            "clean",
            "analyze",
            "visualize",
            "report",
        ],
        default="all",
        help="Target pipeline module to execute.",
    )

    return parser


def main() -> int:
    """Main CLI execution handler.

    Returns:
        int: Process return code (0 for success, non-zero for error).
    """
    parser = build_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level=log_level)

    logger.info("Initializing Dirty Data, Real Decisions Pipeline")
    logger.info(f"Target Module: {args.module} | Raw Data Source: {args.raw_path}")

    try:
        # Step 1: Load Data
        if args.module in ("load", "profile", "all"):
            logger.info("--- Executing Module 2: Data Loading ---")
            df = load_raw_data(args.raw_path)
            logger.info(f"Data loading successful. Loaded {len(df)} records.")

        # Step 2: Data Profiling
        if args.module in ("profile", "all"):
            logger.info("--- Executing Module 3: Data Profiling ---")
            profiling_export = Path("reports/exports/profiling_summary.md")
            profile = generate_profiling_report(
                df=df,
                source_name=args.raw_path.name,
                output_path=profiling_export,
            )
            logger.info(
                f"Profiling summary exported to {profiling_export} "
                f"({profile.row_count} rows, {profile.column_count} columns)."
            )

        return 0
    except Exception as exc:
        logger.error(f"Pipeline execution failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
