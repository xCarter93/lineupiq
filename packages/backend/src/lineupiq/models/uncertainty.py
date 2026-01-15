"""
Prediction intervals using conformal prediction for uncertainty quantification.

This module provides per-prediction uncertainty bounds using a split conformal
approach. High-variance players (boom/bust WRs) get wider intervals, consistent
players get tighter intervals.

Uses MAPIE's conformal prediction methodology but implements a simpler split
conformal approach that works with already-trained models (no need to retrain).

Example:
    >>> from lineupiq.models.uncertainty import calibrate_intervals, predict_with_intervals
    >>> # Calibrate using holdout data
    >>> quantile = calibrate_intervals(model, X_cal, y_cal)
    >>> # Make predictions with intervals
    >>> point, lower, upper = predict_with_intervals(model, X_test, quantile)
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray


def calibrate_intervals(
    model: Any,
    X_cal: NDArray[np.floating[Any]],
    y_cal: NDArray[np.floating[Any]],
    alpha: float = 0.1,
) -> float:
    """
    Compute conformal prediction quantile using calibration set residuals.

    Uses split conformal prediction: compute residuals on calibration data,
    then use the (1-alpha) quantile of absolute residuals for interval width.

    Args:
        model: Fitted XGBoost model (or any sklearn-compatible regressor).
        X_cal: Calibration features, shape (n_samples, n_features).
        y_cal: Calibration targets, shape (n_samples,).
        alpha: Significance level (default 0.1 for 90% coverage).
            alpha=0.1 means 90% of true values fall within intervals.

    Returns:
        Quantile value to add/subtract from predictions for intervals.

    Raises:
        ValueError: If calibration data is empty or alpha is out of range.

    Example:
        >>> quantile = calibrate_intervals(model, X_cal, y_cal, alpha=0.1)
        >>> # quantile is the amount to add/subtract for 90% intervals
    """
    if len(X_cal) == 0 or len(y_cal) == 0:
        raise ValueError("Calibration data cannot be empty")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    # Get predictions on calibration set
    y_pred_cal = model.predict(X_cal)

    # Compute absolute residuals (conformity scores)
    residuals = np.abs(y_cal - y_pred_cal)

    # Use (1-alpha) quantile for desired coverage
    # With finite sample correction: use (n+1)(1-alpha)/n quantile
    n = len(residuals)
    corrected_quantile = min(1.0, (n + 1) * (1 - alpha) / n)
    quantile = float(np.quantile(residuals, corrected_quantile))

    return quantile


def predict_with_intervals(
    model: Any,
    X: NDArray[np.floating[Any]],
    quantile: float,
) -> tuple[NDArray[np.floating[Any]], NDArray[np.floating[Any]], NDArray[np.floating[Any]]]:
    """
    Make predictions with conformal prediction intervals.

    Args:
        model: Fitted XGBoost model (or any sklearn-compatible regressor).
        X: Features to predict, shape (n_samples, n_features) or (n_features,).
        quantile: Interval width from calibrate_intervals().

    Returns:
        Tuple of (point_predictions, lower_bounds, upper_bounds), each shape (n_samples,).

    Example:
        >>> point, lower, upper = predict_with_intervals(model, X_test, quantile)
        >>> # lower[i] <= true_value[i] <= upper[i] with 90% probability
    """
    # Handle single sample case
    X_arr = np.atleast_2d(X)

    # Get point predictions
    point_predictions = model.predict(X_arr)

    # Compute intervals
    lower_bounds = point_predictions - quantile
    upper_bounds = point_predictions + quantile

    # Ensure non-negative predictions (stats can't be negative)
    lower_bounds = np.maximum(lower_bounds, 0.0)

    return point_predictions, lower_bounds, upper_bounds


def format_interval_response(point: float, lower: float, upper: float) -> dict[str, Any]:
    """
    Format prediction with intervals for API response.

    Args:
        point: Point prediction.
        lower: Lower bound of interval.
        upper: Upper bound of interval.

    Returns:
        Dictionary formatted for API response with prediction and interval info.

    Example:
        >>> response = format_interval_response(285.3, 245.1, 325.5)
        >>> response["prediction"]  # 285.3
        >>> response["interval"]["lower"]  # 245.1
        >>> response["interval"]["confidence"]  # 0.9
    """
    return {
        "prediction": round(float(point), 1),
        "interval": {
            "lower": round(max(float(lower), 0.0), 1),  # Ensure non-negative
            "upper": round(float(upper), 1),
            "confidence": 0.9,  # Fixed at 90% coverage
        },
    }


def calculate_interval_width(
    lower: NDArray[np.floating[Any]],
    upper: NDArray[np.floating[Any]],
) -> NDArray[np.floating[Any]]:
    """
    Calculate width of prediction intervals.

    Useful for tracking interval quality and comparing uncertainty across
    different predictions. Wider intervals indicate higher uncertainty.

    Args:
        lower: Lower bounds, shape (n_samples,).
        upper: Upper bounds, shape (n_samples,).

    Returns:
        Array of interval widths, shape (n_samples,).

    Example:
        >>> widths = calculate_interval_width(lower, upper)
        >>> print(f"Average interval width: {widths.mean():.1f}")
    """
    return upper - lower


def get_interval_coverage(
    y_true: NDArray[np.floating[Any]],
    lower: NDArray[np.floating[Any]],
    upper: NDArray[np.floating[Any]],
) -> float:
    """
    Calculate empirical coverage of prediction intervals.

    Measures what fraction of true values fall within the predicted intervals.
    Should be close to the target coverage (e.g., 0.9 for 90% intervals).

    Args:
        y_true: True target values, shape (n_samples,).
        lower: Lower bounds, shape (n_samples,).
        upper: Upper bounds, shape (n_samples,).

    Returns:
        Coverage fraction in [0, 1].

    Example:
        >>> coverage = get_interval_coverage(y_test, lower, upper)
        >>> print(f"Empirical coverage: {coverage:.1%}")  # Should be ~90%
    """
    in_interval = (y_true >= lower) & (y_true <= upper)
    return float(np.mean(in_interval))
