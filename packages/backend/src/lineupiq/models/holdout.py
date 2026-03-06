"""
Holdout validation utilities for training models on historical data and predicting future seasons.

This module provides infrastructure for holdout validation, where models are trained
on a subset of seasons (e.g., 2022-2024) and evaluated on a completely unseen
holdout season (e.g., 2025). This approach:

1. Proves model quality on truly out-of-sample data
2. Prevents data leakage (holdout season never seen during training)
3. Much faster than walk-forward validation (~20x speedup)
4. Scientifically equivalent for establishing prediction accuracy

Key functions:
- train_holdout_models: Train all 32 models using only specified training seasons
- predict_season: Generate predictions for all weeks of a holdout season
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import NDArray

from lineupiq.data.defense_processing import get_defense_target_columns
from lineupiq.data.kicker_processing import get_kicker_target_columns
from lineupiq.features.pipeline import build_features
from lineupiq.models.qb import QB_TARGETS
from lineupiq.models.rb import RB_TARGETS
from lineupiq.models.receiver import RECEIVER_TARGETS
from lineupiq.models.persistence import MODELS_DIR, load_model

logger = logging.getLogger(__name__)

# All position-target combinations (32 total models)
POSITION_TARGETS = {
    "QB": QB_TARGETS,
    "RB": RB_TARGETS,
    "WR": RECEIVER_TARGETS,
    "TE": RECEIVER_TARGETS,
    "K": get_kicker_target_columns(),
    "DEF": get_defense_target_columns(),
}


def train_holdout_models(
    train_seasons: list[int],
    positions: list[str] | None = None,
    n_trials: int = 30,
    output_dir: str = "models_holdout",
) -> dict[str, Path]:
    """Train all models using data from specified training seasons only.

    This function trains models on a restricted set of seasons (e.g., 2022-2024)
    so they can be validated on a completely unseen holdout season (e.g., 2025).
    Models are saved to a separate directory to avoid overwriting production models.

    Args:
        train_seasons: List of seasons to train on (e.g., [2022, 2023, 2024]).
        positions: List of positions to train (default: all 6 positions).
        n_trials: Number of Optuna trials for hyperparameter tuning (default: 30).
        output_dir: Directory name for saved models (default: "models_holdout").

    Returns:
        Dict mapping "{position}_{target}" to model file path.

    Raises:
        ValueError: If train_seasons is empty or contains invalid years.

    Example:
        >>> # Train models on 2022-2024 data only (never see 2025)
        >>> model_paths = train_holdout_models(
        ...     train_seasons=[2022, 2023, 2024],
        ...     positions=["QB", "RB"],
        ...     n_trials=10
        ... )
        >>> "QB_passing_yards" in model_paths
        True
    """
    if not train_seasons:
        raise ValueError("train_seasons cannot be empty")

    if positions is None:
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    logger.info("=" * 80)
    logger.info("HOLDOUT MODEL TRAINING")
    logger.info("=" * 80)
    logger.info(f"Training seasons: {train_seasons}")
    logger.info(f"Positions: {', '.join(positions)}")
    logger.info(f"Optuna trials: {n_trials}")
    logger.info(f"Output directory: packages/backend/{output_dir}/")
    logger.info("=" * 80)

    # Create output directory
    output_path = MODELS_DIR.parent / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    # Temporarily modify MODELS_DIR to point to holdout directory
    # This ensures save_model() writes to the correct location
    import lineupiq.models.persistence as persistence_module
    original_models_dir = persistence_module.MODELS_DIR
    persistence_module.MODELS_DIR = output_path

    try:
        model_paths: dict[str, Path] = {}

        for position in positions:
            if position not in POSITION_TARGETS:
                logger.warning(f"Unknown position: {position}, skipping")
                continue

            logger.info(f"\n{'=' * 80}")
            logger.info(f"TRAINING {position} MODELS ({len(POSITION_TARGETS[position])} targets)")
            logger.info(f"{'=' * 80}")

            # Import position-specific training function
            if position == "QB":
                from lineupiq.models.qb import train_qb_models
                results = train_qb_models(seasons=train_seasons, n_trials=n_trials)
            elif position == "RB":
                from lineupiq.models.rb import train_rb_models
                results = train_rb_models(seasons=train_seasons, n_trials=n_trials)
            elif position == "WR":
                from lineupiq.models.receiver import train_wr_models
                results = train_wr_models(seasons=train_seasons, n_trials=n_trials)
            elif position == "TE":
                from lineupiq.models.receiver import train_te_models
                results = train_te_models(seasons=train_seasons, n_trials=n_trials)
            elif position == "K":
                from lineupiq.models.kicker import train_kicker_models
                results = train_kicker_models(seasons=train_seasons, n_trials=n_trials)
            elif position == "DEF":
                from lineupiq.models.defense import train_defense_models
                results = train_defense_models(seasons=train_seasons, n_trials=n_trials)
            else:
                continue

            # Record model paths
            for target in results.keys():
                model_key = f"{position}_{target}"
                model_paths[model_key] = output_path / f"{model_key}.joblib"

            logger.info(f"✓ {position} training complete ({len(results)} models)")

        logger.info(f"\n{'=' * 80}")
        logger.info(f"HOLDOUT TRAINING COMPLETE")
        logger.info(f"{'=' * 80}")
        logger.info(f"Total models trained: {len(model_paths)}")
        logger.info(f"Models saved to: {output_path}")
        logger.info(f"{'=' * 80}")

        return model_paths

    finally:
        # Restore original MODELS_DIR
        persistence_module.MODELS_DIR = original_models_dir


def predict_season(
    season: int,
    model_dir: str,
    positions: list[str] | None = None,
    weeks: list[int] | None = None,
) -> pl.DataFrame:
    """Predict all available weeks of a season using models from model_dir.

    Loads player data for the specified season, computes features, and generates
    predictions using models from the specified directory. This allows validation
    on a completely unseen season (e.g., predict 2025 using models trained on 2022-2024).

    Args:
        season: Season year to predict (e.g., 2025).
        model_dir: Directory containing trained models (e.g., "models_holdout").
        positions: List of positions to predict (default: all).
        weeks: List of weeks to predict (default: all available weeks).

    Returns:
        DataFrame with columns:
        - player_id: Player identifier
        - player_name: Player full name
        - position: Player position (QB, RB, WR, TE, K, DEF)
        - season: Season year
        - week: Week number
        - target: Target stat name (e.g., "passing_yards")
        - predicted_value: Model prediction
        - actual_value: Actual outcome from the game

    Raises:
        ValueError: If season data unavailable or models directory doesn't exist.
        FileNotFoundError: If model files missing from model_dir.

    Example:
        >>> # Predict entire 2025 season using holdout models
        >>> predictions_df = predict_season(
        ...     season=2025,
        ...     model_dir="models_holdout",
        ...     positions=["QB", "RB"]
        ... )
        >>> "predicted_value" in predictions_df.columns
        True
        >>> "actual_value" in predictions_df.columns
        True
    """
    logger.info("=" * 80)
    logger.info(f"PREDICTING SEASON {season}")
    logger.info("=" * 80)
    logger.info(f"Model directory: packages/backend/{model_dir}/")
    logger.info(f"Positions: {positions or 'all'}")
    logger.info(f"Weeks: {weeks or 'all available'}")
    logger.info("=" * 80)

    # Validate model directory exists
    model_path = MODELS_DIR.parent / model_dir
    if not model_path.exists():
        raise ValueError(f"Model directory does not exist: {model_path}")

    if positions is None:
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    # Load feature data for the season
    # Need prior season for rolling feature computation
    logger.info(f"Loading data for seasons {[season - 1, season]} (need prior season for rolling stats)")
    try:
        df_all = build_features([season - 1, season])
    except Exception as e:
        raise ValueError(f"Failed to load data for season {season}: {e}")

    # Filter to target season only
    df_season = df_all.filter(pl.col("season") == season)

    if len(df_season) == 0:
        raise ValueError(
            f"No data available for season {season}. "
            f"The season may not have started yet or data is not available."
        )

    # Filter by weeks if specified
    if weeks is not None:
        df_season = df_season.filter(pl.col("week").is_in(weeks))
        if len(df_season) == 0:
            raise ValueError(f"No data for weeks {weeks} in season {season}")

    logger.info(f"Loaded {len(df_season)} player-week observations for season {season}")

    # Temporarily modify MODELS_DIR to load from holdout directory
    import lineupiq.models.persistence as persistence_module
    original_models_dir = persistence_module.MODELS_DIR
    persistence_module.MODELS_DIR = model_path

    try:
        all_predictions = []

        # Process each position
        for position in positions:
            if position not in POSITION_TARGETS:
                logger.warning(f"Unknown position: {position}, skipping")
                continue

            # Import position-specific data preparation
            if position == "QB":
                from lineupiq.models.qb import prepare_qb_data, QB_TARGETS
                from lineupiq.features.pipeline import get_feature_columns

                pos_df = df_season.filter(pl.col("position") == "QB")
                if len(pos_df) == 0:
                    logger.info(f"No {position} data for season {season}")
                    continue

                # Add derived columns for QB
                pos_df = pos_df.with_columns(
                    pl.col("passing_interceptions").fill_null(0).alias("interceptions"),
                    (
                        pl.col("sack_fumbles_lost").fill_null(0)
                        + pl.col("rushing_fumbles_lost").fill_null(0)
                    ).alias("fumbles_lost"),
                )
                targets = QB_TARGETS
                feature_cols = get_feature_columns()

            elif position == "RB":
                from lineupiq.models.rb import RB_TARGETS
                from lineupiq.features.pipeline import get_feature_columns

                pos_df = df_season.filter(pl.col("position") == "RB")
                if len(pos_df) == 0:
                    logger.info(f"No {position} data for season {season}")
                    continue

                # Add derived columns for RB
                pos_df = pos_df.with_columns(
                    (
                        pl.col("rushing_fumbles_lost").fill_null(0)
                        + pl.col("receiving_fumbles_lost").fill_null(0)
                    ).alias("fumbles_lost")
                )
                targets = RB_TARGETS
                feature_cols = get_feature_columns()

            elif position in ["WR", "TE"]:
                from lineupiq.models.receiver import RECEIVER_TARGETS
                from lineupiq.features.pipeline import get_feature_columns

                pos_df = df_season.filter(pl.col("position") == position)
                if len(pos_df) == 0:
                    logger.info(f"No {position} data for season {season}")
                    continue

                # Add derived columns for receivers
                pos_df = pos_df.with_columns(
                    pl.col("receiving_fumbles_lost").fill_null(0).alias("fumbles_lost")
                )
                targets = RECEIVER_TARGETS
                feature_cols = get_feature_columns()

            elif position == "K":
                from lineupiq.data.kicker_processing import process_kicker_data, get_kicker_feature_columns, get_kicker_target_columns

                # Kicker data requires separate processing
                logger.info(f"Processing kicker data for season {season}")
                kicker_df = process_kicker_data([season - 1, season])
                pos_df = kicker_df.filter(pl.col("season") == season)

                if weeks is not None:
                    pos_df = pos_df.filter(pl.col("week").is_in(weeks))

                if len(pos_df) == 0:
                    logger.info(f"No {position} data for season {season}")
                    continue

                targets = get_kicker_target_columns()
                feature_cols = get_kicker_feature_columns()

            elif position == "DEF":
                from lineupiq.data.defense_processing import process_defense_data, get_defense_feature_columns, get_defense_target_columns

                # Defense data requires separate processing
                logger.info(f"Processing defense data for season {season}")
                defense_df = process_defense_data([season - 1, season])
                pos_df = defense_df.filter(pl.col("season") == season)

                if weeks is not None:
                    pos_df = pos_df.filter(pl.col("week").is_in(weeks))

                if len(pos_df) == 0:
                    logger.info(f"No {position} data for season {season}")
                    continue

                targets = get_defense_target_columns()
                feature_cols = get_defense_feature_columns()

            else:
                continue

            # Drop rows with null values in features or targets
            all_required_cols = feature_cols + targets
            available_cols = [c for c in all_required_cols if c in pos_df.columns]
            pos_df = pos_df.drop_nulls(subset=available_cols)

            if len(pos_df) == 0:
                logger.info(f"No valid {position} data after dropping nulls")
                continue

            logger.info(f"Predicting {position}: {len(pos_df)} observations, {len(targets)} targets")

            # Extract metadata columns
            metadata_cols = ["player_id", "player_name", "season", "week"]
            if position == "DEF":
                # Defense uses team as identifier
                metadata_cols = ["team", "season", "week"]

            available_meta = [c for c in metadata_cols if c in pos_df.columns]
            metadata_df = pos_df.select(available_meta)

            # Generate predictions for each target
            for target in targets:
                model_key = f"{position}_{target}"
                model_file = model_path / f"{model_key}.joblib"

                if not model_file.exists():
                    logger.warning(f"Model not found: {model_file}, skipping")
                    continue

                try:
                    # Load model
                    model, _ = load_model(position, target)

                    # Prepare features
                    X = pos_df.select(feature_cols).to_numpy().astype(np.float64)

                    # Get actual values
                    if target not in pos_df.columns:
                        logger.warning(f"Target column '{target}' not in data for {position}, skipping")
                        continue

                    y_actual = pos_df.select(target).to_numpy().flatten().astype(np.float64)

                    # Generate predictions
                    y_pred = model.predict(X)

                    # Build prediction records
                    for i in range(len(y_pred)):
                        record = {
                            "position": position,
                            "season": season,
                            "target": target,
                            "predicted_value": float(y_pred[i]),
                            "actual_value": float(y_actual[i]),
                        }

                        # Add metadata
                        meta_row = metadata_df.row(i, named=True)

                        if position == "DEF":
                            record["player_id"] = meta_row.get("team", "")
                            record["player_name"] = meta_row.get("team", "")
                        else:
                            record["player_id"] = meta_row.get("player_id", "")
                            record["player_name"] = meta_row.get("player_name", "")

                        record["week"] = meta_row.get("week", 0)

                        all_predictions.append(record)

                except Exception as e:
                    logger.error(f"Error predicting {model_key}: {e}")
                    continue

            logger.info(f"✓ {position} predictions complete")

        # Convert to DataFrame
        if not all_predictions:
            raise ValueError(f"No predictions generated for season {season}")

        predictions_df = pl.DataFrame(all_predictions)

        logger.info(f"\n{'=' * 80}")
        logger.info(f"PREDICTION COMPLETE")
        logger.info(f"{'=' * 80}")
        logger.info(f"Total predictions: {len(predictions_df)}")
        logger.info(f"Positions: {predictions_df['position'].unique().to_list()}")
        logger.info(f"Weeks: {sorted(predictions_df['week'].unique().to_list())}")
        logger.info(f"{'=' * 80}")

        return predictions_df

    finally:
        # Restore original MODELS_DIR
        persistence_module.MODELS_DIR = original_models_dir
