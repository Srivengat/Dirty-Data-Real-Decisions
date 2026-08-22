#!/usr/bin/env python3
"""Dirty Data, Real Decisions — Master Pipeline CLI Entrypoint.

Brite Sparks 2026 Hackathon Solution
"""

import argparse
import logging
import sys
from pathlib import Path

from src.analysis.business_analysis import run_business_analysis
from src.analysis.confidence import evaluate_confidence
from src.cleaning.category_normalization import normalize_categories
from src.cleaning.pipeline import run_cleaning_pipeline
from src.data.load_data import load_raw_data
from src.profiling.profiling import generate_profiling_report
from src.quality.assessment import run_quality_assessment
from src.quality.date_validation import validate_dates
from src.quality.duplicates import detect_duplicates
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
        if args.module in ("load", "profile", "quality", "duplicates", "dates", "categories", "clean", "analyze", "all"):
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

        # Step 3: Data Quality Assessment
        quality_score = 91.11
        if args.module in ("quality", "all"):
            logger.info("--- Executing Module 4: Data Quality Assessment ---")
            quality_export = Path("reports/exports/data_quality_report.md")
            report = run_quality_assessment(
                df=df,
                dataset_name=args.raw_path.name,
                output_path=quality_export,
            )
            quality_score = report.quality_score
            logger.info(
                f"Quality assessment exported to {quality_export} "
                f"(Score: {report.quality_score}/100, Anomalies: {report.total_anomalies})."
            )

        # Step 4: Duplicate Detection
        if args.module in ("duplicates", "all"):
            logger.info("--- Executing Module 5: Duplicate Detection ---")
            dupe_report = detect_duplicates(df=df)
            logger.info(
                f"Duplicate detection completed: {len(dupe_report.duplicate_groups)} clusters identified "
                f"({dupe_report.total_unique_records_affected} total rows affected)."
            )

        # Step 5: Date Validation
        if args.module in ("dates", "all"):
            logger.info("--- Executing Module 6: Date Validation ---")
            date_summary = validate_dates(df=df)
            logger.info(
                f"Date validation completed: {date_summary.valid_date_records}/{date_summary.total_records} valid records. "
                f"Mean closure duration: {date_summary.mean_duration_days} days."
            )

        # Step 6: Category Normalization
        if args.module in ("categories", "all"):
            logger.info("--- Executing Module 7: Category Normalization ---")
            df_norm, cat_records = normalize_categories(df=df)
            modified_count = sum(1 for r in cat_records if r.was_modified)
            logger.info(
                f"Category normalization complete: {modified_count} fields standardized across {len(df_norm)} rows."
            )

        # Step 7: Cleaning Pipeline & Audit Logging
        if args.module in ("clean", "analyze", "all"):
            logger.info("--- Executing Module 8 & 9: Cleaning Pipeline & Audit Logging ---")
            cleaning_result = run_cleaning_pipeline(
                raw_df=df,
                output_cleaned_path=args.cleaned_path,
                output_log_path=args.log_path,
            )
            logger.info(
                f"Cleaning pipeline completed: {cleaning_result.initial_rows} raw -> "
                f"{cleaning_result.final_rows} clean records saved to {args.cleaned_path} "
                f"({cleaning_result.quarantined_rows_count} quarantined, "
                f"{cleaning_result.deduplicated_rows_count} deduplicated)."
            )
            cleaned_df = cleaning_result.cleaned_df

        # Step 8: Business Analysis & Confidence Framework
        if args.module in ("analyze", "all"):
            logger.info("--- Executing Module 10 & 11: Business Analysis & Confidence Framework ---")
            analysis_report = run_business_analysis(cleaned_df=cleaned_df)
            confidence_evals = evaluate_confidence(
                analysis_report=analysis_report,
                quality_score=quality_score,
                raw_record_count=len(df),
                clean_record_count=len(cleaned_df),
            )

            for q_id, ans in analysis_report.answers.items():
                conf = confidence_evals.get(q_id)
                score_str = f"Score: {conf.confidence_score}/100" if conf else ""
                logger.info(
                    f"[{q_id}] {ans.question_text}\n"
                    f"     -> Verdict: {ans.verdict}\n"
                    f"     -> Confidence: {conf.overall_confidence if conf else ans.confidence_level} ({score_str})"
                )

        return 0
    except Exception as exc:
        logger.error(f"Pipeline execution failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
