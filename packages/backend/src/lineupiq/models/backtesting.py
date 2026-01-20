"""
Backtesting utilities for validating trained models on holdout data.

Provides functions for running predictions on holdout seasons (e.g., 2025)
that were not seen during training, allowing true out-of-sample validation.

Key functions:
- load_holdout_data: Load and process a holdout season through the feature pipeline
- load_kicker_holdout_data: Load kicker holdout data for backtesting
- load_defense_holdout_data: Load defense holdout data for backtesting
- run_backtest: Run a single model on holdout data and collect predictions vs actuals
- run_all_backtests: Run all trained models on holdout data
- run_kicker_backtests: Run backtests for all kicker models
- run_defense_backtests: Run backtests for all defense models
"""

import logging
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray

from lineupiq.data.defense_processing import (
    get_defense_feature_columns,
    get_defense_target_columns,
    process_defense_data,
)
from lineupiq.data.kicker_processing import (
    get_kicker_feature_columns,
    get_kicker_target_columns,
    process_kicker_data,
)
from lineupiq.features.pipeline import build_features, get_feature_columns
from lineupiq.models.ensemble import load_ensemble
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
        position: Player position (e.g., "QB", "RB", "WR", "TE", "K", "DEF").
        target: Target stat (e.g., "passing_yards", "rushing_tds", "fg_att").
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

    # Try to load ensemble model first (preferred), fall back to single model
    try:
        model = load_ensemble(position, target, "voting_weighted")
        logger.debug(f"Using ensemble model for {position}_{target}")
        model_metadata = {}  # Ensembles don't have metadata dict
    except FileNotFoundError:
        # Fall back to single model if ensemble not available
        model, model_metadata = load_model(position, target)
        logger.debug(f"Using single model for {position}_{target}")

    # Get feature columns based on position
    if position == "K":
        feature_cols = get_kicker_feature_columns()
    elif position == "DEF":
        feature_cols = get_defense_feature_columns()
    else:
        feature_cols = get_feature_columns()  # Skill positions

    # Filter holdout data based on position type
    if position == "K":
        # Kicker data doesn't have position column - use all data
        pos_df = holdout_df
    elif position == "DEF":
        # Defense data doesn't have position column - use all data
        pos_df = holdout_df
    else:
        # Skill positions filter by position column
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

    Note: Only backtests base models (excludes XGBoost variants and ensemble models).
    The API loader will automatically use ensemble models if available when loading
    the base model name.

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
    all_models = list_models()

    # Filter to only base models (exclude XGBoost variants and ensemble models)
    # This prevents trying to backtest "_xgb" and "_voting_weighted" models directly
    base_models = [
        (pos, target) for pos, target in all_models
        if not target.endswith("_xgb")
        and not target.endswith("_voting_weighted")
        and not target.endswith("_voting_simple")
        and not target.endswith("_stacking")
    ]

    logger.info(f"Running backtests for {len(base_models)} base models (from {len(all_models)} total saved models)")

    results = []
    for position, target in base_models:
        try:
            result = run_backtest(position, target, holdout_df)
            results.append(result)
        except FileNotFoundError as e:
            logger.warning(f"Model not found: {position}_{target}: {e}")
        except ValueError as e:
            logger.warning(f"Cannot backtest {position}_{target}: {e}")
        except Exception as e:
            logger.error(f"Error running backtest for {position}_{target}: {e}")

    logger.info(f"Successfully ran {len(results)}/{len(base_models)} backtests")
    return results


def load_kicker_holdout_data(season: int = 2025) -> pl.DataFrame:
    """Load kicker holdout data for backtesting.

    Processes kicker data through the kicker feature pipeline for the specified
    holdout season. Includes prior season for rolling feature computation.

    Args:
        season: Holdout season year (default: 2025).

    Returns:
        DataFrame with kicker features and targets for the holdout season.

    Raises:
        ValueError: If no kicker data available for the season.

    Example:
        >>> kicker_df = load_kicker_holdout_data(2025)
        >>> "fg_att_roll3" in kicker_df.columns
        True
    """
    logger.info(f"Loading kicker holdout data for season {season}")

    # Need prior season for rolling features
    df = process_kicker_data([season - 1, season])

    # Filter to holdout season
    holdout = df.filter(pl.col("season") == season)

    if len(holdout) == 0:
        raise ValueError(f"No kicker data for season {season}")

    logger.info(f"Loaded {len(holdout)} kicker holdout rows")
    return holdout


def load_defense_holdout_data(season: int = 2025) -> pl.DataFrame:
    """Load defense holdout data for backtesting.

    Processes team defense data through the defense feature pipeline for the
    specified holdout season. Includes prior season for rolling feature computation.

    Args:
        season: Holdout season year (default: 2025).

    Returns:
        DataFrame with defense features and targets for the holdout season.

    Raises:
        ValueError: If no defense data available for the season.

    Example:
        >>> defense_df = load_defense_holdout_data(2025)
        >>> "points_allowed_roll3" in defense_df.columns
        True
    """
    logger.info(f"Loading defense holdout data for season {season}")

    df = process_defense_data([season - 1, season])

    holdout = df.filter(pl.col("season") == season)

    if len(holdout) == 0:
        raise ValueError(f"No defense data for season {season}")

    logger.info(f"Loaded {len(holdout)} defense holdout rows")
    return holdout


def run_kicker_backtests(holdout_df: pl.DataFrame) -> list[dict[str, Any]]:
    """Run backtests for all kicker models.

    Iterates through kicker target stats, runs backtests, and collects results.

    Args:
        holdout_df: Kicker holdout DataFrame from load_kicker_holdout_data.

    Returns:
        List of backtest result dicts for kicker models.

    Example:
        >>> kicker_holdout = load_kicker_holdout_data(2025)
        >>> results = run_kicker_backtests(kicker_holdout)
        >>> all(r["position"] == "K" for r in results)
        True
    """
    target_cols = get_kicker_target_columns()
    logger.info(f"Running kicker backtests for {len(target_cols)} targets")

    results = []
    for target in target_cols:
        try:
            result = run_backtest("K", target, holdout_df)
            results.append(result)
        except Exception as e:
            logger.warning(f"Cannot backtest K_{target}: {e}")

    logger.info(f"Successfully ran {len(results)}/{len(target_cols)} kicker backtests")
    return results


def run_defense_backtests(holdout_df: pl.DataFrame) -> list[dict[str, Any]]:
    """Run backtests for all defense models.

    Iterates through defense target stats, runs backtests, and collects results.

    Args:
        holdout_df: Defense holdout DataFrame from load_defense_holdout_data.

    Returns:
        List of backtest result dicts for defense models.

    Example:
        >>> defense_holdout = load_defense_holdout_data(2025)
        >>> results = run_defense_backtests(defense_holdout)
        >>> all(r["position"] == "DEF" for r in results)
        True
    """
    target_cols = get_defense_target_columns()
    logger.info(f"Running defense backtests for {len(target_cols)} targets")

    results = []
    for target in target_cols:
        try:
            result = run_backtest("DEF", target, holdout_df)
            results.append(result)
        except Exception as e:
            logger.warning(f"Cannot backtest DEF_{target}: {e}")

    logger.info(f"Successfully ran {len(results)}/{len(target_cols)} defense backtests")
    return results
