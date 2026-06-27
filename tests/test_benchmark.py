"""
Tests for benchmark validation metrics and runners.
"""

import pytest

from benchmark.metrics import BenchmarkMetrics


def test_mae_calculation():
    """Test Mean Absolute Error calculation."""
    human = [80.0, 60.0, 90.0]
    ai = [85.0, 50.0, 90.0]
    # |85-80| + |50-60| + |90-90| = 5 + 10 + 0 = 15 / 3 = 5.0
    mae = BenchmarkMetrics.mae(human, ai)
    assert mae == 5.0


def test_rmse_calculation():
    """Test Root Mean Squared Error calculation."""
    human = [80.0, 60.0, 90.0]
    ai = [85.0, 50.0, 90.0]
    # (5)^2 + (-10)^2 + (0)^2 = 25 + 100 + 0 = 125 / 3 = 41.666...
    # sqrt(41.666...) ≈ 6.455
    rmse = BenchmarkMetrics.rmse(human, ai)
    assert abs(rmse - 6.455) < 0.01


def test_validation_errors():
    """Test that metrics raise ValueError on invalid inputs."""
    with pytest.raises(ValueError):
        BenchmarkMetrics.mae([], [])

    with pytest.raises(ValueError):
        BenchmarkMetrics.mae([1.0, 2.0], [1.0])

    with pytest.raises(ValueError):
        # Needs at least 2 samples for metrics like pearson
        BenchmarkMetrics.pearson_r([1.0], [1.0])
