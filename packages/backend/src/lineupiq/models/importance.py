"""
Feature importance analysis using SHAP values and XGBoost native importance.

Provides tools for understanding which features contribute most to model predictions:
- XGBoost native gain-based importance
- SHAP TreeExplainer for model-agnostic explanations
- Combined analysis with top feature identification

Key functions:
- get_xgb_importance: Extract XGBoost native feature importance
- compute_shap_values: Compute SHAP values using TreeExplainer
- get_shap_importance: Aggregate SHAP values to feature importance
- analyze_feature_importance: Complete importance analysis for a model
"""

import logging
from typing import Any

import numpy as np
import shap
from xgboost import XGBRegressor

from lineupiq.models.persistence import load_model

logger = logging.getLogger(__name__)


def get_xgb_importance(
    model: XGBRegressor,
    feature_names: list[str] | None = None,
) -> dict[str, float]:
    """Extract XGBoost native feature importance (gain-based).

    Uses the gain metric which measures the average training loss reduction
    gained when using a feature for splitting.

    Args:
        model: Trained XGBRegressor model.
        feature_names: Optional list of feature names. If not provided,
            uses f0, f1, f2... as names.

    Returns:
        Dict mapping feature name to normalized importance value.
        Values sum to 1.0 for comparability.

    Example:
        >>> model = XGBRegressor()
        >>> model.fit(X, y)
        >>> importance = get_xgb_importance(model, ["feat1", "feat2"])
        >>> sum(importance.values())
        1.0
    """
    # Get raw importance scores from booster
    booster = model.get_booster()
    raw_importance = booster.get_score(importance_type="gain")

    # If no features were used (empty model), return empty dict
    if not raw_importance:
        logger.warning("Model has no feature importance scores")
        return {}

    # Map feature indices (f0, f1, ...) to names if provided
    importance_dict: dict[str, float] = {}

    for key, value in raw_importance.items():
        # XGBoost uses f0, f1, f2... by default
        if feature_names is not None:
            # Parse index from key like "f0" -> 0
            if key.startswith("f") and key[1:].isdigit():
                idx = int(key[1:])
                if idx < len(feature_names):
                    importance_dict[feature_names[idx]] = value
                else:
                    importance_dict[key] = value
            else:
                importance_dict[key] = value
        else:
            importance_dict[key] = value

    # Normalize to sum to 1.0
    total = sum(importance_dict.values())
    if total > 0:
        importance_dict = {k: v / total for k, v in importance_dict.items()}

    logger.info(f"Extracted XGBoost importance for {len(importance_dict)} features")
    return importance_dict


def compute_shap_values(
    model: XGBRegressor,
    X: np.ndarray,
    feature_names: list[str] | None = None,
) -> tuple[np.ndarray, float]:
    """Compute SHAP values using TreeExplainer for XGBoost model.

    TreeExplainer is optimized for tree-based models and computes exact
    SHAP values efficiently.

    Args:
        model: Trained XGBRegressor model.
        X: Sample data to explain, shape (n_samples, n_features).
        feature_names: Optional feature names for explanation context.

    Returns:
        Tuple of:
        - shap_values: SHAP values array, shape (n_samples, n_features)
        - expected_value: Base value (model's expected output)

    Example:
        >>> shap_vals, expected = compute_shap_values(model, X_sample)
        >>> shap_vals.shape
        (100, 17)
    """
    logger.info(f"Computing SHAP values for {X.shape[0]} samples, {X.shape[1]} features")

    # Create TreeExplainer - optimized for XGBoost
    explainer = shap.TreeExplainer(model)

    # Compute SHAP values
    shap_values = explainer.shap_values(X)

    # Get expected value (base prediction)
    expected_value = explainer.expected_value

    # Handle case where expected_value is an array (some versions)
    if isinstance(expected_value, np.ndarray):
        expected_value = float(expected_value[0]) if len(expected_value) > 0 else 0.0

    logger.info(f"SHAP values computed: shape={shap_values.shape}, expected={expected_value:.4f}")
    return shap_values, expected_value


def get_shap_importance(
    shap_values: np.ndarray,
    feature_names: list[str],
) -> dict[str, float]:
    """Compute feature importance from SHAP values.

    Takes mean absolute SHAP value per feature as importance metric.
    This measures average impact on prediction magnitude.

    Args:
        shap_values: SHAP values array, shape (n_samples, n_features).
        feature_names: List of feature names matching columns.

    Returns:
        Dict mapping feature name to normalized importance value.
        Values sum to 1.0 for comparability.

    Example:
        >>> importance = get_shap_importance(shap_vals, feature_names)
        >>> importance["passing_yards_roll3"]
        0.15
    """
    if shap_values.shape[1] != len(feature_names):
        raise ValueError(
            f"Feature count mismatch: SHAP has {shap_values.shape[1]} features, "
            f"but {len(feature_names)} names provided"
        )

    # Mean absolute SHAP value per feature
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    # Build dict
    importance_dict = {
        name: float(value)
        for name, value in zip(feature_names, mean_abs_shap)
    }

    # Normalize to sum to 1.0
    total = sum(importance_dict.values())
    if total > 0:
        importance_dict = {k: v / total for k, v in importance_dict.items()}

    logger.info(f"Computed SHAP importance for {len(importance_dict)} features")
    return importance_dict


def analyze_feature_importance(
    position: str,
    target: str,
    X_sample: np.ndarray | None = None,
    n_samples: int = 100,
) -> dict[str, Any]:
    """Analyze feature importance for a trained model.

    Loads model from persistence and computes importance metrics.
    Always computes XGBoost native importance. SHAP importance is
    computed if X_sample is provided.

    Args:
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").
        X_sample: Optional sample data for SHAP analysis. If None,
            only XGBoost importance is returned.
        n_samples: Max samples to use for SHAP (for speed). Ignored
            if X_sample is None.

    Returns:
        Dict containing:
        - xgb_importance: dict of feature -> importance (gain-based)
        - shap_importance: dict of feature -> importance (if X_sample provided)
        - top_features: list of top 5 features by XGBoost importance
        - position: input position
        - target: input target

    Raises:
        FileNotFoundError: If model doesn't exist.

    Example:
        >>> result = analyze_feature_importance("QB", "passing_yards", X_sample)
        >>> result["top_features"]
        ['passing_yards_roll3', 'passing_tds_roll3', ...]
    """
    logger.info(f"Analyzing feature importance for {position}/{target}")

    # Load model and metadata
    model, metadata = load_model(position, target)
    feature_names = metadata.get("feature_names")

    # Get XGBoost native importance
    xgb_importance = get_xgb_importance(model, feature_names)

    # Build result dict
    result: dict[str, Any] = {
        "xgb_importance": xgb_importance,
        "position": position,
        "target": target,
    }

    # Add top features by XGBoost importance
    sorted_features = sorted(
        xgb_importance.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    result["top_features"] = [f[0] for f in sorted_features[:5]]

    # Compute SHAP importance if sample data provided
    if X_sample is not None:
        # Limit samples for performance
        if len(X_sample) > n_samples:
            logger.info(f"Limiting SHAP analysis to {n_samples} samples")
            X_sample = X_sample[:n_samples]

        # Compute SHAP values
        shap_values, expected_value = compute_shap_values(model, X_sample, feature_names)

        # Get feature names for SHAP importance
        if feature_names is None:
            feature_names = [f"f{i}" for i in range(X_sample.shape[1])]

        shap_importance = get_shap_importance(shap_values, feature_names)
        result["shap_importance"] = shap_importance
        result["expected_value"] = expected_value

    logger.info(f"Feature importance analysis complete for {position}/{target}")
    return result
