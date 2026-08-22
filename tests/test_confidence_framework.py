"""Unit tests for Module 11: Confidence Evaluation Framework."""

import pandas as pd
import pytest

from src.analysis.business_analysis import BusinessAnalyzer, QuestionAnswer
from src.analysis.confidence import (
    ConfidenceAssessment,
    ConfidenceEvaluator,
    evaluate_confidence,
)
from src.cleaning.pipeline import run_cleaning_pipeline
from src.data.load_data import load_raw_data


@pytest.fixture
def business_report():
    """Fixture generating a business analysis report from raw data."""
    raw_df = load_raw_data("data/raw/case_management_raw.csv")
    cleaning_res = run_cleaning_pipeline(raw_df=raw_df)
    analyzer = BusinessAnalyzer(cleaning_res.cleaned_df)
    return analyzer.run_full_analysis()


def test_confidence_scoring_q1(business_report) -> None:
    """Verify quantitative confidence calculation for Question 1."""
    evaluator = ConfidenceEvaluator(base_quality_score=91.1, raw_record_count=120, clean_record_count=113)
    assessment = evaluator.evaluate_q1_confidence(business_report.answers["Q1"])

    assert assessment.question_id == "Q1"
    assert assessment.overall_confidence in ("HIGH", "MEDIUM")
    assert 0.0 <= assessment.confidence_score <= 100.0
    assert assessment.sample_size_score > 0
    assert assessment.data_quality_score > 0
    assert assessment.statistical_power_score > 0


def test_confidence_scoring_q2(business_report) -> None:
    """Verify quantitative confidence calculation for Question 2."""
    evaluator = ConfidenceEvaluator(base_quality_score=91.1, raw_record_count=120, clean_record_count=113)
    assessment = evaluator.evaluate_q2_confidence(business_report.answers["Q2"])

    assert assessment.question_id == "Q2"
    assert assessment.overall_confidence in ("HIGH", "MEDIUM")
    assert assessment.confidence_score >= 70.0


def test_confidence_scoring_q3(business_report) -> None:
    """Verify quantitative confidence calculation for Question 3."""
    evaluator = ConfidenceEvaluator(base_quality_score=91.1, raw_record_count=120, clean_record_count=113)
    assessment = evaluator.evaluate_q3_confidence(business_report.answers["Q3"])

    assert assessment.question_id == "Q3"
    assert assessment.overall_confidence in ("HIGH", "MEDIUM")
    assert assessment.confounding_penalty >= 0


def test_cannot_answer_confidence() -> None:
    """Verify that CANNOT ANSWER leads to 0.0 confidence score."""
    q_blank = QuestionAnswer(
        question_id="Q1",
        question_text="Sample question",
        verdict="CANNOT ANSWER",
        confidence_level="CANNOT ANSWER",
        evidence_summary="Insufficient data.",
    )
    evaluator = ConfidenceEvaluator()
    assessment = evaluator.evaluate_q1_confidence(q_blank)

    assert assessment.overall_confidence == "CANNOT ANSWER"
    assert assessment.confidence_score == 0.0


def test_full_confidence_evaluation(business_report) -> None:
    """Verify evaluate_confidence runs across Q1, Q2, and Q3."""
    evals = evaluate_confidence(
        analysis_report=business_report,
        quality_score=91.11,
        raw_record_count=120,
        clean_record_count=113,
    )
    assert set(evals.keys()) == {"Q1", "Q2", "Q3"}
    for q_id, ev in evals.items():
        assert isinstance(ev, ConfidenceAssessment)
        assert ev.confidence_score > 0
