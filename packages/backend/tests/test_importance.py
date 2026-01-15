"""
Unit tests for feature importance analysis.

Tests cover:
- XGBoost native importance extraction
- SHAP value computation with TreeExplainer
- SHAP importance aggregation
- analyze_feature_importance with and without samples
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from xgboost import XGBRegressor

from lineupiq.models.importance import (
    analyze_feature_importance,
    compute_shap_values,
    get_shap_importance,
    get_xgb_importance,
)


@pytest.fixture
def synthetic_data() -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Create small synthetic dataset for fast tests.

    Returns:
        Tuple of (X, y, feature_names) with 100 samples and 5 features.
    """
    np.random.seed(42)
    n_samples = 100
    n_features = 5

    X = np.random.randn(n_samples, n_features)
    # Simple linear relationship with noise
    y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1

    feature_names = [f"feature_{i}" for i in range(n_features)]
    return X, y, feature_names


@pytest.fixture
def trained_model(synthetic_data: tuple[np.ndarray, np.ndarray, list[str]]) -> XGBRegressor:
    """Create a trained XGBoost model for testing."""
    X, y, _ = synthetic_data
    model = XGBRegressor(
        n_estimators=10,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X, y)
    return model


@pytest.fixture
def temp_models_dir(tmp_path: Path) -> Path:
    """Create temporary directory for model persistence tests."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    return models_dir


def test_get_xgb_importance_returns_dict(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
) -> None:
    """Verify XGBoost importance extraction returns dict."""
    _, _, feature_names = synthetic_data

    importance = get_xgb_importance(trained_model, feature_names)

    # Should return dict
    assert isinstance(importance, dict)
    # Should have some features (not all may be used depending on tree structure)
    assert len(importance) > 0


def test_xgb_importance_normalized(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
) -> None:
    """Verify XGBoost importance values sum to 1.0."""
    _, _, feature_names = synthetic_data

    importance = get_xgb_importance(trained_model, feature_names)

    # Values should sum to 1.0 (normalized)
    total = sum(importance.values())
    assert abs(total - 1.0) < 0.001, f"Expected sum to be 1.0, got {total}"


def test_xgb_importance_without_feature_names(
    trained_model: XGBRegressor,
) -> None:
    """Verify XGBoost importance works without feature names."""
    importance = get_xgb_importance(trained_model)

    # Should return dict with default feature names (f0, f1, ...)
    assert isinstance(importance, dict)
    assert len(importance) > 0
    # Keys should be f0, f1, etc. format
    for key in importance.keys():
        assert key.startswith("f") or key.startswith("feature_")


def test_compute_shap_values_shape(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
) -> None:
    """Verify SHAP values have correct shape."""
    X, _, _ = synthetic_data
    X_sample = X[:20]  # Use subset for speed

    shap_values, expected_value = compute_shap_values(trained_model, X_sample)

    # Shape should be (n_samples, n_features)
    assert shap_values.shape == (20, 5), f"Expected (20, 5), got {shap_values.shape}"
    # Expected value should be a numeric type (float or numpy float)
    assert isinstance(expected_value, (float, np.floating))


def test_get_shap_importance_returns_dict(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
) -> None:
    """Verify SHAP importance aggregation returns dict."""
    X, _, feature_names = synthetic_data
    X_sample = X[:20]

    shap_values, _ = compute_shap_values(trained_model, X_sample)
    importance = get_shap_importance(shap_values, feature_names)

    # Should return dict with all features
    assert isinstance(importance, dict)
    assert len(importance) == len(feature_names)
    # All feature names should be present
    for name in feature_names:
        assert name in importance


def test_get_shap_importance_normalized(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
) -> None:
    """Verify SHAP importance values sum to 1.0."""
    X, _, feature_names = synthetic_data
    X_sample = X[:20]

    shap_values, _ = compute_shap_values(trained_model, X_sample)
    importance = get_shap_importance(shap_values, feature_names)

    # Values should sum to 1.0 (normalized)
    total = sum(importance.values())
    assert abs(total - 1.0) < 0.001, f"Expected sum to be 1.0, got {total}"


def test_get_shap_importance_feature_mismatch() -> None:
    """Verify error raised when feature count doesn't match."""
    # Create fake SHAP values with 5 features
    shap_values = np.random.randn(10, 5)
    # But only 3 feature names
    feature_names = ["a", "b", "c"]

    with pytest.raises(ValueError, match="Feature count mismatch"):
        get_shap_importance(shap_values, feature_names)


def test_analyze_feature_importance_without_samples(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
    temp_models_dir: Path,
) -> None:
    """Test analyze_feature_importance in XGBoost-only mode."""
    X, y, feature_names = synthetic_data

    # Mock MODELS_DIR and save a model
    with patch("lineupiq.models.persistence.MODELS_DIR", temp_models_dir):
        from lineupiq.models import save_model
        save_model(trained_model, "QB", "passing_yards", {"n_samples": len(y)})

        # Patch for analyze_feature_importance to find the model
        with patch("lineupiq.models.importance.load_model") as mock_load:
            mock_load.return_value = (trained_model, {"feature_names": feature_names})

            result = analyze_feature_importance("QB", "passing_yards")

    # Should have XGBoost importance
    assert "xgb_importance" in result
    assert isinstance(result["xgb_importance"], dict)

    # Should have top features
    assert "top_features" in result
    assert len(result["top_features"]) <= 5

    # Should NOT have SHAP importance (no samples provided)
    assert "shap_importance" not in result

    # Should have metadata
    assert result["position"] == "QB"
    assert result["target"] == "passing_yards"


def test_analyze_feature_importance_with_samples(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
    temp_models_dir: Path,
) -> None:
    """Test analyze_feature_importance with full SHAP analysis."""
    X, y, feature_names = synthetic_data

    # Mock MODELS_DIR and save a model
    with patch("lineupiq.models.persistence.MODELS_DIR", temp_models_dir):
        from lineupiq.models import save_model
        save_model(trained_model, "QB", "passing_yards", {"n_samples": len(y)})

        # Patch for analyze_feature_importance to find the model
        with patch("lineupiq.models.importance.load_model") as mock_load:
            mock_load.return_value = (trained_model, {"feature_names": feature_names})

            result = analyze_feature_importance(
                "QB",
                "passing_yards",
                X_sample=X[:50],  # Use subset for speed
            )

    # Should have XGBoost importance
    assert "xgb_importance" in result
    assert isinstance(result["xgb_importance"], dict)

    # Should have SHAP importance (samples provided)
    assert "shap_importance" in result
    assert isinstance(result["shap_importance"], dict)
    assert len(result["shap_importance"]) == len(feature_names)

    # Should have expected value (float or numpy float)
    assert "expected_value" in result
    assert isinstance(result["expected_value"], (float, np.floating))

    # Should have top features
    assert "top_features" in result

    # Should have metadata
    assert result["position"] == "QB"
    assert result["target"] == "passing_yards"


def test_analyze_feature_importance_limits_samples(
    trained_model: XGBRegressor,
    synthetic_data: tuple[np.ndarray, np.ndarray, list[str]],
    temp_models_dir: Path,
) -> None:
    """Test that analyze_feature_importance limits sample count."""
    X, y, feature_names = synthetic_data

    with patch("lineupiq.models.importance.load_model") as mock_load:
        mock_load.return_value = (trained_model, {"feature_names": feature_names})

        # Pass 100 samples but limit to 20
        result = analyze_feature_importance(
            "QB",
            "passing_yards",
            X_sample=X,  # All 100 samples
            n_samples=20,  # But limit to 20
        )

    # Should still have SHAP importance (with limited samples)
    assert "shap_importance" in result
    assert isinstance(result["shap_importance"], dict)
