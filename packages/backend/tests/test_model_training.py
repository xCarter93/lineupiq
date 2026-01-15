"""
Unit tests for ML training infrastructure.

Tests cover:
- Hyperparameter generation from Optuna trials
- Model training with TimeSeriesSplit CV
- Hyperparameter tuning workflow
- Model save/load roundtrip
- Model listing
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import optuna
import pytest

from lineupiq.models import (
    get_xgb_params,
    list_models,
    load_model,
    save_model,
    train_model,
    tune_hyperparameters,
)


@pytest.fixture
def synthetic_data() -> tuple[np.ndarray, np.ndarray]:
    """Create small synthetic dataset for fast tests.

    Returns:
        Tuple of (X, y) with 200 samples and 5 features.
    """
    np.random.seed(42)
    n_samples = 200
    n_features = 5

    X = np.random.randn(n_samples, n_features)
    # Simple linear relationship with noise
    y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1

    return X, y


@pytest.fixture
def temp_models_dir(tmp_path: Path) -> Path:
    """Create temporary directory for model persistence tests."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    return models_dir


def test_get_xgb_params_returns_valid_dict() -> None:
    """Verify get_xgb_params returns dict with expected keys."""
    # Create a trial from a study
    study = optuna.create_study()
    trial = study.ask()

    params = get_xgb_params(trial)

    # Check all expected keys are present
    expected_keys = [
        "max_depth",
        "learning_rate",
        "n_estimators",
        "min_child_weight",
        "subsample",
        "colsample_bytree",
        "reg_alpha",
        "reg_lambda",
    ]

    for key in expected_keys:
        assert key in params, f"Missing key: {key}"

    # Check value ranges
    assert 3 <= params["max_depth"] <= 9
    assert 0.01 <= params["learning_rate"] <= 0.3
    assert 100 <= params["n_estimators"] <= 500
    assert 1 <= params["min_child_weight"] <= 20
    assert 0.6 <= params["subsample"] <= 1.0
    assert 0.6 <= params["colsample_bytree"] <= 1.0
    assert 1e-8 <= params["reg_alpha"] <= 10.0
    assert 1e-8 <= params["reg_lambda"] <= 10.0


def test_train_model_returns_model_and_scores(
    synthetic_data: tuple[np.ndarray, np.ndarray]
) -> None:
    """Test train_model returns trained model and CV scores."""
    X, y = synthetic_data

    model, scores = train_model(X, y, n_splits=3)

    # Model should be fitted
    assert hasattr(model, "feature_importances_")

    # Scores array should have n_splits elements
    assert len(scores) == 3

    # Scores are negative RMSE (should be negative)
    assert all(score < 0 for score in scores)


def test_train_model_uses_timeseries_split(
    synthetic_data: tuple[np.ndarray, np.ndarray]
) -> None:
    """Verify TimeSeriesSplit is used (no future leakage)."""
    X, y = synthetic_data

    # Mock TimeSeriesSplit to verify it's being used
    with patch("lineupiq.models.training.TimeSeriesSplit") as mock_tscv:
        # Configure mock to return valid splits
        mock_tscv.return_value.split.return_value = [
            (np.arange(100), np.arange(100, 150)),
            (np.arange(150), np.arange(150, 200)),
        ]

        # This will use the mock
        train_model(X, y, n_splits=2)

        # Verify TimeSeriesSplit was instantiated with n_splits
        mock_tscv.assert_called_once_with(n_splits=2)


def test_tune_hyperparameters_returns_best_params(
    synthetic_data: tuple[np.ndarray, np.ndarray]
) -> None:
    """Quick 5-trial test for hyperparameter tuning."""
    X, y = synthetic_data

    # Run small optimization (5 trials, 2 CV splits for speed)
    best_params, study = tune_hyperparameters(X, y, n_trials=5, n_splits=2)

    # Should return dict with hyperparameters
    assert isinstance(best_params, dict)
    assert "max_depth" in best_params
    assert "learning_rate" in best_params

    # Study should have completed trials
    assert len(study.trials) == 5
    assert study.best_value is not None


def test_save_and_load_model_roundtrip(
    synthetic_data: tuple[np.ndarray, np.ndarray],
    temp_models_dir: Path,
) -> None:
    """Save model, load it, verify same predictions."""
    X, y = synthetic_data

    # Train a model
    model, scores = train_model(X, y, n_splits=3)

    # Get predictions before save
    predictions_before = model.predict(X[:10])

    # Mock MODELS_DIR to use temp directory
    with patch("lineupiq.models.persistence.MODELS_DIR", temp_models_dir):
        # Save model
        metadata = {
            "n_samples": len(y),
            "cv_scores": scores.tolist(),
        }
        path = save_model(model, "QB", "passing_yards", metadata)

        assert path.exists()
        assert path.name == "QB_passing_yards.joblib"

        # Load model
        loaded_model, loaded_metadata = load_model("QB", "passing_yards")

        # Get predictions after load
        predictions_after = loaded_model.predict(X[:10])

        # Predictions should be identical
        np.testing.assert_array_almost_equal(predictions_before, predictions_after)

        # Metadata should be preserved
        assert loaded_metadata["n_samples"] == len(y)
        assert loaded_metadata["cv_scores"] == scores.tolist()


def test_list_models_finds_saved(
    synthetic_data: tuple[np.ndarray, np.ndarray],
    temp_models_dir: Path,
) -> None:
    """Save a model, verify list_models includes it."""
    X, y = synthetic_data

    with patch("lineupiq.models.persistence.MODELS_DIR", temp_models_dir):
        # Initially empty
        assert list_models() == []

        # Train and save a model
        model, _ = train_model(X, y, n_splits=2)
        save_model(model, "QB", "passing_yards")

        # Should now find the model
        models = list_models()
        assert ("QB", "passing_yards") in models

        # Save another model
        save_model(model, "RB", "rushing_yards")

        models = list_models()
        assert len(models) == 2
        assert ("QB", "passing_yards") in models
        assert ("RB", "rushing_yards") in models
