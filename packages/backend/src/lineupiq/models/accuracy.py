"""
Accuracy metrics for model-level confidence and user-facing summaries.

Provides functions for computing model accuracy percentages and confidence
tiers that can be displayed to users to build trust in predictions.

Key functions:
- calculate_model_accuracy: Compute comprehensive accuracy metrics from predictions
- calculate_confidence_rating: Convert metrics to user-friendly confidence tier
- summarize_backtest_results: Aggregate backtest results for API consumption
"""

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

logger = logging.getLogger(__name__)


def calculate_model_accuracy(
    predictions: NDArray[np.floating[Any]],
    actuals: NDArray[np.floating[Any]],
) -> dict[str, float]:
    """Calculate comprehensive accuracy metrics for model evaluation.

    Computes standard regression metrics plus user-friendly accuracy percentages:
    - MAE: Mean Absolute Error
    - RMSE: Root Mean Squared Error
    - R2: R-squared coefficient
    - accuracy_pct: 100 * R² (variance explained) - a 0-100% score
    - directional_accuracy: % of predictions with correct above/below mean direction

    Args:
        predictions: Array of predicted values.
        actuals: Array of actual values.

    Returns:
        Dict with mae, rmse, r2, accuracy_pct, directional_accuracy keys.

    Example:
        >>> preds = np.array([100, 200, 150])
        >>> acts = np.array([110, 190, 160])
        >>> metrics = calculate_model_accuracy(preds, acts)
        >>> "accuracy_pct" in metrics
        True
        >>> 0 <= metrics["accuracy_pct"] <= 100
        True
    """
    # Standard regression metrics
    mae = mean_absolute_error(actuals, predictions)
    rmse = root_mean_squared_error(actuals, predictions)
    r2 = r2_score(actuals, predictions)

    # R²-based accuracy: Directly represents variance explained (0-100%)
    # Clamped to [0, 100] range (R² can be negative for very poor models)
    accuracy_pct = max(0.0, min(100.0, 100.0 * r2))

    # Directional accuracy: % of predictions where direction matches actual
    # Direction = above or below the mean
    mean_actual = np.mean(actuals)
    pred_direction = predictions >= mean_actual
    actual_direction = actuals >= mean_actual
    directional_matches = pred_direction == actual_direction
    directional_accuracy = 100.0 * np.mean(directional_matches)

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "accuracy_pct": float(accuracy_pct),
        "directional_accuracy": float(directional_accuracy),
    }


def calculate_confidence_rating(r2: float, accuracy_pct: float) -> str:
    """Convert metrics to user-friendly confidence tier.

    Provides a simple High/Medium/Low rating based on model performance.
    This helps users understand how much to trust predictions without
    needing to interpret statistical metrics.

    Args:
        r2: R-squared score from model evaluation.
        accuracy_pct: Accuracy percentage from calculate_model_accuracy.

    Returns:
        Confidence tier: "High", "Medium", or "Low".

    Example:
        >>> calculate_confidence_rating(0.6, 85.0)
        'High'
        >>> calculate_confidence_rating(0.4, 70.0)
        'Medium'
        >>> calculate_confidence_rating(0.1, 50.0)
        'Low'
    """
    # High confidence: Strong R2 and good accuracy
    if r2 > 0.5 and accuracy_pct > 80.0:
        return "High"

    # Medium confidence: Reasonable R2 or reasonable accuracy
    if r2 > 0.3 or accuracy_pct > 70.0:
        return "Medium"

    # Low confidence: Poor metrics
    return "Low"


def summarize_backtest_results(backtest_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate backtest results for API consumption.

    Processes results from run_all_backtests to produce a summary
    structured for easy frontend display, including overall accuracy
    and per-model breakdowns.

    Args:
        backtest_results: List of backtest result dicts from run_all_backtests.
            Each dict should have predictions, actuals, position, target.

    Returns:
        Dict with structure:
        {
            "overall_accuracy_pct": float,
            "overall_confidence": str,  # High/Medium/Low
            "total_models": int,
            "total_predictions": int,
            "by_model": [
                {
                    "position": str,
                    "target": str,
                    "accuracy_pct": float,
                    "directional_accuracy": float,
                    "r2": float,
                    "mae": float,
                    "rmse": float,
                    "confidence": str,
                    "sample_count": int,
                },
                ...
            ]
        }

    Example:
        >>> summary = summarize_backtest_results(backtest_results)
        >>> "overall_accuracy_pct" in summary
        True
        >>> isinstance(summary["by_model"], list)
        True
    """
    if not backtest_results:
        return {
            "overall_accuracy_pct": 0.0,
            "overall_confidence": "Low",
            "total_models": 0,
            "total_predictions": 0,
            "by_model": [],
        }

    # Calculate metrics for each model
    model_summaries = []
    all_predictions = []
    all_actuals = []

    for result in backtest_results:
        predictions = result["predictions"]
        actuals = result["actuals"]

        # Accumulate for overall metrics
        all_predictions.extend(predictions.tolist())
        all_actuals.extend(actuals.tolist())

        # Calculate model-specific metrics
        metrics = calculate_model_accuracy(predictions, actuals)
        confidence = calculate_confidence_rating(metrics["r2"], metrics["accuracy_pct"])

        model_summary = {
            "position": result["position"],
            "target": result["target"],
            "accuracy_pct": round(metrics["accuracy_pct"], 1),
            "directional_accuracy": round(metrics["directional_accuracy"], 1),
            "r2": round(metrics["r2"], 3),
            "mae": round(metrics["mae"], 2),
            "rmse": round(metrics["rmse"], 2),
            "confidence": confidence,
            "sample_count": result["n_samples"],
        }
        model_summaries.append(model_summary)

    # Calculate overall metrics across all models
    all_predictions_arr = np.array(all_predictions)
    all_actuals_arr = np.array(all_actuals)

    overall_metrics = calculate_model_accuracy(all_predictions_arr, all_actuals_arr)
    overall_confidence = calculate_confidence_rating(
        overall_metrics["r2"], overall_metrics["accuracy_pct"]
    )

    return {
        "overall_accuracy_pct": round(overall_metrics["accuracy_pct"], 1),
        "overall_confidence": overall_confidence,
        "total_models": len(backtest_results),
        "total_predictions": len(all_predictions),
        "by_model": model_summaries,
    }
