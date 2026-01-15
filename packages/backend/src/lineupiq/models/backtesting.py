"""
Backtesting utilities for validating trained models on holdout data.

Provides functions for running predictions on holdout seasons (e.g., 2025)
that were not seen during training, allowing true out-of-sample validation.

Key functions:
- load_holdout_data: Load and process a holdout season through the feature pipeline
- run_backtest: Run a single model on holdout data and collect predictions vs actuals
- run_all_backtests: Run all trained models on holdout data
"""

import logging
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray

from lineupiq.features.pipeline import build_features, get_feature_columns
from lineupiq.models.persistence import list_models, load_model

logger = logging.getLogger(__name__)


def load_holdout_data(season: int = 2025) -> pl.DataFrame:
    """Load and process holdout season data through the feature pipeline.

    Fetches data for the specified holdout season and processes it through
    the full feature pipeline (rolling stats, opponent features, etc.).
    This data should NOT have been used during model training.

    Args:
        season: Holdout season year (default: 2025).

    Returns:
        DataFrame with features and actual outcomes for the holdout season.

    Raises:
        ValueError: If holdout data is empty or unavailable.

    Example:
        >>> holdout_df = load_holdout_data(2025)
        >>> "passing_yards" in holdout_df.columns
        True
        >>> holdout_df["season"].unique().to_list()
        [2025]
    """
    logger.info(f"Loading holdout data for season {season}")

    try:
        # Build features for the holdout season
        # Need to include prior season for rolling stat computation
        seasons_to_load = [season - 1, season]
        df = build_features(seasons_to_load)

        # Filter to only the holdout season
        holdout_df = df.filter(pl.col("season") == season)

        if len(holdout_df) == 0:
            raise ValueError(
                f"No data available for holdout season {season}. "
                f"The season may not have started yet or data is not available."
            )

        logger.info(
            f"Loaded holdout data: {len(holdout_df)} rows for season {season}"
        )

        return holdout_df

    except Exception as e:
        logger.error(f"Failed to load holdout data for season {season}: {e}")
        raise


def run_backtest(
    position: str,
    target: str,
    holdout_df: pl.DataFrame,
) -> dict[str, Any]:
    """Run backtest for a single position/target model on holdout data.

    Loads the trained model, generates predictions for all games in the
    holdout data, and returns predictions alongside actuals and metadata.

    Args:
        position: Player position (e.g., "QB", "RB", "WR", "TE").
        target: Target stat (e.g., "passing_yards", "rushing_tds").
        holdout_df: Holdout DataFrame with features and target column.

    Returns:
        Dict containing:
        - position: str - Player position
        - target: str - Target stat name
        - predictions: NDArray - Predicted values
        - actuals: NDArray - Actual values
        - n_samples: int - Number of samples
        - metadata: list[dict] - Per-prediction metadata (player_id, week, opponent)

    Raises:
        FileNotFoundError: If model file doesn't exist.
        ValueError: If no samples for position or missing columns.

    Example:
        >>> result = run_backtest("QB", "passing_yards", holdout_df)
        >>> result["position"]
        'QB'
        >>> len(result["predictions"]) == result["n_samples"]
        True
    """
    logger.info(f"Running backtest for {position}_{target}")

    # Load trained model
    model, model_metadata = load_model(position, target)

    # Get feature columns
    feature_cols = get_feature_columns()

    # Filter holdout data to this position
    pos_df = holdout_df.filter(pl.col("position") == position)

    if len(pos_df) == 0:
        raise ValueError(f"No holdout samples for position {position}")

    # Verify target column exists
    if target not in pos_df.columns:
        raise ValueError(f"Target column '{target}' not in holdout data")

    # Verify all feature columns exist
    missing_cols = [c for c in feature_cols if c not in pos_df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns: {missing_cols}")

    # Prepare feature matrix
    X = pos_df.select(feature_cols).to_numpy()

    # Get actual values
    y_actual: NDArray[np.floating[Any]] = pos_df.select(target).to_numpy().flatten()

    # Generate predictions
    y_pred: NDArray[np.floating[Any]] = model.predict(X)

    # Collect metadata for each prediction
    metadata_cols = ["player_id", "week", "opponent"]
    available_meta_cols = [c for c in metadata_cols if c in pos_df.columns]

    prediction_metadata = []
    if available_meta_cols:
        meta_df = pos_df.select(available_meta_cols)
        for row in meta_df.iter_rows(named=True):
            prediction_metadata.append(row)

    result = {
        "position": position,
        "target": target,
        "predictions": y_pred,
        "actuals": y_actual,
        "n_samples": len(y_actual),
        "metadata": prediction_metadata,
    }

    logger.info(
        f"Backtest {position}_{target}: {result['n_samples']} predictions generated"
    )

    return result


def run_all_backtests(holdout_df: pl.DataFrame) -> list[dict[str, Any]]:
    """Run backtests for all trained models on holdout data.

    Iterates through all saved models, runs backtests, and collects results.
    Handles errors gracefully, logging warnings for failed models.

    Args:
        holdout_df: Holdout DataFrame with features and target columns.

    Returns:
        List of backtest result dicts from run_backtest.

    Example:
        >>> results = run_all_backtests(holdout_df)
        >>> len(results) > 0
        True
        >>> all("predictions" in r for r in results)
        True
    """
    models = list_models()
    logger.info(f"Running backtests for {len(models)} trained models")

    results = []
    for position, target in models:
        try:
            result = run_backtest(position, target, holdout_df)
            results.append(result)
        except FileNotFoundError as e:
            logger.warning(f"Model not found: {position}_{target}: {e}")
        except ValueError as e:
            logger.warning(f"Cannot backtest {position}_{target}: {e}")
        except Exception as e:
            logger.error(f"Error running backtest for {position}_{target}: {e}")

    logger.info(f"Successfully ran {len(results)}/{len(models)} backtests")
    return results
