"""Unit tests for Module 10: Business Analysis."""

import pandas as pd
import pytest

from src.analysis.business_analysis import (
    BusinessAnalysisReport,
    BusinessAnalyzer,
    QuestionAnswer,
    run_business_analysis,
)
from src.cleaning.pipeline import run_cleaning_pipeline
from src.data.load_data import load_raw_data


@pytest.fixture
def clean_test_dataset() -> pd.DataFrame:
    """Fixture providing a cleaned analytical dataset for statistical testing."""
    raw_df = load_raw_data("data/raw/case_management_raw.csv")
    cleaning_res = run_cleaning_pipeline(raw_df=raw_df)
    return cleaning_res.cleaned_df


def test_question_1_closure_trends(clean_test_dataset: pd.DataFrame) -> None:
    """Verify Q1 trend analysis calculates regression metrics and verdict."""
    analyzer = BusinessAnalyzer(clean_test_dataset)
    ans_q1 = analyzer.analyze_question_1_closure_trends()

    assert ans_q1.question_id == "Q1"
    assert ans_q1.confidence_level in ("HIGH", "MEDIUM", "LOW", "CANNOT ANSWER")
    assert "linear_regression" in ans_q1.statistical_metrics
    assert "monthly_slope_days" in ans_q1.statistical_metrics["linear_regression"]
    assert "p_value" in ans_q1.statistical_metrics["linear_regression"]
    assert len(ans_q1.assumptions) > 0
    assert len(ans_q1.limitations) > 0


def test_question_2_duration_drivers(clean_test_dataset: pd.DataFrame) -> None:
    """Verify Q2 driver analysis evaluates categories, priorities, and contact correlation."""
    analyzer = BusinessAnalyzer(clean_test_dataset)
    ans_q2 = analyzer.analyze_question_2_duration_drivers()

    assert ans_q2.question_id == "Q2"
    assert ans_q2.confidence_level in ("HIGH", "MEDIUM", "LOW")
    assert "kruskal_wallis_category" in ans_q2.statistical_metrics
    assert "spearman_contact_correlation" in ans_q2.statistical_metrics
    assert "category_durations" in ans_q2.statistical_metrics
    assert "ols_regression" in ans_q2.statistical_metrics


def test_question_3_triage_effectiveness(clean_test_dataset: pd.DataFrame) -> None:
    """Verify Q3 triage impact analysis calculates Mann-Whitney U and group statistics."""
    analyzer = BusinessAnalyzer(clean_test_dataset)
    ans_q3 = analyzer.analyze_question_3_triage_effectiveness()

    assert ans_q3.question_id == "Q3"
    assert ans_q3.confidence_level in ("HIGH", "MEDIUM", "LOW", "CANNOT ANSWER")
    assert "triaged_cohort" in ans_q3.statistical_metrics
    assert "untriaged_cohort" in ans_q3.statistical_metrics
    assert "statistical_tests" in ans_q3.statistical_metrics
    assert "mann_whitney_p" in ans_q3.statistical_metrics["statistical_tests"]


def test_insufficient_data_cannot_answer() -> None:
    """Verify that insufficient data returns CANNOT ANSWER instead of hallucinating."""
    sparse_df = pd.DataFrame({
        "case_id": ["C1", "C2"],
        "status": ["Closed", "Closed"],
        "category": ["Tech", "Tech"],
        "priority": ["High", "High"],
        "duration_days": [3.0, 4.0],
        "intake_date": ["2024-01-01", "2024-01-02"],
        "closure_date": ["2024-01-04", "2024-01-06"],
        "triaged": [True, True],
        "contact_count": [1, 2],
    })
    analyzer = BusinessAnalyzer(sparse_df)
    ans_q1 = analyzer.analyze_question_1_closure_trends()
    ans_q2 = analyzer.analyze_question_2_duration_drivers()
    ans_q3 = analyzer.analyze_question_3_triage_effectiveness()

    assert ans_q1.confidence_level == "CANNOT ANSWER"
    assert ans_q2.confidence_level == "CANNOT ANSWER"
    assert ans_q3.confidence_level == "CANNOT ANSWER"


def test_run_full_business_analysis(clean_test_dataset: pd.DataFrame) -> None:
    """Verify full end-to-end business analysis report generation."""
    report = run_business_analysis(cleaned_df=clean_test_dataset)
    assert report.total_clean_cases_analyzed > 0
    assert "Q1" in report.answers
    assert "Q2" in report.answers
    assert "Q3" in report.answers
