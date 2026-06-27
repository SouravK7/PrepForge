"""
Benchmark and scientific validation framework.

This package measures how closely the AI evaluation ensemble
agrees with human expert scores on annotated benchmark answers.

Metrics computed:
    MAE:       Mean Absolute Error
    RMSE:      Root Mean Squared Error
    Pearson R: Linear correlation coefficient
    Spearman R: Rank correlation coefficient

Experiments:
    Ablation study measuring contribution of each evaluator.
    Error analysis identifying where and why the model fails.
"""

from benchmark.metrics import BenchmarkMetrics
from benchmark.run_benchmark import BenchmarkRunner
from benchmark.ablation_runner import AblationRunner
from benchmark.error_analysis import ErrorAnalyzer
from benchmark.report_writer import ReportWriter

__all__ = [
    "BenchmarkMetrics",
    "BenchmarkRunner",
    "AblationRunner",
    "ErrorAnalyzer",
    "ReportWriter",
]
