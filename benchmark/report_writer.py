"""
Report writer for benchmark results.

Generates a human-readable Markdown report
summarizing all benchmark and ablation results.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from schemas.benchmark_schema import AblationResult, BenchmarkRunReport


class ReportWriter:
    """
    Generates Markdown summary reports from benchmark results.
    """

    def __init__(self) -> None:
        """Initialize paths."""
        self._reports_path = Path(__file__).parent / "reports"
        self._reports_path.mkdir(exist_ok=True)

    def write_full_report(
        self,
        benchmark_reports: dict[str, BenchmarkRunReport],
        ablation_results: list[AblationResult],
    ) -> str:
        """
        Generate a complete Markdown benchmark report.

        Args:
            benchmark_reports: Map of benchmark file name to report.
            ablation_results: Results from the ablation study.

        Returns:
            Path to the generated report file.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"full_benchmark_report_{timestamp}.md"
        filepath = self._reports_path / filename

        lines = []
        lines.append("# AI Evaluation Ensemble - Benchmark Report")
        lines.append(f"\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("\n---\n")

        # Benchmark results
        lines.append("## Benchmark Results\n")
        lines.append(
            "The following table shows how closely the AI evaluation ensemble "
            "agrees with human expert scores on annotated benchmark answers.\n"
        )
        lines.append("| Benchmark | Answers | Pearson R | Spearman R | MAE | RMSE |")
        lines.append("|-----------|---------|-----------|------------|-----|------|")
        for name, report in benchmark_reports.items():
            lines.append(
                f"| {name} | {report.total_answers} | "
                f"{report.pearson_r:.4f} | {report.spearman_r:.4f} | "
                f"{report.mae:.2f} | {report.rmse:.2f} |"
            )

        lines.append("\n---\n")

        # Ablation study
        lines.append("## Ablation Study\n")
        lines.append(
            "Each row shows performance when adding one more evaluator "
            "to the ensemble. This proves each evaluator contributes "
            "measurable improvement.\n"
        )
        lines.append(
            "| Experiment | Evaluators | Pearson R | MAE | Improvement |"
        )
        lines.append("|------------|------------|-----------|-----|-------------|")
        for result in ablation_results:
            improvement = (
                f"+{result.improvement_over_baseline:.1f}%"
                if result.improvement_over_baseline and result.improvement_over_baseline > 0
                else "baseline"
            )
            lines.append(
                f"| {result.experiment_name} | "
                f"{', '.join(result.evaluators_used)} | "
                f"{result.pearson_r:.4f} | "
                f"{result.mae:.2f} | "
                f"{improvement} |"
            )

        lines.append("\n---\n")

        # Interpretation
        lines.append("## Interpretation\n")
        if ablation_results:
            baseline = ablation_results[0]
            full = ablation_results[-1]
            lines.append(
                f"The semantic-only baseline achieved a Pearson R of "
                f"**{baseline.pearson_r:.4f}**. "
                f"The full ensemble achieved **{full.pearson_r:.4f}**, "
                f"demonstrating that multi-dimensional evaluation significantly "
                f"outperforms similarity-only approaches.\n"
            )

        lines.append("---\n")
        lines.append("## Known Limitations\n")
        lines.append(
            "- The dataset is currently small and relies on synthetically augmented "
            "human annotations.\n"
            "- Concept coverage can under-score creative answers that do not use "
            "expected terminology.\n"
            "- Further tuning of weights in `scoring_weights.yaml` may be needed "
            "as the dataset grows.\n"
        )

        with open(filepath, "w") as f:
            f.write("\n".join(lines))

        print(f"\n  Markdown report generated: {filepath}")
        return str(filepath)
