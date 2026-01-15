"""
Model evaluation utilities for assessing trained ML model performance.

Provides functions for:
- Calculating standard regression metrics (MAE, RMSE, R2, MAPE)
- Creating holdout splits by season for out-of-sample validation
- Evaluating individual models and all trained models

Key functions:
- calculate_metrics: Compute MAE, RMSE, R2, MAPE from predictions
- create_holdout_split: Split data by season for temporal validation
- evaluate_model: Evaluate a single position/target model
- evaluate_all_models: Evaluate all trained models
"""

import logging
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from lineupiq.features.pipeline import get_feature_columns
from lineupiq.models.persistence import list_models, load_model

logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: NDArray[np.floating[Any]],
    y_pred: NDArray[np.floating[Any]],
) -> dict[str, float]:
    """Calculate regression metrics for model evaluation.

    Computes standard metrics for comparing predictions to actuals:
    - MAE: Mean Absolute Error (average absolute difference)
    - RMSE: Root Mean Squared Error (penalizes large errors)
    - R2: R-squared coefficient (variance explained)
    - MAPE: Mean Absolute Percentage Error (percentage-based)

    Args:
        y_true: Array of actual values.
        y_pred: Array of predicted values.

    Returns:
        Dict with mae, rmse, r2, mape keys.

    Example:
        >>> y_true = np.array([100, 200, 150])
        >>> y_pred = np.array([110, 190, 160])
        >>> metrics = calculate_metrics(y_true, y_pred)
        >>> 'mae' in metrics
        True
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    r2 = r2_score(y_true, y_pred)

    # MAPE with zero handling: skip zeros in denominator
    # Use np.where to avoid division by zero
    nonzero_mask = y_true != 0
    if nonzero_mask.sum() > 0:
        mape = np.mean(
            np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])
        ) * 100
    else:
        # All zeros - MAPE undefined
        mape = np.nan

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "mape": float(mape),
    }


def create_holdout_split(
    df: pl.DataFrame,
    test_season: int = 2024,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Split data by season for holdout validation.

    Creates train/test split where training uses all seasons before
    test_season, and testing uses test_season only. This provides
    true out-of-sample validation - models trained on historical data
    are tested on future data they haven't seen.

    Args:
        df: Feature DataFrame with 'season' column.
        test_season: Season to hold out for testing (default: 2024).

    Returns:
        Tuple of (train_df, test_df) DataFrames.

    Example:
        >>> df = pl.DataFrame({"season": [2022, 2023, 2024], "value": [1, 2, 3]})
        >>> train, test = create_holdout_split(df, test_season=2024)
        >>> len(train)
        2
        >>> len(test)
        1
    """
    train_df = df.filter(pl.col("season") < test_season)
    test_df = df.filter(pl.col("season") == test_season)

    logger.info(
        f"Holdout split: {len(train_df)} train (seasons < {test_season}), "
        f"{len(test_df)} test (season {test_season})"
    )

    return train_df, test_df


def evaluate_model(
    position: str,
    target: str,
    test_df: pl.DataFrame,
) -> dict[str, Any]:
    """Evaluate a single trained model on test data.

    Loads the specified model, filters test data to the position,
    generates predictions, and calculates metrics.

    Args:
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").
        test_df: Test DataFrame with features and target column.

    Returns:
        Dict with metrics plus n_samples, position, target keys.

    Raises:
        FileNotFoundError: If model file doesn't exist.
        ValueError: If no test samples for position or missing columns.

    Example:
        >>> results = evaluate_model("QB", "passing_yards", test_df)
        >>> results["position"]
        'QB'
        >>> "mae" in results
        True
    """
    # Load model
    model, metadata = load_model(position, target)

    # Get feature columns
    feature_cols = get_feature_columns()

    # Filter test data to position
    pos_df = test_df.filter(pl.col("position") == position)

    if len(pos_df) == 0:
        raise ValueError(f"No test samples for position {position}")

    # Check target column exists
    if target not in pos_df.columns:
        raise ValueError(f"Target column '{target}' not in test data")

    # Check all feature columns exist
    missing_cols = [c for c in feature_cols if c not in pos_df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns: {missing_cols}")

    # Prepare X and y arrays
    X = pos_df.select(feature_cols).to_numpy()
    y = pos_df.select(target).to_numpy().flatten()

    # Generate predictions
    y_pred = model.predict(X)

    # Calculate metrics
    metrics = calculate_metrics(y, y_pred)

    # Add context
    metrics["position"] = position
    metrics["target"] = target
    metrics["n_samples"] = len(y)

    logger.info(
        f"Evaluated {position}_{target}: MAE={metrics['mae']:.2f}, "
        f"RMSE={metrics['rmse']:.2f}, R2={metrics['r2']:.3f}, "
        f"n={metrics['n_samples']}"
    )

    return metrics


def evaluate_all_models(test_df: pl.DataFrame) -> list[dict[str, Any]]:
    """Evaluate all trained models on test data.

    Lists all saved models and evaluates each one, collecting results.
    Handles missing models or errors gracefully with logging.

    Args:
        test_df: Test DataFrame with features and target columns.

    Returns:
        List of result dicts from evaluate_model, one per model.

    Example:
        >>> results = evaluate_all_models(test_df)
        >>> len(results) > 0
        True
        >>> all("mae" in r for r in results)
        True
    """
    models = list_models()
    logger.info(f"Found {len(models)} trained models to evaluate")

    results = []
    for position, target in models:
        try:
            result = evaluate_model(position, target, test_df)
            results.append(result)
        except FileNotFoundError as e:
            logger.warning(f"Model not found: {position}_{target}: {e}")
        except ValueError as e:
            logger.warning(f"Cannot evaluate {position}_{target}: {e}")
        except Exception as e:
            logger.error(f"Error evaluating {position}_{target}: {e}")

    logger.info(f"Successfully evaluated {len(results)}/{len(models)} models")
    return results
