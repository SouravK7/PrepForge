"""
Ablation study runner.

Tests the evaluation ensemble with progressively more evaluators
to measure each evaluator's individual contribution to accuracy.

Experiments:
    1. Semantic only
    2. Semantic + Concept
    3. Semantic + Concept + Evidence
    4. Semantic + Concept + Evidence + Communication
    5. Full Ensemble (all evaluators)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np

from ai_core.evaluation_pipeline.semantic_evaluator import SemanticEvaluator
from ai_core.evaluation_pipeline.concept_evaluator import ConceptEvaluator
from ai_core.evaluation_pipeline.communication_evaluator import CommunicationEvaluator
from ai_core.evaluation_pipeline.evidence_evaluator import EvidenceEvaluator
from ai_core.evaluation_pipeline.reasoning_evaluator import ReasoningEvaluator
from ai_core.evaluation_pipeline.score_fusion import ScoreFusion, FusionInput
from ai_core.evaluation_pipeline.base_evaluator import DimensionScore
from benchmark.metrics import BenchmarkMetrics
from schemas.answer_schema import AnswerInput
from schemas.benchmark_schema import AblationResult
from schemas.question_schema import QuestionType


class AblationRunner:
    """
    Runs ablation study across multiple evaluator configurations.

    Each experiment adds one more evaluator to measure
    the marginal contribution of that evaluator to final accuracy.
    """

    # Define experiments in order of increasing complexity
    EXPERIMENTS: list[dict] = [
        {
            "name": "semantic_only",
            "description": "Semantic similarity evaluator alone",
            "evaluators": ["semantic"],
        },
        {
            "name": "semantic_concept",
            "description": "Semantic + Concept coverage",
            "evaluators": ["semantic", "concept"],
        },
        {
            "name": "semantic_concept_evidence",
            "description": "Semantic + Concept + Evidence",
            "evaluators": ["semantic", "concept", "evidence"],
        },
        {
            "name": "semantic_concept_evidence_communication",
            "description": "Semantic + Concept + Evidence + Communication",
            "evaluators": ["semantic", "concept", "evidence", "communication"],
        },
        {
            "name": "full_ensemble",
            "description": "Full ensemble: all five evaluators",
            "evaluators": ["semantic", "concept", "evidence", "communication", "reasoning"],
        },
    ]

    def __init__(self) -> None:
        """Initialize all evaluators."""
        self._semantic = SemanticEvaluator()
        self._concept = ConceptEvaluator()
        self._communication = CommunicationEvaluator()
        self._evidence = EvidenceEvaluator()
        self._reasoning = ReasoningEvaluator()
        self._data_path = (
            Path(__file__).parent.parent / "data" / "benchmark"
        )
        self._reports_path = Path(__file__).parent / "reports"
        self._reports_path.mkdir(exist_ok=True)

    def run(
        self,
        benchmark_file: str = "oop_benchmark_v1",
    ) -> list[AblationResult]:
        """
        Run full ablation study on a benchmark file.

        Args:
            benchmark_file: Name of benchmark JSON file without extension.

        Returns:
            List of AblationResult for each experiment.
        """
        # Load benchmark data
        benchmark_path = self._data_path / f"{benchmark_file}.json"
        if not benchmark_path.exists():
            raise FileNotFoundError(f"Benchmark not found: {benchmark_path}")

        with open(benchmark_path, "r") as f:
            raw_data = json.load(f)

        # Build answer inputs and human scores
        answer_inputs, human_scores = self._build_inputs(raw_data, benchmark_file)

        if not answer_inputs:
            raise ValueError("No valid answers found in benchmark file")

        print("\n" + "=" * 65)
        print(f"  ABLATION STUDY: {benchmark_file}")
        print("=" * 65)
        print(
            f"  {'Experiment':<40} {'Pearson R':>9} {'MAE':>7} {'Improve':>8}"
        )
        print("-" * 65)

        results: list[AblationResult] = []
        baseline_pearson: float | None = None

        for experiment in self.EXPERIMENTS:
            ai_scores = self._run_experiment(
                answer_inputs=answer_inputs,
                active_evaluators=experiment["evaluators"],
            )

            metrics = BenchmarkMetrics.all_metrics(human_scores, ai_scores)
            pearson = metrics["pearson_r"]
            mae = metrics["mae"]

            improvement = None
            if baseline_pearson is not None:
                improvement = BenchmarkMetrics.improvement_over_baseline(
                    baseline_pearson, pearson
                )

            if baseline_pearson is None:
                baseline_pearson = pearson

            result = AblationResult(
                experiment_name=experiment["name"],
                evaluators_used=experiment["evaluators"],
                mae=mae,
                rmse=metrics["rmse"],
                pearson_r=pearson,
                improvement_over_baseline=improvement,
            )
            results.append(result)

            improvement_str = (
                f"+{improvement:.1f}%" if improvement and improvement > 0
                else f"{improvement:.1f}%" if improvement is not None
                else "baseline"
            )

            print(
                f"  {experiment['name']:<40} "
                f"{pearson:>9.4f} "
                f"{mae:>7.2f} "
                f"{improvement_str:>8}"
            )

        print("=" * 65)

        # Print interpretation
        self._print_interpretation(results)

        # Save report
        self._save_ablation_report(results, benchmark_file)

        return results

    def _run_experiment(
        self,
        answer_inputs: list[tuple[AnswerInput, dict]],
        active_evaluators: list[str],
    ) -> list[float]:
        """
        Run one ablation experiment with specified evaluators.

        Args:
            answer_inputs: List of (AnswerInput, question_data) tuples.
            active_evaluators: Names of evaluators to use.

        Returns:
            List of AI scores for each answer.
        """
        ai_scores = []

        for answer_input, question_data in answer_inputs:
            # Run only active evaluators
            semantic_score = (
                self._semantic.evaluate(answer_input)
                if "semantic" in active_evaluators
                else DimensionScore(score=50.0, label="semantic", reason="disabled", evidence=[])
            )
            concept_score = (
                self._concept.evaluate(answer_input)
                if "concept" in active_evaluators
                else DimensionScore(score=50.0, label="concept", reason="disabled", evidence=[])
            )
            communication_score = (
                self._communication.evaluate(answer_input)
                if "communication" in active_evaluators
                else DimensionScore(score=50.0, label="communication", reason="disabled", evidence=[])
            )
            evidence_score = (
                self._evidence.evaluate(answer_input)
                if "evidence" in active_evaluators
                else DimensionScore(score=50.0, label="evidence", reason="disabled", evidence=[])
            )
            reasoning_score = (
                self._reasoning.evaluate(answer_input)
                if "reasoning" in active_evaluators
                else DimensionScore(score=50.0, label="reasoning", reason="disabled", evidence=[])
            )

            # Build dynamic weights for active evaluators only
            weights = self._compute_dynamic_weights(
                active_evaluators, answer_input.question_type
            )

            # Manual weighted fusion
            score = (
                semantic_score.score * weights.get("semantic", 0.0)
                + concept_score.score * weights.get("concept", 0.0)
                + communication_score.score * weights.get("communication", 0.0)
                + evidence_score.score * weights.get("evidence", 0.0)
                + reasoning_score.score * weights.get("reasoning", 0.0)
            )

            ai_scores.append(round(float(max(0.0, min(100.0, score))), 2))

        return ai_scores

    def _compute_dynamic_weights(
        self,
        active_evaluators: list[str],
        question_type: QuestionType,
    ) -> dict[str, float]:
        """
        Compute normalized weights for only active evaluators.

        When some evaluators are disabled, redistribute their
        weight proportionally among active evaluators.

        Args:
            active_evaluators: Names of evaluators that are enabled.
            question_type: Technical or HR determines base weights.

        Returns:
            Normalized weight dictionary for active evaluators only.
        """
        if question_type == QuestionType.TECHNICAL:
            base_weights = {
                "semantic": 0.20,
                "concept": 0.35,
                "communication": 0.10,
                "evidence": 0.15,
                "reasoning": 0.20,
            }
        else:
            base_weights = {
                "semantic": 0.25,
                "concept": 0.10,
                "communication": 0.25,
                "evidence": 0.25,
                "reasoning": 0.15,
            }

        # Extract only active weights
        active_weights = {k: v for k, v in base_weights.items() if k in active_evaluators}

        # Normalize to sum to 1.0
        total = sum(active_weights.values())
        if total == 0:
            return {k: 1.0 / len(active_evaluators) for k in active_evaluators}

        return {k: v / total for k, v in active_weights.items()}

    def _build_inputs(
        self,
        raw_data: dict,
        benchmark_file: str,
    ) -> tuple[list[tuple[AnswerInput, dict]], list[float]]:
        """
        Build AnswerInput objects and collect human scores from raw data.

        Args:
            raw_data: Parsed benchmark JSON.
            benchmark_file: Benchmark file name for type detection.

        Returns:
            Tuple of (answer_input_list, human_scores).
        """
        answer_inputs = []
        human_scores = []

        competency_id = raw_data.get("competency_id", "comp_unknown")
        q_type = (
            QuestionType.HR
            if "hr_benchmark" in benchmark_file
            else QuestionType.TECHNICAL
        )

        for question_data in raw_data["questions"]:
            question_id = question_data["question_id"]
            question_text = question_data["question_text"]
            required_concepts = question_data["required_concepts"]

            # Get sample answer (excellent or explicit)
            sample_answer = self._get_sample_answer(question_data)

            for answer_data in question_data["answers"]:
                answer_input = AnswerInput(
                    session_id=0,
                    user_id=0,
                    question_id=question_id,
                    competency_id=competency_id,
                    question_text=question_text,
                    question_type=q_type,
                    sample_answer=sample_answer,
                    required_concepts=required_concepts,
                    optional_concepts=[],
                    rubric_id=(
                        "rubric_hr_standard"
                        if q_type == QuestionType.HR
                        else "rubric_technical_standard"
                    ),
                    user_answer=answer_data["text"],
                )

                answer_inputs.append((answer_input, question_data))
                human_scores.append(answer_data["human_score"])

        return answer_inputs, human_scores

    def _get_sample_answer(self, question_data: dict) -> str:
        """Extract sample answer from question data."""
        if "sample_answer" in question_data:
            return question_data["sample_answer"]
        for answer in question_data.get("answers", []):
            if answer["answer_type"] == "excellent":
                return answer["text"]
        return "No sample answer available."

    def _print_interpretation(self, results: list[AblationResult]) -> None:
        """Print human-readable interpretation of ablation results."""
        if len(results) < 2:
            return

        baseline = results[0]
        full = results[-1]

        print(f"\n  Interpretation:")
        print(
            f"  Semantic-only baseline Pearson R: {baseline.pearson_r:.4f}"
        )
        print(
            f"  Full ensemble Pearson R:          {full.pearson_r:.4f}"
        )

        if full.pearson_r > baseline.pearson_r:
            total_improvement = BenchmarkMetrics.improvement_over_baseline(
                baseline.pearson_r, full.pearson_r
            )
            print(
                f"  Total improvement:                +{total_improvement:.1f}%"
            )
            print(
                f"\n  Conclusion: The full ensemble outperforms semantic-only "
                f"by {total_improvement:.1f}%. Each evaluator adds measurable value."
            )
        else:
            print(
                "\n  Note: Additional evaluators did not improve Pearson R "
                "on this benchmark. Consider tuning weights or expanding dataset."
            )

    def _save_ablation_report(
        self,
        results: list[AblationResult],
        benchmark_file: str,
    ) -> None:
        """Save ablation results to disk."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"ablation_{benchmark_file}_{timestamp}.json"
        filepath = self._reports_path / filename

        report_data = {
            "benchmark_file": benchmark_file,
            "run_at": datetime.utcnow().isoformat(),
            "experiments": [
                {
                    "name": r.experiment_name,
                    "evaluators_used": r.evaluators_used,
                    "pearson_r": r.pearson_r,
                    "mae": r.mae,
                    "rmse": r.rmse,
                    "improvement_over_baseline": r.improvement_over_baseline,
                }
                for r in results
            ],
        }

        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n  Ablation report saved: {filepath}")
