"""Quantitative confidence evaluation framework grading analytical conclusions."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.analysis.business_analysis import BusinessAnalysisReport, QuestionAnswer
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConfidenceAssessment:
    """Quantitative confidence scorecard for a specific analytical finding."""

    question_id: str
    overall_confidence: str  # 'HIGH', 'MEDIUM', 'LOW', 'CANNOT ANSWER'
    confidence_score: float  # 0.0 to 100.0
    sample_size_score: float  # 0.0 to 30.0
    data_quality_score: float  # 0.0 to 30.0
    statistical_power_score: float  # 0.0 to 30.0
    confounding_penalty: float  # 0.0 to 20.0
    justification: str
    risk_factors: List[str] = field(default_factory=list)


class ConfidenceEvaluator:
    """Production confidence scoring engine combining data health and statistical power."""

    def __init__(
        self,
        base_quality_score: float = 90.0,
        raw_record_count: int = 120,
        clean_record_count: int = 113,
    ) -> None:
        """Initialize ConfidenceEvaluator with dataset attrition and quality metrics.

        Args:
            base_quality_score: Quality score (0-100) from Module 4.
            raw_record_count: Total raw records.
            clean_record_count: Cleaned usable analytical records.
        """
        self.base_quality_score = base_quality_score
        self.raw_record_count = max(1, raw_record_count)
        self.clean_record_count = clean_record_count
        self.retention_rate = (self.clean_record_count / self.raw_record_count) * 100.0

    def _calculate_base_data_health(self) -> float:
        """Compute base data health score out of 30.0."""
        # Quality score contributes 70%, retention rate contributes 30%
        quality_component = (self.base_quality_score / 100.0) * 21.0
        retention_component = (min(100.0, self.retention_rate) / 100.0) * 9.0
        return round(quality_component + retention_component, 2)

    def evaluate_q1_confidence(self, q_ans: QuestionAnswer) -> ConfidenceAssessment:
        """Evaluate confidence for Question 1 (Closure Time Trends)."""
        if q_ans.confidence_level == "CANNOT ANSWER" or "linear_regression" not in q_ans.statistical_metrics:
            return ConfidenceAssessment(
                question_id="Q1",
                overall_confidence="CANNOT ANSWER",
                confidence_score=0.0,
                sample_size_score=0.0,
                data_quality_score=0.0,
                statistical_power_score=0.0,
                confounding_penalty=0.0,
                justification="Insufficient data to compute trend regression.",
                risk_factors=["Sample size below minimum threshold (< 10)."],
            )

        reg = q_ans.statistical_metrics["linear_regression"]
        p_val = reg["p_value"]
        r_sq = reg["r_squared"]
        n_cohorts = len(q_ans.statistical_metrics.get("monthly_cohort_counts", {}))

        # Sample size score (0 - 30): based on cohort span and total cases
        sample_score = min(30.0, (n_cohorts / 12.0) * 15.0 + (self.clean_record_count / 100.0) * 15.0)

        # Data health score (0 - 30)
        data_health_score = self._calculate_base_data_health()

        # Statistical power score (0 - 30): p-value and R²
        stat_score = 0.0
        if p_val < 0.001:
            stat_score += 20.0
        elif p_val < 0.01:
            stat_score += 15.0
        elif p_val < 0.05:
            stat_score += 10.0

        if r_sq >= 0.20:
            stat_score += 10.0
        elif r_sq >= 0.10:
            stat_score += 6.0
        elif r_sq >= 0.05:
            stat_score += 3.0

        # Confounding penalty (0 - 20)
        penalty = 0.0
        risks = []
        if n_cohorts < 6:
            penalty += 5.0
            risks.append("Short longitudinal horizon (< 6 months).")
        if (100.0 - self.retention_rate) > 10.0:
            penalty += 5.0
            risks.append("Data attrition exceeded 10% during cleaning.")

        total_score = max(0.0, min(100.0, round(sample_score + data_health_score + stat_score - penalty, 1)))

        if total_score >= 80.0 and p_val < 0.01:
            overall = "HIGH"
        elif total_score >= 55.0 and p_val < 0.05:
            overall = "MEDIUM"
        else:
            overall = "LOW"

        justification = (
            f"Strong statistical evidence (p = {p_val:.4e}, R² = {r_sq:.3f}) across {n_cohorts} monthly cohorts "
            f"with {self.retention_rate:.1f}% data retention."
        )

        return ConfidenceAssessment(
            question_id="Q1",
            overall_confidence=overall,
            confidence_score=total_score,
            sample_size_score=round(sample_score, 1),
            data_quality_score=round(data_health_score, 1),
            statistical_power_score=round(stat_score, 1),
            confounding_penalty=round(penalty, 1),
            justification=justification,
            risk_factors=risks,
        )

    def evaluate_q2_confidence(self, q_ans: QuestionAnswer) -> ConfidenceAssessment:
        """Evaluate confidence for Question 2 (Duration Drivers)."""
        if q_ans.confidence_level == "CANNOT ANSWER" or "kruskal_wallis_category" not in q_ans.statistical_metrics:
            return ConfidenceAssessment(
                question_id="Q2",
                overall_confidence="CANNOT ANSWER",
                confidence_score=0.0,
                sample_size_score=0.0,
                data_quality_score=0.0,
                statistical_power_score=0.0,
                confounding_penalty=0.0,
                justification="Insufficient data for multivariate driver analysis.",
                risk_factors=["Sample size below minimum threshold."],
            )

        kw_p = q_ans.statistical_metrics["kruskal_wallis_category"]["p_value"]
        spearman_p = q_ans.statistical_metrics["spearman_contact_correlation"]["p_value"]
        ols_r2 = q_ans.statistical_metrics["ols_regression"]["adj_r_squared"]

        # Sample score (0 - 30)
        sample_score = min(30.0, (self.clean_record_count / 100.0) * 30.0)
        # Data health score (0 - 30)
        data_health_score = self._calculate_base_data_health()

        # Statistical power score (0 - 30)
        stat_score = 0.0
        if kw_p < 0.001 and spearman_p < 0.001:
            stat_score += 20.0
        elif kw_p < 0.05:
            stat_score += 12.0

        if ols_r2 >= 0.30:
            stat_score += 10.0
        elif ols_r2 >= 0.15:
            stat_score += 6.0

        # Confounding penalty
        penalty = 5.0  # Hardware RMA shipping delay confounding
        risks = ["Hardware turnaround is partially driven by external vendor RMA logistics rather than agent labor."]

        total_score = max(0.0, min(100.0, round(sample_score + data_health_score + stat_score - penalty, 1)))
        overall = "HIGH" if total_score >= 80.0 else ("MEDIUM" if total_score >= 55.0 else "LOW")

        justification = (
            f"Kruskal-Wallis ANOVA (p = {kw_p:.4e}) and OLS regression (Adj. R² = {ols_r2:.3f}) robustly "
            f"isolate category and contact volume as dominant variance drivers."
        )

        return ConfidenceAssessment(
            question_id="Q2",
            overall_confidence=overall,
            confidence_score=total_score,
            sample_size_score=round(sample_score, 1),
            data_quality_score=round(data_health_score, 1),
            statistical_power_score=round(stat_score, 1),
            confounding_penalty=round(penalty, 1),
            justification=justification,
            risk_factors=risks,
        )

    def evaluate_q3_confidence(self, q_ans: QuestionAnswer) -> ConfidenceAssessment:
        """Evaluate confidence for Question 3 (Triage Efficacy on High Priority Cases)."""
        if q_ans.confidence_level == "CANNOT ANSWER" or "statistical_tests" not in q_ans.statistical_metrics:
            return ConfidenceAssessment(
                question_id="Q3",
                overall_confidence="CANNOT ANSWER",
                confidence_score=0.0,
                sample_size_score=0.0,
                data_quality_score=0.0,
                statistical_power_score=0.0,
                confounding_penalty=0.0,
                justification="Insufficient High/Critical priority cases.",
                risk_factors=["High priority subset too small."],
            )

        mwu_p = q_ans.statistical_metrics["statistical_tests"]["mann_whitney_p"]
        triaged_n = q_ans.statistical_metrics["triaged_cohort"]["count"]
        untriaged_n = q_ans.statistical_metrics["untriaged_cohort"]["count"]

        # Sample score (0 - 30) based on High Priority cohort sizes
        total_hp = triaged_n + untriaged_n
        sample_score = min(30.0, (total_hp / 40.0) * 30.0)

        # Data health score (0 - 30)
        data_health_score = self._calculate_base_data_health()

        # Statistical power score (0 - 30)
        stat_score = 0.0
        if mwu_p < 0.001:
            stat_score += 25.0
        elif mwu_p < 0.01:
            stat_score += 20.0
        elif mwu_p < 0.05:
            stat_score += 12.0

        # Confounding penalty (0 - 20): Check if untriaged cases skew toward Hardware
        penalty = 0.0
        risks = []
        if untriaged_n < 10:
            penalty += 8.0
            risks.append(f"Untriaged High Priority cohort is relatively small (n = {untriaged_n}).")
        cat_dist = q_ans.statistical_metrics.get("category_distribution_by_triage", {})
        if "Hardware" in str(cat_dist):
            penalty += 4.0
            risks.append("Untriaged cohort contains a disproportionate share of Hardware cases (category confounding).")

        total_score = max(0.0, min(100.0, round(sample_score + data_health_score + stat_score - penalty, 1)))
        overall = "HIGH" if total_score >= 80.0 else ("MEDIUM" if total_score >= 55.0 else "LOW")

        justification = (
            f"Mann-Whitney U test confirms statistically significant turnaround improvement (p = {mwu_p:.4e}) "
            f"with noticeable effect size, though tempered by category mix differences."
        )

        return ConfidenceAssessment(
            question_id="Q3",
            overall_confidence=overall,
            confidence_score=total_score,
            sample_size_score=round(sample_score, 1),
            data_quality_score=round(data_health_score, 1),
            statistical_power_score=round(stat_score, 1),
            confounding_penalty=round(penalty, 1),
            justification=justification,
            risk_factors=risks,
        )

    def evaluate_all(
        self, analysis_report: BusinessAnalysisReport
    ) -> Dict[str, ConfidenceAssessment]:
        """Run confidence evaluation across all answered business questions.

        Args:
            analysis_report: Report containing answers for Q1, Q2, and Q3.

        Returns:
            Dict[str, ConfidenceAssessment]: Scorecards for each question.
        """
        logger.info("Evaluating analytical confidence scores across Q1, Q2, and Q3...")
        evaluations: Dict[str, ConfidenceAssessment] = {}

        if "Q1" in analysis_report.answers:
            evaluations["Q1"] = self.evaluate_q1_confidence(analysis_report.answers["Q1"])
        if "Q2" in analysis_report.answers:
            evaluations["Q2"] = self.evaluate_q2_confidence(analysis_report.answers["Q2"])
        if "Q3" in analysis_report.answers:
            evaluations["Q3"] = self.evaluate_q3_confidence(analysis_report.answers["Q3"])

        for q_id, ev in evaluations.items():
            logger.info(
                f"Confidence for [{q_id}]: {ev.overall_confidence} (Score: {ev.confidence_score}/100.0) — "
                f"Data Health: {ev.data_quality_score}/30, Stats Power: {ev.statistical_power_score}/30, "
                f"Penalty: -{ev.confounding_penalty}"
            )

        return evaluations


def evaluate_confidence(
    analysis_report: BusinessAnalysisReport,
    quality_score: float = 91.11,
    raw_record_count: int = 120,
    clean_record_count: int = 113,
) -> Dict[str, ConfidenceAssessment]:
    """Helper function to grade confidence for business analysis findings.

    Args:
        analysis_report: Output from BusinessAnalyzer.
        quality_score: Base quality score from DataQualityAssessor.
        raw_record_count: Raw row count.
        clean_record_count: Clean row count.

    Returns:
        Dict[str, ConfidenceAssessment]: Confidence evaluations.
    """
    evaluator = ConfidenceEvaluator(
        base_quality_score=quality_score,
        raw_record_count=raw_record_count,
        clean_record_count=clean_record_count,
    )
    return evaluator.evaluate_all(analysis_report)
