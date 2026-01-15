"""
Unit tests for model evaluation utilities.

Tests cover:
- Metrics calculation (MAE, RMSE, R2, MAPE)
- MAPE handling of zero values
- Holdout split by season
- Model evaluation on test data
- Batch evaluation of all models
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import polars as pl
import pytest

from lineupiq.models.evaluation import (
    calculate_metrics,
    create_holdout_split,
    evaluate_all_models,
    evaluate_model,
)


def test_calculate_metrics_accuracy() -> None:
    """Verify metrics calculation on known values."""
    # Known values for easy verification
    y_true = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    y_pred = np.array([110.0, 190.0, 310.0, 390.0, 510.0])

    metrics = calculate_metrics(y_true, y_pred)

    # MAE = mean(|10, 10, 10, 10, 10|) = 10
    assert metrics["mae"] == pytest.approx(10.0, rel=0.01)

    # RMSE = sqrt(mean(100, 100, 100, 100, 100)) = 10
    assert metrics["rmse"] == pytest.approx(10.0, rel=0.01)

    # R2 should be high (good predictions)
    assert metrics["r2"] > 0.99

    # MAPE = mean(|10/100, 10/200, 10/300, 10/400, 10/500|) * 100
    # = mean(0.1, 0.05, 0.033, 0.025, 0.02) * 100 ~ 4.57%
    assert "mape" in metrics
    assert metrics["mape"] > 0


def test_calculate_metrics_handles_zeros() -> None:
    """Verify MAPE handles zero targets gracefully."""
    # Include zeros in true values
    y_true = np.array([0.0, 100.0, 200.0, 0.0, 300.0])
    y_pred = np.array([10.0, 110.0, 190.0, 5.0, 310.0])

    metrics = calculate_metrics(y_true, y_pred)

    # Should not raise division by zero error
    assert "mape" in metrics

    # MAPE should be calculated only on non-zero values
    # Non-zero: (10/100, 10/200, 10/300) = (0.1, 0.05, 0.033)
    # Mean ~ 6.1%
    assert metrics["mape"] > 0
    assert not np.isnan(metrics["mape"])


def test_calculate_metrics_all_zeros() -> None:
    """Verify MAPE returns NaN when all targets are zero."""
    y_true = np.array([0.0, 0.0, 0.0])
    y_pred = np.array([1.0, 2.0, 3.0])

    metrics = calculate_metrics(y_true, y_pred)

    # MAPE undefined when all actuals are zero
    assert np.isnan(metrics["mape"])

    # Other metrics should still work
    assert metrics["mae"] == pytest.approx(2.0)


def test_create_holdout_split() -> None:
    """Verify season-based splitting works correctly."""
    df = pl.DataFrame({
        "season": [2022, 2022, 2023, 2023, 2024, 2024],
        "week": [1, 2, 1, 2, 1, 2],
        "value": [10, 20, 30, 40, 50, 60],
    })

    train_df, test_df = create_holdout_split(df, test_season=2024)

    # Train should have 2022 and 2023 (4 rows)
    assert len(train_df) == 4
    assert set(train_df["season"].unique().to_list()) == {2022, 2023}

    # Test should have only 2024 (2 rows)
    assert len(test_df) == 2
    assert test_df["season"].unique().to_list() == [2024]


def test_create_holdout_split_empty_test() -> None:
    """Verify handling when test season has no data."""
    df = pl.DataFrame({
        "season": [2022, 2023],
        "value": [10, 20],
    })

    train_df, test_df = create_holdout_split(df, test_season=2024)

    # All data in train, none in test
    assert len(train_df) == 2
    assert len(test_df) == 0


@pytest.fixture
def mock_test_df() -> pl.DataFrame:
    """Create mock test DataFrame with required columns."""
    np.random.seed(42)
    n_samples = 50

    # Create feature columns
    feature_data = {
        "position": ["QB"] * n_samples,
        "player_id": [f"player_{i}" for i in range(n_samples)],
        "passing_yards": np.random.randint(150, 350, n_samples).astype(float),
        "passing_tds": np.random.randint(0, 4, n_samples).astype(float),
        # Rolling features
        "passing_yards_roll3": np.random.uniform(150, 350, n_samples),
        "passing_tds_roll3": np.random.uniform(0, 3, n_samples),
        "rushing_yards_roll3": np.random.uniform(0, 50, n_samples),
        "rushing_tds_roll3": np.random.uniform(0, 1, n_samples),
        "carries_roll3": np.random.uniform(0, 10, n_samples),
        "receiving_yards_roll3": np.random.uniform(0, 20, n_samples),
        "receiving_tds_roll3": np.random.uniform(0, 0.5, n_samples),
        "receptions_roll3": np.random.uniform(0, 3, n_samples),
        # Opponent features
        "opp_pass_defense_strength": np.random.uniform(0, 1, n_samples),
        "opp_rush_defense_strength": np.random.uniform(0, 1, n_samples),
        "opp_pass_yards_allowed_rank": np.random.randint(1, 33, n_samples),
        "opp_rush_yards_allowed_rank": np.random.randint(1, 33, n_samples),
        "opp_total_yards_allowed_rank": np.random.randint(1, 33, n_samples),
        # Weather features
        "temp_normalized": np.random.uniform(-1, 1, n_samples),
        "wind_normalized": np.random.uniform(0, 1, n_samples),
        # Context features
        "is_home": np.random.choice([0, 1], n_samples),
        "is_dome": np.random.choice([0, 1], n_samples),
    }

    return pl.DataFrame(feature_data)


def test_evaluate_model_returns_metrics(mock_test_df: pl.DataFrame) -> None:
    """Test evaluate_model returns expected metrics dict."""
    # Create a mock model that returns predictions
    mock_model = MagicMock()
    mock_model.predict.return_value = np.random.uniform(150, 350, len(mock_test_df))

    mock_metadata = {
        "n_samples": 1000,
        "cv_scores": [-50.0, -45.0, -55.0],
    }

    with patch("lineupiq.models.evaluation.load_model") as mock_load:
        mock_load.return_value = (mock_model, mock_metadata)

        result = evaluate_model("QB", "passing_yards", mock_test_df)

        # Check structure
        assert "mae" in result
        assert "rmse" in result
        assert "r2" in result
        assert "mape" in result
        assert result["position"] == "QB"
        assert result["target"] == "passing_yards"
        assert result["n_samples"] == len(mock_test_df)

        # Model should have been called with feature matrix
        mock_model.predict.assert_called_once()


def test_evaluate_model_no_samples_for_position(mock_test_df: pl.DataFrame) -> None:
    """Test evaluate_model raises when position has no samples."""
    # Change all positions to RB (no QB data)
    df = mock_test_df.with_columns(pl.lit("RB").alias("position"))

    with patch("lineupiq.models.evaluation.load_model") as mock_load:
        mock_load.return_value = (MagicMock(), {})

        with pytest.raises(ValueError, match="No test samples for position QB"):
            evaluate_model("QB", "passing_yards", df)


def test_evaluate_all_models_returns_list(mock_test_df: pl.DataFrame) -> None:
    """Verify evaluate_all_models evaluates all trained models."""
    # Mock list_models to return 2 models
    mock_models_list = [("QB", "passing_yards"), ("QB", "passing_tds")]

    # Create mock model
    mock_model = MagicMock()
    mock_model.predict.return_value = np.random.uniform(0, 300, len(mock_test_df))

    with patch("lineupiq.models.evaluation.list_models") as mock_list:
        mock_list.return_value = mock_models_list

        with patch("lineupiq.models.evaluation.load_model") as mock_load:
            mock_load.return_value = (mock_model, {})

            results = evaluate_all_models(mock_test_df)

            # Should have results for both models
            assert len(results) == 2

            # Each result should have metrics
            for result in results:
                assert "mae" in result
                assert "rmse" in result
                assert "r2" in result
                assert "position" in result
                assert "target" in result


def test_evaluate_all_models_handles_missing_model(mock_test_df: pl.DataFrame) -> None:
    """Verify evaluate_all_models continues when a model is missing."""
    mock_models_list = [("QB", "passing_yards"), ("QB", "missing_target")]

    mock_model = MagicMock()
    mock_model.predict.return_value = np.random.uniform(0, 300, len(mock_test_df))

    with patch("lineupiq.models.evaluation.list_models") as mock_list:
        mock_list.return_value = mock_models_list

        with patch("lineupiq.models.evaluation.load_model") as mock_load:
            # First call succeeds, second raises
            mock_load.side_effect = [
                (mock_model, {}),
                FileNotFoundError("Model not found"),
            ]

            results = evaluate_all_models(mock_test_df)

            # Should have 1 result (the successful one)
            assert len(results) == 1
            assert results[0]["target"] == "passing_yards"
