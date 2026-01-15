"""
Unit tests for RB (Running Back) model training.

Tests cover:
- Data preparation filtering to RB position
- Feature column extraction
- Model training integration (small n_trials for speed)
- Prediction reasonableness for saved models
"""

from unittest.mock import patch

import numpy as np
import polars as pl
import pytest

from lineupiq.features.pipeline import get_feature_columns
from lineupiq.models.persistence import load_model
from lineupiq.models.rb import RB_TARGETS, prepare_rb_data, train_rb_models


@pytest.fixture
def sample_rb_dataframe() -> pl.DataFrame:
    """Create sample DataFrame with RB and other position data.

    Returns:
        DataFrame with feature columns and target columns for testing.
    """
    np.random.seed(42)
    feature_cols = get_feature_columns()
    n_samples = 100

    # Create base data dict
    data: dict[str, list] = {
        "player_id": [f"player_{i}" for i in range(n_samples)],
        "player_name": [f"Player {i}" for i in range(n_samples)],
        "position": ["RB"] * 60 + ["WR"] * 20 + ["QB"] * 10 + ["TE"] * 10,
        "season": [2024] * n_samples,
        "week": [(i % 17) + 1 for i in range(n_samples)],
    }

    # Add feature columns with random values
    for col in feature_cols:
        data[col] = np.random.randn(n_samples).tolist()

    # Add target columns with reasonable random values
    data["rushing_yards"] = (np.random.randn(n_samples) * 30 + 50).clip(0, 200).tolist()
    data["rushing_tds"] = (np.random.randn(n_samples) * 0.5 + 0.3).clip(0, 3).tolist()
    data["carries"] = (np.random.randn(n_samples) * 5 + 12).clip(0, 30).tolist()
    data["receiving_yards"] = (np.random.randn(n_samples) * 15 + 20).clip(0, 100).tolist()
    data["receptions"] = (np.random.randn(n_samples) * 1.5 + 2).clip(0, 10).tolist()
    data["passing_yards"] = (np.random.randn(n_samples) * 50 + 200).clip(0, 400).tolist()
    data["passing_tds"] = (np.random.randn(n_samples) * 0.8 + 1.5).clip(0, 5).tolist()

    return pl.DataFrame(data)


def test_prepare_rb_data_filters_position(sample_rb_dataframe: pl.DataFrame) -> None:
    """Verify prepare_rb_data only returns RB data."""
    X, y = prepare_rb_data(sample_rb_dataframe)

    # Original had 100 samples with 60 RBs
    # After filtering to RB and dropping nulls, should have exactly 60
    assert X.shape[0] == 60, f"Expected 60 RB samples, got {X.shape[0]}"


def test_prepare_rb_data_returns_correct_features(sample_rb_dataframe: pl.DataFrame) -> None:
    """Feature count matches get_feature_columns()."""
    X, y = prepare_rb_data(sample_rb_dataframe)

    expected_feature_count = len(get_feature_columns())
    assert X.shape[1] == expected_feature_count, (
        f"Expected {expected_feature_count} features, got {X.shape[1]}"
    )


def test_prepare_rb_data_returns_all_targets(sample_rb_dataframe: pl.DataFrame) -> None:
    """All RB targets are extracted."""
    X, y = prepare_rb_data(sample_rb_dataframe)

    for target in RB_TARGETS:
        assert target in y, f"Missing target: {target}"
        assert len(y[target]) == X.shape[0], f"Target {target} length mismatch"


def test_train_rb_models_creates_models(tmp_path: pytest.TempPathFactory) -> None:
    """Integration test: train models with small n_trials for speed.

    Uses mock MODELS_DIR to avoid polluting real models directory.
    Uses smaller season set for faster training.
    """
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    with patch("lineupiq.models.rb.save_model") as mock_save:
        with patch("lineupiq.models.persistence.MODELS_DIR", models_dir):
            # Train with minimal settings for speed
            # Using 2024 only and just 5 trials
            results = train_rb_models(seasons=[2024], n_trials=5)

            # Should have results for all 5 targets
            assert len(results) == 5, f"Expected 5 targets, got {len(results)}"

            for target in RB_TARGETS:
                assert target in results, f"Missing target in results: {target}"
                model, metrics = results[target]

                # Model should be trained (has feature_importances_)
                assert hasattr(model, "feature_importances_")

                # Metrics should have expected keys
                assert "cv_rmse_mean" in metrics
                assert "cv_rmse_std" in metrics
                assert "best_params" in metrics
                assert "n_samples" in metrics


def test_rb_model_predictions_reasonable() -> None:
    """Load saved models and verify predictions are in reasonable ranges.

    This test requires trained models to exist in the models/ directory.
    Skip if models don't exist.

    Note: Models may predict slightly negative values when given random input,
    since the model was trained on realistic feature distributions. We test
    that predictions are within a relaxed range that allows for model extrapolation.
    """
    try:
        # Try to load one model to check if models exist
        load_model("RB", "rushing_yards")
    except FileNotFoundError:
        pytest.skip("RB models not trained yet - run train_rb_models first")

    # Create sample input with correct feature count
    feature_cols = get_feature_columns()
    n_samples = 10
    np.random.seed(42)

    # Create random feature data
    X = np.random.randn(n_samples, len(feature_cols))

    # Define reasonable prediction ranges for each target
    # Allow negative values since random features may extrapolate beyond training
    ranges = {
        "rushing_yards": (-50, 300),
        "rushing_tds": (-1, 5),
        "carries": (-5, 40),
        "receiving_yards": (-30, 150),
        "receptions": (-2, 15),
    }

    for target in RB_TARGETS:
        model, _ = load_model("RB", target)
        predictions = model.predict(X)

        min_val, max_val = ranges[target]
        assert all(
            min_val <= p <= max_val for p in predictions
        ), f"{target} predictions out of range [{min_val}, {max_val}]: {predictions}"


def test_rb_targets_constant() -> None:
    """Verify RB_TARGETS contains expected targets."""
    expected = ["rushing_yards", "rushing_tds", "carries", "receiving_yards", "receptions"]
    assert RB_TARGETS == expected, f"RB_TARGETS mismatch: {RB_TARGETS}"
