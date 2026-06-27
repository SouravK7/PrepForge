"""
Error analysis module.

After benchmarking, analyzes where and why the evaluator
makes the largest errors. This produces the most honest
and scientifically credible section of the final report.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from schemas.benchmark_schema import BenchmarkResult, BenchmarkRunReport, ErrorAnalysisEntry


class ErrorAnalyzer:
    """
    Analyzes errors in benchmark results.

    Identifies systematic patterns in evaluator errors:
    which answer types, question types, and score ranges
    produce the largest errors.
    """

    OVER_SCORED_THRESHOLD = 10.0
    UNDER_SCORED_THRESHOLD = 10.0

    def __init__(self) -> None:
        """Initialize paths."""
        self._reports_path = Path(__file__).parent / "reports"
        self._reports_path.mkdir(exist_ok=True)

    def analyze(
        self,
        report: BenchmarkRunReport,
        save: bool = True,
    ) -> list[ErrorAnalysisEntry]:
        """
        Analyze errors in a benchmark run report.

        Args:
            report: Completed benchmark run report.
            save: Whether to save analysis to disk.

        Returns:
            List of ErrorAnalysisEntry for each result.
        """
        entries: list[ErrorAnalysisEntry] = []

        for result in report.results:
            error = result.ai_score - result.human_score
            abs_error = abs(error)

            if error > self.OVER_SCORED_THRESHOLD:
                category = "over_scored"
                likely_cause = self._diagnose_over_scoring(result)
            elif error < -self.UNDER_SCORED_THRESHOLD:
                category = "under_scored"
                likely_cause = self._diagnose_under_scoring(result)
            else:
                category = "accurate"
                likely_cause = "Score within acceptable range"

            entry = ErrorAnalysisEntry(
                question_id=result.question_id,
                answer_type=result.answer_type,
                human_score=result.human_score,
                ai_score=result.ai_score,
                error=round(error, 2),
                absolute_error=round(abs_error, 2),
                error_category=category,
                likely_cause=likely_cause,
            )
            entries.append(entry)

        self._print_analysis(entries, report)

        if save:
            self._save_analysis(entries, report.run_id)

        return entries

    def _diagnose_over_scoring(self, result: BenchmarkResult) -> str:
        """
        Diagnose why the AI over-scored an answer.

        Args:
            result: A single benchmark result with AI > human score.

        Returns:
            Hypothesis about the cause of over-scoring.
        """
        dim = result.dimension_scores

        if dim.get("semantic", 0) > 70 and dim.get("concept", 0) < 50:
            return (
                "High semantic similarity but low concept coverage. "
                "Embedding similarity may reward fluent but incomplete answers."
            )

        if dim.get("communication", 0) > 80:
            return (
                "High communication score inflating total. "
                "Well-written but superficial answers may over-score."
            )

        if result.answer_type == "poor":
            return (
                "Poor answer over-scored. "
                "Short but fluent responses may score higher than expected "
                "on semantic and communication dimensions."
            )

        return "Over-scoring cause unclear. May reflect edge case in weighting."

    def _diagnose_under_scoring(self, result: BenchmarkResult) -> str:
        """
        Diagnose why the AI under-scored an answer.

        Args:
            result: A single benchmark result with AI < human score.

        Returns:
            Hypothesis about the cause of under-scoring.
        """
        dim = result.dimension_scores

        if dim.get("concept", 0) < 60 and result.human_score > 70:
            return (
                "Low concept coverage score despite good human rating. "
                "Answer may use synonyms or alternative terminology "
                "not in the required concepts list. Ontology may need expansion."
            )

        if dim.get("evidence", 0) < 40 and result.human_score > 75:
            return (
                "Evidence evaluator penalizing answer that human rated highly. "
                "May contain implicit evidence not detected by signal phrases."
            )

        if result.answer_type == "excellent":
            return (
                "Excellent answer under-scored. "
                "Creative or unconventional excellent answers may use "
                "different terminology than the concept list expects."
            )

        return "Under-scoring cause unclear. May reflect missing synonym handling."

    def _print_analysis(
        self,
        entries: list[ErrorAnalysisEntry],
        report: BenchmarkRunReport,
    ) -> None:
        """Print formatted error analysis to console."""
        over_scored = [e for e in entries if e.error_category == "over_scored"]
        under_scored = [e for e in entries if e.error_category == "under_scored"]
        accurate = [e for e in entries if e.error_category == "accurate"]

        print("\n" + "=" * 65)
        print(f"  ERROR ANALYSIS: Run {report.run_id}")
        print("=" * 65)
        print(f"  Total answers:   {len(entries)}")
        print(f"  Accurate:        {len(accurate)} ({100 * len(accurate)/len(entries):.1f}%)")
        print(f"  Over-scored:     {len(over_scored)} ({100 * len(over_scored)/len(entries):.1f}%)")
        print(f"  Under-scored:    {len(under_scored)} ({100 * len(under_scored)/len(entries):.1f}%)")

        # Errors by answer type
        print("\n  Errors by answer type:")
        for answer_type in ["poor", "below_average", "average", "good", "excellent"]:
            type_entries = [e for e in entries if e.answer_type == answer_type]
            if type_entries:
                avg_error = sum(e.absolute_error for e in type_entries) / len(type_entries)
                avg_human = sum(e.human_score for e in type_entries) / len(type_entries)
                avg_ai = sum(e.ai_score for e in type_entries) / len(type_entries)
                print(
                    f"  {answer_type:<15} | "
                    f"Avg Human: {avg_human:5.1f} | "
                    f"Avg AI: {avg_ai:5.1f} | "
                    f"Avg Error: {avg_error:5.1f}"
                )

        # Largest errors
        sorted_entries = sorted(entries, key=lambda e: e.absolute_error, reverse=True)
        if sorted_entries:
            print("\n  Largest errors:")
            for entry in sorted_entries[:3]:
                print(
                    f"  [{entry.error_category}] {entry.question_id} | "
                    f"{entry.answer_type} | "
                    f"Human: {entry.human_score:.1f} | "
                    f"AI: {entry.ai_score:.1f} | "
                    f"Error: {entry.absolute_error:.1f}"
                )
                print(f"    Cause: {entry.likely_cause}")

        print("=" * 65)

    def _save_analysis(
        self,
        entries: list[ErrorAnalysisEntry],
        run_id: str,
    ) -> None:
        """Save error analysis to disk."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"error_analysis_{run_id}_{timestamp}.json"
        filepath = self._reports_path / filename

        data = {
            "run_id": run_id,
            "analyzed_at": datetime.utcnow().isoformat(),
            "entries": [
                {
                    "question_id": e.question_id,
                    "answer_type": e.answer_type,
                    "human_score": e.human_score,
                    "ai_score": e.ai_score,
                    "error": e.error,
                    "absolute_error": e.absolute_error,
                    "error_category": e.error_category,
                    "likely_cause": e.likely_cause,
                }
                for e in entries
            ],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n  Error analysis saved: {filepath}")
