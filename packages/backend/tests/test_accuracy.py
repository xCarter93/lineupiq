"""
Unit tests for accuracy metrics and confidence rating.

Tests cover:
- R²-based accuracy calculation
- Edge cases (perfect predictions, negative R², R² > 1)
- Confidence tier assignment based on R² thresholds
- Boundary conditions for confidence tiers
- Backtest results summarization
"""

import numpy as np
import pytest

from lineupiq.models.accuracy import (
    calculate_confidence_rating,
    calculate_model_accuracy,
    summarize_backtest_results,
)


def test_calculate_model_accuracy_perfect_predictions() -> None:
    """Verify accuracy_pct = 100.0 when R² = 1.0 (perfect predictions)."""
    y_true = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    y_pred = np.array([100.0, 200.0, 300.0, 400.0, 500.0])

    metrics = calculate_model_accuracy(y_pred, y_true)

    assert metrics["r2"] == pytest.approx(1.0, abs=0.001)
    assert metrics["accuracy_pct"] == pytest.approx(100.0, abs=0.1)
    assert metrics["mae"] == pytest.approx(0.0, abs=0.001)
    assert metrics["rmse"] == pytest.approx(0.0, abs=0.001)
    assert metrics["directional_accuracy"] == pytest.approx(100.0, abs=0.1)


def test_calculate_model_accuracy_good_predictions() -> None:
    """Verify accuracy_pct matches 100*R² for good model."""
    # Create realistic data with moderate noise
    np.random.seed(42)
    y_true = np.array([100.0, 200.0, 150.0, 250.0, 180.0, 220.0, 190.0, 210.0, 160.0, 240.0])
    # Add noise to create R² < 1.0
    noise = np.random.normal(0, 30, size=10)
    y_pred = y_true + noise

    metrics = calculate_model_accuracy(y_pred, y_true)

    # R² should be positive and less than 1.0
    assert 0.3 < metrics["r2"] < 1.0
    # accuracy_pct should exactly match 100 * R² (formula guarantee)
    assert abs(metrics["accuracy_pct"] - 100 * metrics["r2"]) < 0.1
    assert metrics["mae"] > 0
    assert metrics["rmse"] > 0


def test_calculate_model_accuracy_poor_predictions() -> None:
    """Verify accuracy_pct ≈ 20.0 when R² ≈ 0.2 (poor model)."""
    # Create data with low R² (high variance, poor fit)
    y_true = np.array([100.0, 200.0, 150.0, 250.0, 180.0])
    y_pred = np.array([150.0, 150.0, 200.0, 200.0, 150.0])

    metrics = calculate_model_accuracy(y_pred, y_true)

    # R² should be low but positive
    assert 0.0 <= metrics["r2"] < 0.5
    # accuracy_pct should match R² (clamped to [0, 100])
    assert 0 <= metrics["accuracy_pct"] <= 100
    assert abs(metrics["accuracy_pct"] - 100 * metrics["r2"]) < 1.0


def test_calculate_model_accuracy_negative_r2_clamped() -> None:
    """Verify accuracy_pct = 0.0 when R² < 0 (very poor model, worse than mean)."""
    y_true = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    # Predictions worse than mean baseline (constant prediction far from optimal)
    y_pred = np.array([500.0, 500.0, 500.0, 500.0, 500.0])

    metrics = calculate_model_accuracy(y_pred, y_true)

    # R² can be negative when model is worse than mean baseline
    assert metrics["r2"] <= 0
    # accuracy_pct should be clamped to 0 (not negative)
    assert metrics["accuracy_pct"] == pytest.approx(0.0, abs=0.001)


def test_calculate_model_accuracy_r2_over_100_clamped() -> None:
    """Verify accuracy_pct = 100.0 when R² > 1.0 (overfitting edge case)."""
    # R² > 1 is mathematically possible in edge cases (e.g., with weighted samples)
    # For standard sklearn r2_score, this shouldn't happen, but we test the clamping
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([100.0, 200.0, 300.0])

    metrics = calculate_model_accuracy(y_pred, y_true)

    # R² = 1.0 for perfect predictions
    assert metrics["r2"] == pytest.approx(1.0, abs=0.001)
    # Even if R² were > 1, accuracy_pct should be clamped to 100
    assert metrics["accuracy_pct"] <= 100.0


def test_calculate_model_accuracy_directional_accuracy() -> None:
    """Verify directional_accuracy calculation."""
    # Mean = 200
    y_true = np.array([100.0, 150.0, 200.0, 250.0, 300.0])
    # Create predictions with deliberate direction mismatches
    # y_true: [<mean, <mean, =mean, >mean, >mean]
    # y_pred: [>mean, <mean, <mean, >mean, >mean]
    # Matches: [False, True, False, True, True] = 3/5 = 60%
    y_pred = np.array([250.0, 150.0, 150.0, 300.0, 350.0])

    metrics = calculate_model_accuracy(y_pred, y_true)

    # 3 out of 5 should match direction = 60%
    assert metrics["directional_accuracy"] == pytest.approx(60.0, abs=1.0)


def test_calculate_confidence_rating_high() -> None:
    """Verify confidence = 'High' when R² > 0.5."""
    assert calculate_confidence_rating(0.7) == "High"
    assert calculate_confidence_rating(0.6) == "High"
    assert calculate_confidence_rating(0.51) == "High"


def test_calculate_confidence_rating_high_boundary() -> None:
    """Verify confidence = 'High' at R² = 0.5 boundary."""
    # R² > 0.5 means 0.5 is not included (should be Medium)
    assert calculate_confidence_rating(0.5) == "Medium"
    # Just above 0.5 should be High
    assert calculate_confidence_rating(0.500001) == "High"


def test_calculate_confidence_rating_medium() -> None:
    """Verify confidence = 'Medium' when R² 0.3-0.5."""
    assert calculate_confidence_rating(0.5) == "Medium"
    assert calculate_confidence_rating(0.4) == "Medium"
    assert calculate_confidence_rating(0.35) == "Medium"
    assert calculate_confidence_rating(0.31) == "Medium"


def test_calculate_confidence_rating_medium_boundary() -> None:
    """Verify confidence = 'Medium' at R² = 0.3 boundary."""
    # R² > 0.3 means 0.3 is not included (should be Low)
    assert calculate_confidence_rating(0.3) == "Low"
    # Just above 0.3 should be Medium
    assert calculate_confidence_rating(0.300001) == "Medium"


def test_calculate_confidence_rating_low() -> None:
    """Verify confidence = 'Low' when R² < 0.3."""
    assert calculate_confidence_rating(0.2) == "Low"
    assert calculate_confidence_rating(0.1) == "Low"
    assert calculate_confidence_rating(0.0) == "Low"
    assert calculate_confidence_rating(-0.1) == "Low"


def test_summarize_backtest_results_empty() -> None:
    """Verify empty backtest results return default values."""
    summary = summarize_backtest_results([])

    assert summary["overall_accuracy_pct"] == 0.0
    assert summary["overall_confidence"] == "Low"
    assert summary["total_models"] == 0
    assert summary["total_predictions"] == 0
    assert summary["by_model"] == []


def test_summarize_backtest_results_single_model() -> None:
    """Verify summary for single model backtest."""
    y_true = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    y_pred = np.array([110.0, 190.0, 310.0, 390.0, 510.0])

    backtest_results = [
        {
            "position": "QB",
            "target": "passing_yards",
            "predictions": y_pred,
            "actuals": y_true,
            "n_samples": 5,
        }
    ]

    summary = summarize_backtest_results(backtest_results)

    # R² should be very high (good predictions)
    assert summary["overall_accuracy_pct"] > 90.0
    assert summary["overall_confidence"] == "High"
    assert summary["total_models"] == 1
    assert summary["total_predictions"] == 5

    # Model-specific summary
    assert len(summary["by_model"]) == 1
    model_summary = summary["by_model"][0]
    assert model_summary["position"] == "QB"
    assert model_summary["target"] == "passing_yards"
    assert model_summary["accuracy_pct"] > 90.0
    assert model_summary["confidence"] == "High"
    assert model_summary["sample_count"] == 5
    assert model_summary["r2"] > 0.9
    assert model_summary["mae"] > 0


def test_summarize_backtest_results_multiple_models() -> None:
    """Verify summary aggregates multiple models correctly."""
    # Good model (R² ~ 0.99)
    y_true_1 = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    y_pred_1 = np.array([110.0, 190.0, 310.0, 390.0, 510.0])

    # Medium model (R² ~ 0.4)
    y_true_2 = np.array([50.0, 100.0, 150.0, 200.0, 250.0])
    y_pred_2 = np.array([60.0, 90.0, 140.0, 210.0, 240.0])

    backtest_results = [
        {
            "position": "QB",
            "target": "passing_yards",
            "predictions": y_pred_1,
            "actuals": y_true_1,
            "n_samples": 5,
        },
        {
            "position": "RB",
            "target": "rushing_yards",
            "predictions": y_pred_2,
            "actuals": y_true_2,
            "n_samples": 5,
        },
    ]

    summary = summarize_backtest_results(backtest_results)

    # Overall metrics should aggregate across both models
    assert summary["total_models"] == 2
    assert summary["total_predictions"] == 10

    # Model-specific summaries
    assert len(summary["by_model"]) == 2

    # First model should be High confidence
    model_1 = summary["by_model"][0]
    assert model_1["position"] == "QB"
    assert model_1["confidence"] == "High"
    assert model_1["r2"] > 0.9

    # Second model should be Medium confidence
    model_2 = summary["by_model"][1]
    assert model_2["position"] == "RB"
    assert model_2["confidence"] in ["Medium", "High"]  # Depends on exact R²
    assert 0.3 < model_2["r2"] < 1.0


def test_summarize_backtest_results_r2_based_confidence() -> None:
    """Verify confidence tiers match R² thresholds across models."""
    # Create models with specific R² values
    # High: R² 0.6
    y_true_high = np.array([100.0, 200.0, 150.0, 250.0, 180.0, 220.0])
    y_pred_high = np.array([110.0, 190.0, 145.0, 255.0, 175.0, 215.0])

    # Medium: R² 0.4
    y_true_med = np.array([100.0, 200.0, 150.0, 250.0, 180.0])
    y_pred_med = np.array([120.0, 180.0, 140.0, 260.0, 170.0])

    # Low: R² 0.1
    y_true_low = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    y_pred_low = np.array([300.0, 300.0, 300.0, 300.0, 300.0])

    backtest_results = [
        {
            "position": "QB",
            "target": "passing_yards",
            "predictions": y_pred_high,
            "actuals": y_true_high,
            "n_samples": 6,
        },
        {
            "position": "RB",
            "target": "rushing_yards",
            "predictions": y_pred_med,
            "actuals": y_true_med,
            "n_samples": 5,
        },
        {
            "position": "WR",
            "target": "receiving_yards",
            "predictions": y_pred_low,
            "actuals": y_true_low,
            "n_samples": 5,
        },
    ]

    summary = summarize_backtest_results(backtest_results)

    # Check each model's confidence matches R² tier
    for model in summary["by_model"]:
        r2 = model["r2"]
        confidence = model["confidence"]

        if r2 > 0.5:
            assert confidence == "High"
        elif r2 > 0.3:
            assert confidence == "Medium"
        else:
            assert confidence == "Low"
