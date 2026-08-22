#!/usr/bin/env python3
"""Dirty Data, Real Decisions — Master Pipeline CLI Entrypoint.

Brite Sparks 2026 Hackathon Solution
"""

import argparse
import logging
import sys
from pathlib import Path

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

    if not args.raw_path.exists():
        logger.warning(f"Raw data file not found at: {args.raw_path}")

    # Skeleton handler for Module 1 project setup
    logger.info("Pipeline scaffolding initialized successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
