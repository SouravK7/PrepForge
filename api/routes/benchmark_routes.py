"""
Benchmark routes.

Endpoints to run and retrieve benchmark validation results.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from database.models import User
from database.repositories import BenchmarkRepository
from benchmark.run_benchmark import BenchmarkRunner
from benchmark.ablation_runner import AblationRunner

router = APIRouter()


class RunBenchmarkRequest(BaseModel):
    """Request to run a benchmark."""

    benchmark_file: str = Field(default="oop_benchmark_v1")
    experiment_name: str = Field(default="full_ensemble")
    save_report: bool = Field(default=True)


@router.post(
    "/run",
    summary="Run benchmark validation",
)
def run_benchmark(
    request: RunBenchmarkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Run the evaluation ensemble against benchmark dataset.

    Args:
        request: Benchmark run parameters.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Benchmark report with MAE, RMSE, Pearson R.
    """
    try:
        runner = BenchmarkRunner()
        report = runner.run(
            benchmark_file=request.benchmark_file,
            experiment_name=request.experiment_name,
            save_report=request.save_report,
        )

        # Save to database
        if request.save_report:
            repo = BenchmarkRepository(db)
            repo.save_run(
                run_id=report.run_id,
                experiment_name=report.experiment_name,
                benchmark_file=request.benchmark_file,
                evaluators_used=report.evaluators_used,
                total_answers=report.total_answers,
                mae=report.mae,
                rmse=report.rmse,
                pearson_r=report.pearson_r,
                spearman_r=report.spearman_r,
            )

        return {
            "run_id": report.run_id,
            "experiment_name": report.experiment_name,
            "total_answers": report.total_answers,
            "mae": report.mae,
            "rmse": report.rmse,
            "pearson_r": report.pearson_r,
            "spearman_r": report.spearman_r,
            "results": [
                {
                    "question_id": r.question_id,
                    "answer_type": r.answer_type,
                    "human_score": r.human_score,
                    "ai_score": r.ai_score,
                    "absolute_error": r.absolute_error,
                }
                for r in report.results
            ],
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/ablation",
    summary="Run ablation study",
)
def run_ablation(
    benchmark_file: str = "oop_benchmark_v1",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Run ablation study showing each evaluator's contribution.

    Args:
        benchmark_file: Target benchmark file.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of results for each ablation configuration.
    """
    try:
        runner = AblationRunner()
        results = runner.run_study(
            benchmark_file=benchmark_file,
            save_results=True,
        )

        return [
            {
                "experiment_name": r.experiment_name,
                "evaluators_used": r.evaluators_used,
                "mae": r.mae,
                "rmse": r.rmse,
                "pearson_r": r.pearson_r,
                "spearman_r": r.spearman_r,
            }
            for r in results
        ]
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/history",
    summary="Get benchmark history",
)
def get_benchmark_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get past benchmark runs.

    Args:
        limit: Max results.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of benchmark run records.
    """
    repo = BenchmarkRepository(db)
    records = repo.get_latest_runs(limit)

    return [
        {
            "id": r.id,
            "run_id": r.run_id,
            "experiment_name": r.experiment_name,
            "benchmark_file": r.benchmark_file,
            "evaluators_used": r.evaluators_used,
            "total_answers": r.total_answers,
            "mae": r.mae,
            "rmse": r.rmse,
            "pearson_r": r.pearson_r,
            "spearman_r": r.spearman_r,
            "run_date": r.run_date.isoformat(),
        }
        for r in records
    ]
