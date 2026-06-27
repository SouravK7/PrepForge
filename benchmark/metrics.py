"""
Evaluation metrics for benchmark validation.

Computes MAE, RMSE, Pearson R, and Spearman R
between AI scores and human annotator scores.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
from scipy import stats


class BenchmarkMetrics:
    """
    Computes evaluation metrics between AI scores and human scores.

    All methods are static and operate on plain lists of floats.
    """

    @staticmethod
    def mae(
        human_scores: list[float],
        ai_scores: list[float],
    ) -> float:
        """
        Compute Mean Absolute Error.

        MAE = mean(|ai_score - human_score|)

        Args:
            human_scores: Ground truth scores from human annotators.
            ai_scores: Scores predicted by the AI evaluator.

        Returns:
            MAE value. Lower is better.

        Raises:
            ValueError: If lists have different lengths or are empty.
        """
        BenchmarkMetrics._validate(human_scores, ai_scores)

        errors = [abs(ai - human) for ai, human in zip(ai_scores, human_scores)]
        return round(float(np.mean(errors)), 4)

    @staticmethod
    def rmse(
        human_scores: list[float],
        ai_scores: list[float],
    ) -> float:
        """
        Compute Root Mean Squared Error.

        RMSE = sqrt(mean((ai_score - human_score)^2))

        Args:
            human_scores: Ground truth scores from human annotators.
            ai_scores: Scores predicted by the AI evaluator.

        Returns:
            RMSE value. Lower is better.

        Raises:
            ValueError: If lists have different lengths or are empty.
        """
        BenchmarkMetrics._validate(human_scores, ai_scores)

        squared_errors = [(ai - human) ** 2 for ai, human in zip(ai_scores, human_scores)]
        return round(float(math.sqrt(np.mean(squared_errors))), 4)

    @staticmethod
    def pearson_r(
        human_scores: list[float],
        ai_scores: list[float],
    ) -> tuple[float, float]:
        """
        Compute Pearson correlation coefficient.

        Measures linear correlation between AI and human scores.

        Args:
            human_scores: Ground truth scores from human annotators.
            ai_scores: Scores predicted by the AI evaluator.

        Returns:
            Tuple of (pearson_r, p_value).
            Pearson R closer to 1.0 is better.

        Raises:
            ValueError: If lists have different lengths or are empty.
        """
        BenchmarkMetrics._validate(human_scores, ai_scores)

        r, p_value = stats.pearsonr(human_scores, ai_scores)
        return round(float(r), 4), round(float(p_value), 6)

    @staticmethod
    def spearman_r(
        human_scores: list[float],
        ai_scores: list[float],
    ) -> tuple[float, float]:
        """
        Compute Spearman rank correlation coefficient.

        Measures monotonic rank correlation. More robust than
        Pearson when scores are not normally distributed.

        Args:
            human_scores: Ground truth scores from human annotators.
            ai_scores: Scores predicted by the AI evaluator.

        Returns:
            Tuple of (spearman_r, p_value).
            Spearman R closer to 1.0 is better.

        Raises:
            ValueError: If lists have different lengths or are empty.
        """
        BenchmarkMetrics._validate(human_scores, ai_scores)

        r, p_value = stats.spearmanr(human_scores, ai_scores)
        return round(float(r), 4), round(float(p_value), 6)

    @staticmethod
    def all_metrics(
        human_scores: list[float],
        ai_scores: list[float],
    ) -> dict[str, float]:
        """
        Compute all metrics in one call.

        Args:
            human_scores: Ground truth scores.
            ai_scores: AI predicted scores.

        Returns:
            Dictionary with all metric values.
        """
        mae = BenchmarkMetrics.mae(human_scores, ai_scores)
        rmse = BenchmarkMetrics.rmse(human_scores, ai_scores)
        pearson, pearson_p = BenchmarkMetrics.pearson_r(human_scores, ai_scores)
        spearman, spearman_p = BenchmarkMetrics.spearman_r(human_scores, ai_scores)

        return {
            "mae": mae,
            "rmse": rmse,
            "pearson_r": pearson,
            "pearson_p": pearson_p,
            "spearman_r": spearman,
            "spearman_p": spearman_p,
            "n_samples": len(human_scores),
        }

    @staticmethod
    def improvement_over_baseline(
        baseline_pearson: float,
        experiment_pearson: float,
    ) -> float:
        """
        Compute percentage improvement over baseline Pearson R.

        Args:
            baseline_pearson: Pearson R of the baseline experiment.
            experiment_pearson: Pearson R of the current experiment.

        Returns:
            Percentage improvement. Positive means better than baseline.
        """
        if baseline_pearson == 0:
            return 0.0
        improvement = ((experiment_pearson - baseline_pearson) / abs(baseline_pearson)) * 100
        return round(improvement, 2)

    @staticmethod
    def _validate(
        human_scores: list[float],
        ai_scores: list[float],
    ) -> None:
        """
        Validate input lists.

        Args:
            human_scores: Human annotator scores.
            ai_scores: AI predicted scores.

        Raises:
            ValueError: If validation fails.
        """
        if not human_scores or not ai_scores:
            raise ValueError("Score lists cannot be empty")
        if len(human_scores) != len(ai_scores):
            raise ValueError(
                f"Score lists must have equal length. "
                f"Got {len(human_scores)} human and {len(ai_scores)} AI scores."
            )
        if len(human_scores) < 2:
            raise ValueError("Need at least 2 samples to compute metrics")
