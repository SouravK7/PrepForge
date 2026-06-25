"""
Benchmark schemas.

Data contracts for the scientific validation framework.
Used to measure AI evaluator accuracy against human scores.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkAnswer(BaseModel):
    """
    A single human-annotated answer in the benchmark dataset.

    Answers are categorized as poor, average, good, or excellent.
    Human scores are averages from multiple annotators.
    """

    model_config = ConfigDict(frozen=True)

    answer_type: str = Field(
        ...,
        description="poor, average, good, or excellent",
    )
    text: str = Field(..., description="The answer text")
    human_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average human annotator score",
    )
    annotator_scores: list[float] = Field(
        default_factory=list,
        description="Individual scores from each annotator",
    )
    notes: str = Field(
        default="",
        description="Annotator notes about this answer",
    )


class BenchmarkQuestion(BaseModel):
    """
    A single question with multiple annotated answers for benchmarking.
    """

    model_config = ConfigDict(frozen=True)

    question_id: str = Field(..., description="Links to question bank")
    question_text: str = Field(..., description="The question")
    competency_id: str = Field(..., description="Which competency this tests")
    required_concepts: list[str] = Field(
        ...,
        description="Expected concepts for evaluation",
    )
    answers: list[BenchmarkAnswer] = Field(
        ...,
        min_length=1,
        description="Annotated answers for this question",
    )


class BenchmarkResult(BaseModel):
    """Result of running the evaluator on one benchmark answer."""

    model_config = ConfigDict(frozen=False)

    question_id: str = Field(..., description="Question evaluated")
    answer_type: str = Field(..., description="poor, average, good, or excellent")
    human_score: float = Field(..., description="Ground truth human score")
    ai_score: float = Field(..., description="AI evaluator prediction")
    absolute_error: float = Field(..., description="abs(ai_score - human_score)")
    squared_error: float = Field(..., description="(ai_score - human_score)^2")
    dimension_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Individual evaluator scores for ablation tracking",
    )


class BenchmarkRunReport(BaseModel):
    """
    Complete report from a benchmark run.

    Contains aggregate metrics and per-question results.
    Used to validate evaluator accuracy and run ablation studies.
    """

    model_config = ConfigDict(frozen=False)

    run_id: str = Field(..., description="Unique run identifier")
    experiment_name: str = Field(
        ...,
        description="e.g. semantic_only or full_ensemble",
    )
    evaluators_used: list[str] = Field(
        ...,
        description="Which evaluators were active in this run",
    )
    total_answers: int = Field(..., description="Total answers evaluated")
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    pearson_r: float = Field(..., description="Pearson correlation coefficient")
    spearman_r: float = Field(..., description="Spearman rank correlation")
    results: list[BenchmarkResult] = Field(
        ...,
        description="Per-answer results",
    )
    run_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this benchmark was run",
    )
    notes: str = Field(default="", description="Run notes and observations")


class AblationResult(BaseModel):
    """Result from a single ablation study experiment."""

    model_config = ConfigDict(frozen=True)

    experiment_name: str = Field(..., description="Name of this ablation experiment")
    evaluators_used: list[str] = Field(..., description="Active evaluators")
    mae: float = Field(..., description="MAE for this configuration")
    rmse: float = Field(..., description="RMSE for this configuration")
    pearson_r: float = Field(..., description="Pearson R for this configuration")
    improvement_over_baseline: Optional[float] = Field(
        default=None,
        description="Percentage improvement over semantic-only baseline",
    )


class ErrorAnalysisEntry(BaseModel):
    """A single entry in the error analysis report."""

    model_config = ConfigDict(frozen=True)

    question_id: str = Field(..., description="Question with error")
    answer_type: str = Field(..., description="Answer quality category")
    human_score: float = Field(..., description="Ground truth")
    ai_score: float = Field(..., description="AI prediction")
    error: float = Field(..., description="Signed error ai - human")
    absolute_error: float = Field(..., description="Absolute error")
    error_category: str = Field(
        ...,
        description="over_scored, under_scored, or accurate",
    )
    likely_cause: str = Field(
        default="",
        description="Hypothesis about why this error occurred",
    )
