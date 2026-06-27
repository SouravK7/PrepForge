"""
Main benchmark runner.

Loads benchmark dataset, runs the evaluation ensemble
on each answer, compares AI scores to human scores,
and generates a complete benchmark report.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ai_core.evaluation_pipeline import EvaluationOrchestrator
from ai_core.shared.config_loader import config
from benchmark.metrics import BenchmarkMetrics
from schemas.answer_schema import AnswerInput
from schemas.benchmark_schema import (
    BenchmarkAnswer,
    BenchmarkQuestion,
    BenchmarkResult,
    BenchmarkRunReport,
)
from schemas.question_schema import QuestionType


class BenchmarkRunner:
    """
    Runs the evaluation ensemble against benchmark datasets.

    Loads human-annotated benchmark answers, evaluates them
    with the AI ensemble, and computes agreement metrics.
    """

    def __init__(self) -> None:
        """Initialize orchestrator and paths."""
        self._orchestrator = EvaluationOrchestrator()
        self._data_path = (
            Path(__file__).parent.parent / "data" / "benchmark"
        )
        self._reports_path = Path(__file__).parent / "reports"
        self._reports_path.mkdir(exist_ok=True)

    def run(
        self,
        benchmark_file: str,
        experiment_name: str = "full_ensemble",
        save_report: bool = True,
    ) -> BenchmarkRunReport:
        """
        Run benchmark on one benchmark file.

        Args:
            benchmark_file: Name of benchmark JSON file without extension.
                           e.g. "oop_benchmark_v1"
            experiment_name: Name for this run.
            save_report: Whether to save results to disk.

        Returns:
            BenchmarkRunReport with all metrics and per-answer results.

        Raises:
            FileNotFoundError: If benchmark file not found.
        """
        benchmark_path = self._data_path / f"{benchmark_file}.json"
        if not benchmark_path.exists():
            raise FileNotFoundError(f"Benchmark file not found: {benchmark_path}")

        with open(benchmark_path, "r") as f:
            raw_data = json.load(f)

        run_id = str(uuid.uuid4())[:8]
        print(f"\nRunning benchmark: {benchmark_file}")
        print(f"Experiment: {experiment_name}")
        print(f"Run ID: {run_id}")
        print("-" * 50)

        results: list[BenchmarkResult] = []
        human_scores: list[float] = []
        ai_scores: list[float] = []

        question_id = raw_data["question_id"]
        question_text = raw_data["question_text"]
        required_concepts = raw_data["required_concepts"]
        competency_id = raw_data.get("competency_id", "comp_unknown")

        print(f"\nQuestion: {question_text[:60]}...")

        for answer_data in raw_data["answers"]:
            answer_type = answer_data["answer_type"]
            answer_text = answer_data.get("text", answer_data.get("answer_text", ""))
            human_score = answer_data["human_score"]

            # Determine question type from data or default to technical
            q_type_str = raw_data.get("question_type", "technical")
            q_type = (
                QuestionType.HR
                if q_type_str == "hr" or "hr_benchmark" in benchmark_file
                else QuestionType.TECHNICAL
            )

            # Build answer input for evaluator
            answer_input = AnswerInput(
                session_id=0,
                user_id=0,
                question_id=question_id,
                competency_id=competency_id,
                question_text=question_text,
                question_type=q_type,
                sample_answer=self._get_sample_answer(raw_data),
                required_concepts=required_concepts,
                optional_concepts=[],
                rubric_id=(
                    "rubric_hr_standard"
                    if q_type == QuestionType.HR
                    else "rubric_technical_standard"
                ),
                user_answer=answer_text,
            )

            # Run evaluation
            try:
                evaluation = self._orchestrator.evaluate(answer_input)
                ai_score = evaluation.scores.weighted_final

                result = BenchmarkResult(
                    question_id=question_id,
                    answer_type=answer_type,
                    human_score=human_score,
                    ai_score=round(ai_score, 2),
                    absolute_error=round(abs(ai_score - human_score), 2),
                    squared_error=round((ai_score - human_score) ** 2, 4),
                    dimension_scores={
                        "semantic": evaluation.scores.semantic,
                        "concept": evaluation.scores.concept,
                        "communication": evaluation.scores.communication,
                        "evidence": evaluation.scores.evidence,
                        "reasoning": evaluation.scores.reasoning,
                    },
                )

                results.append(result)
                human_scores.append(human_score)
                ai_scores.append(ai_score)

                status = "[OK]" if result.absolute_error <= 15 else "[FAIL]"
                print(
                    f"  {status} {answer_type:12s} | "
                    f"Human: {human_score:5.1f} | "
                    f"AI: {ai_score:5.1f} | "
                    f"Error: {result.absolute_error:5.1f}"
                )

            except Exception as e:
                print(f"  [!] Failed to evaluate {answer_type}: {e}")

        # Compute metrics
        metrics = BenchmarkMetrics.all_metrics(human_scores, ai_scores)

        report = BenchmarkRunReport(
            run_id=run_id,
            experiment_name=experiment_name,
            evaluators_used=[
                "SemanticEvaluator",
                "ConceptEvaluator",
                "CommunicationEvaluator",
                "EvidenceEvaluator",
                "ReasoningEvaluator",
            ],
            total_answers=len(results),
            mae=metrics["mae"],
            rmse=metrics["rmse"],
            pearson_r=metrics["pearson_r"],
            spearman_r=metrics["spearman_r"],
            results=results,
            notes=f"Benchmark file: {benchmark_file}",
        )

        self._print_report_summary(report, metrics)

        if save_report:
            self._save_report(report, benchmark_file, experiment_name)

        return report

    def run_all(self, save_reports: bool = True) -> dict[str, BenchmarkRunReport]:
        """
        Run benchmark on all available benchmark files.

        Args:
            save_reports: Whether to save reports to disk.

        Returns:
            Dictionary of benchmark_file_name to BenchmarkRunReport.
        """
        benchmark_files = [
            "oop_benchmark_v1",
            "sql_benchmark_v1",
            "hr_benchmark_v1",
        ]

        reports = {}
        for benchmark_file in benchmark_files:
            try:
                report = self.run(
                    benchmark_file=benchmark_file,
                    experiment_name="full_ensemble",
                    save_report=save_reports,
                )
                reports[benchmark_file] = report
            except FileNotFoundError as e:
                print(f"Skipping {benchmark_file}: {e}")

        self._print_combined_summary(reports)
        return reports

    def _get_sample_answer(self, question_data: dict) -> str:
        """
        Extract or construct sample answer from question data.

        Uses the excellent-type answer as the sample if
        no explicit sample answer is stored.

        Args:
            question_data: Raw question dictionary from benchmark JSON.

        Returns:
            Sample answer string.
        """
        # Use explicit sample answer if available
        if "sample_answer" in question_data:
            return question_data["sample_answer"]

        # Fall back to excellent answer
        for answer in question_data.get("answers", []):
            if answer["answer_type"] == "excellent":
                return answer["text"]

        # Fall back to good answer
        for answer in question_data.get("answers", []):
            if answer["answer_type"] == "good":
                return answer["text"]

        return "No sample answer available."

    def _print_report_summary(
        self,
        report: BenchmarkRunReport,
        metrics: dict[str, float],
    ) -> None:
        """Print formatted benchmark results to console."""
        print("\n" + "=" * 50)
        print(f"  BENCHMARK RESULTS: {report.experiment_name}")
        print("=" * 50)
        print(f"  Total Answers Evaluated:  {report.total_answers}")
        print(f"  MAE:                      {report.mae:.2f}")
        print(f"  RMSE:                     {report.rmse:.2f}")
        print(f"  Pearson R:                {report.pearson_r:.4f}")
        print(f"  Spearman R:               {report.spearman_r:.4f}")
        print(f"  Pearson p-value:          {metrics['pearson_p']:.6f}")

        # Check against success criteria
        target_pearson = config.get_float(
            "success_criteria", "evaluator.full_ensemble_pearson_r", 0.85
        )
        target_mae = config.get_float(
            "success_criteria", "evaluator.full_ensemble_mae", 12.0
        )

        pearson_status = "[PASS]" if report.pearson_r >= target_pearson else "[BELOW TARGET]"
        mae_status = "[PASS]" if report.mae <= target_mae else "[ABOVE TARGET]"

        print(f"\n  Pearson R target ({target_pearson}): {pearson_status}")
        print(f"  MAE target ({target_mae}):        {mae_status}")
        print("=" * 50)

    def _print_combined_summary(
        self,
        reports: dict[str, BenchmarkRunReport],
    ) -> None:
        """Print summary across all benchmark runs."""
        if not reports:
            return

        all_pearson = [r.pearson_r for r in reports.values()]
        all_mae = [r.mae for r in reports.values()]

        print("\n" + "=" * 60)
        print("  COMBINED BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"  {'Benchmark':<30} {'Pearson R':>10} {'MAE':>8}")
        print("-" * 60)
        for name, report in reports.items():
            print(
                f"  {name:<30} {report.pearson_r:>10.4f} {report.mae:>8.2f}"
            )
        print("-" * 60)
        print(
            f"  {'AVERAGE':<30} "
            f"{sum(all_pearson)/len(all_pearson):>10.4f} "
            f"{sum(all_mae)/len(all_mae):>8.2f}"
        )
        print("=" * 60)

    def _save_report(
        self,
        report: BenchmarkRunReport,
        benchmark_file: str,
        experiment_name: str,
    ) -> None:
        """
        Save benchmark report to disk as JSON.

        Args:
            report: Completed benchmark run report.
            benchmark_file: Source benchmark file name.
            experiment_name: Experiment identifier.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{benchmark_file}_{experiment_name}_{timestamp}.json"
        filepath = self._reports_path / filename

        report_dict = {
            "run_id": report.run_id,
            "experiment_name": report.experiment_name,
            "evaluators_used": report.evaluators_used,
            "total_answers": report.total_answers,
            "mae": report.mae,
            "rmse": report.rmse,
            "pearson_r": report.pearson_r,
            "spearman_r": report.spearman_r,
            "run_at": report.run_at.isoformat(),
            "results": [
                {
                    "question_id": r.question_id,
                    "answer_type": r.answer_type,
                    "human_score": r.human_score,
                    "ai_score": r.ai_score,
                    "absolute_error": r.absolute_error,
                    "dimension_scores": r.dimension_scores,
                }
                for r in report.results
            ],
        }

        with open(filepath, "w") as f:
            json.dump(report_dict, f, indent=2)

        print(f"\n  Report saved: {filepath}")
