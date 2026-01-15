"""
Model diagnostics for overfitting detection and train/test performance comparison.

Compares training vs holdout performance to identify models that may need correction.
PROJECT.md notes previous attempts failed due to overfitting - this module provides
quantitative overfitting metrics.

Key functions:
- compute_train_metrics: Calculate train set performance metrics
- compute_overfit_ratio: Calculate test/train RMSE ratio
- diagnose_overfitting: Flag overfitting status with recommendations
- run_diagnostics: Complete diagnostics for a single model
- run_all_diagnostics: Run diagnostics for all saved models
"""

import logging
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from lineupiq.models.persistence import list_models, load_model

logger = logging.getLogger(__name__)


def compute_train_metrics(
    model: XGBRegressor,
    X_train: NDArray[np.floating[Any]],
    y_train: NDArray[np.floating[Any]],
) -> dict[str, float]:
    """Generate predictions on training data and compute performance metrics.

    Args:
        model: Trained XGBRegressor model.
        X_train: Training feature matrix.
        y_train: Training target array.

    Returns:
        Dict with train_mae, train_rmse, train_r2.

    Example:
        >>> model = XGBRegressor()
        >>> model.fit(X_train, y_train)
        >>> metrics = compute_train_metrics(model, X_train, y_train)
        >>> "train_rmse" in metrics
        True
    """
    y_pred = model.predict(X_train)

    train_mae = float(mean_absolute_error(y_train, y_pred))
    train_rmse = float(np.sqrt(mean_squared_error(y_train, y_pred)))
    train_r2 = float(r2_score(y_train, y_pred))

    return {
        "train_mae": train_mae,
        "train_rmse": train_rmse,
        "train_r2": train_r2,
    }


def compute_overfit_ratio(train_rmse: float, test_rmse: float) -> float:
    """Calculate overfit ratio: test_rmse / train_rmse.

    Interpretation:
    - Ratio close to 1.0 = good generalization
    - Ratio >> 1.0 = overfitting (test much worse than train)
    - Ratio < 1.0 = test better than train (unusual, may indicate data issues)

    Args:
        train_rmse: RMSE on training data.
        test_rmse: RMSE on test/holdout data.

    Returns:
        Overfit ratio (test_rmse / train_rmse).

    Example:
        >>> compute_overfit_ratio(10.0, 12.0)
        1.2
        >>> compute_overfit_ratio(10.0, 20.0)
        2.0
    """
    if train_rmse == 0:
        # Avoid division by zero - perfect train fit suggests overfitting
        logger.warning("train_rmse is 0, returning infinite ratio")
        return float("inf")

    return test_rmse / train_rmse


def diagnose_overfitting(
    train_rmse: float,
    test_rmse: float,
    threshold: float = 1.3,
) -> dict[str, Any]:
    """Diagnose model fit status based on train/test performance gap.

    Args:
        train_rmse: RMSE on training data.
        test_rmse: RMSE on test/holdout data.
        threshold: Overfit threshold - ratio above this flags overfitting.
            Default 1.3 means test RMSE up to 30% higher than train is acceptable.

    Returns:
        Dict with:
        - ratio: float - the computed overfit ratio
        - status: str - "healthy", "overfitting", or "underfitting"
        - recommendation: str - suggested action based on status

    Example:
        >>> result = diagnose_overfitting(10.0, 12.0)
        >>> result["status"]
        'healthy'
        >>> result = diagnose_overfitting(10.0, 20.0)
        >>> result["status"]
        'overfitting'
    """
    ratio = compute_overfit_ratio(train_rmse, test_rmse)

    # Determine status
    if ratio > threshold:
        status = "overfitting"
        recommendation = (
            "Model fits training data too closely. Consider: "
            "increasing regularization (reg_alpha, reg_lambda), "
            "reducing max_depth, or using more training data."
        )
    elif train_rmse > 50.0 and ratio < 1.1:
        # High absolute error but train/test similar = underfitting
        # Using 50.0 as threshold since NFL stats typically have errors in 20-40 range
        status = "underfitting"
        recommendation = (
            "Model is not capturing patterns well. Consider: "
            "increasing max_depth, adding more features, "
            "or reducing regularization."
        )
    else:
        status = "healthy"
        recommendation = "Model generalizes well. No changes needed."

    return {
        "ratio": ratio,
        "status": status,
        "recommendation": recommendation,
    }


def run_diagnostics(
    position: str,
    target: str,
    train_df: pl.DataFrame,
    test_df: pl.DataFrame,
    feature_cols: list[str],
) -> dict[str, Any]:
    """Run complete diagnostics for a single model.

    Loads the model, prepares data, computes train and test metrics,
    and diagnoses overfitting status.

    Args:
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").
        train_df: Training DataFrame with features and target.
        test_df: Test DataFrame with features and target.
        feature_cols: List of feature column names.

    Returns:
        Comprehensive dict with:
        - position: str
        - target: str
        - train_metrics: dict with train_mae, train_rmse, train_r2
        - test_metrics: dict with test_mae, test_rmse, test_r2
        - overfit_ratio: float
        - diagnosis: dict with status and recommendation
        - n_train: int - number of training samples
        - n_test: int - number of test samples

    Example:
        >>> result = run_diagnostics("QB", "passing_yards", train_df, test_df, features)
        >>> result["diagnosis"]["status"]
        'healthy'
    """
    # Load model
    model, metadata = load_model(position, target)

    # Filter dataframes to position
    train_pos = train_df.filter(pl.col("position") == position)
    test_pos = test_df.filter(pl.col("position") == position)

    # Drop rows with missing values in target or features
    cols_needed = feature_cols + [target]
    train_pos = train_pos.drop_nulls(cols_needed)
    test_pos = test_pos.drop_nulls(cols_needed)

    # Prepare feature matrices and targets
    X_train = train_pos.select(feature_cols).to_numpy()
    y_train = train_pos.select(target).to_numpy().flatten()
    X_test = test_pos.select(feature_cols).to_numpy()
    y_test = test_pos.select(target).to_numpy().flatten()

    # Compute train metrics
    train_metrics = compute_train_metrics(model, X_train, y_train)

    # Compute test metrics
    y_pred_test = model.predict(X_test)
    test_metrics = {
        "test_mae": float(mean_absolute_error(y_test, y_pred_test)),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
        "test_r2": float(r2_score(y_test, y_pred_test)),
    }

    # Compute overfit ratio and diagnosis
    overfit_ratio = compute_overfit_ratio(
        train_metrics["train_rmse"], test_metrics["test_rmse"]
    )
    diagnosis = diagnose_overfitting(
        train_metrics["train_rmse"], test_metrics["test_rmse"]
    )

    logger.info(
        f"{position}/{target}: train_rmse={train_metrics['train_rmse']:.2f}, "
        f"test_rmse={test_metrics['test_rmse']:.2f}, "
        f"ratio={overfit_ratio:.2f}, status={diagnosis['status']}"
    )

    return {
        "position": position,
        "target": target,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "overfit_ratio": overfit_ratio,
        "diagnosis": diagnosis,
        "n_train": len(train_pos),
        "n_test": len(test_pos),
    }


def run_all_diagnostics(
    train_df: pl.DataFrame,
    test_df: pl.DataFrame,
    feature_cols: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Run diagnostics for all saved models.

    Args:
        train_df: Training DataFrame with features and targets.
        test_df: Test DataFrame with features and targets.
        feature_cols: List of feature column names. If None, uses default
            from get_feature_columns().

    Returns:
        List of diagnostic results, one per model.

    Example:
        >>> results = run_all_diagnostics(train_df, test_df)
        >>> len(results) > 0
        True
        >>> all("diagnosis" in r for r in results)
        True
    """
    # Get feature columns if not provided
    if feature_cols is None:
        from lineupiq.features.pipeline import get_feature_columns

        feature_cols = get_feature_columns()

    # Get all saved models
    models = list_models()

    if not models:
        logger.warning("No saved models found")
        return []

    logger.info(f"Running diagnostics for {len(models)} models")

    results = []
    for position, target in models:
        try:
            result = run_diagnostics(
                position, target, train_df, test_df, feature_cols
            )
            results.append(result)
        except FileNotFoundError:
            logger.warning(f"Model not found: {position}/{target}")
        except Exception as e:
            logger.error(f"Error diagnosing {position}/{target}: {e}")
            results.append({
                "position": position,
                "target": target,
                "error": str(e),
            })

    # Summary log
    statuses = [r.get("diagnosis", {}).get("status", "error") for r in results]
    healthy = sum(1 for s in statuses if s == "healthy")
    overfitting = sum(1 for s in statuses if s == "overfitting")
    underfitting = sum(1 for s in statuses if s == "underfitting")
    errors = sum(1 for s in statuses if s == "error")

    logger.info(
        f"Diagnostics complete: {healthy} healthy, {overfitting} overfitting, "
        f"{underfitting} underfitting, {errors} errors"
    )

    return results
