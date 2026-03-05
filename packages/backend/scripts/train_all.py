#!/usr/bin/env python3
"""
Canonical training script for all LineupIQ models.

This is the single source of truth for retraining models. All other
training scripts should be considered deprecated.

Usage:
    # Train all positions with all 3 model types + ensembles (default)
    uv run python scripts/train_all.py

    # Quick training for testing (10 trials)
    uv run python scripts/train_all.py --quick

    # Train specific positions
    uv run python scripts/train_all.py --positions QB RB WR TE

    # Custom seasons
    uv run python scripts/train_all.py --seasons 2020 2021 2022 2023 2024 2025

    # Custom trial count
    uv run python scripts/train_all.py --trials 50

    # Train only LightGBM (no ensemble)
    uv run python scripts/train_all.py --model-types lightgbm --no-ensemble

Simulation Mode (for backtesting):
    # Train on 2022-2024 only (exclude 2025)
    uv run python scripts/train_all.py --seasons 2022 2023 2024

    # Train on 2022-2024 + first 3 weeks of 2025
    uv run python scripts/train_all.py --seasons 2022 2023 2024 2025 --target-season 2025 --include-weeks 1 2 3

    # Incrementally add weeks (simulate week-by-week advancement)
    uv run python scripts/train_all.py --seasons 2022 2023 2024 2025 --target-season 2025 --include-weeks 1
    uv run python scripts/train_all.py --seasons 2022 2023 2024 2025 --target-season 2025 --include-weeks 1 2
    uv run python scripts/train_all.py --seasons 2022 2023 2024 2025 --target-season 2025 --include-weeks 1 2 3
"""

import argparse
import logging
import sys
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from sklearn.model_selection import train_test_split

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Feature Caching
# =============================================================================
# Features are expensive to compute (40+ columns from raw NFL data).
# Caching them reduces training time by ~50-60% when training multiple positions.

@lru_cache(maxsize=2)
def get_cached_features(
    seasons_tuple: tuple[int, ...],
    rolling_window: int,
    target_season: int | None = None,
    include_weeks_tuple: tuple[int, ...] | None = None,
) -> pl.DataFrame:
    """Load features from cache or compute them once.

    Uses LRU cache to avoid recomputing features for each position.
    Features are computed once and shared across QB, RB, WR, TE training.

    Args:
        seasons_tuple: Tuple of seasons (hashable for caching).
        rolling_window: Rolling window size for feature engineering.
        target_season: If provided, filter this season to only include specific weeks.
        include_weeks_tuple: Weeks to include from target_season (required if target_season set).

    Returns:
        Feature DataFrame ready for model training.
    """
    from lineupiq.features.pipeline import build_features
    logger.info(f"Computing features for seasons {seasons_tuple} (will be cached)")
    df = build_features(list(seasons_tuple), rolling_window=rolling_window)

    # Filter target season to only include specified weeks
    if target_season is not None and include_weeks_tuple is not None:
        include_weeks = list(include_weeks_tuple)
        logger.info(f"Filtering season {target_season} to weeks {include_weeks}")

        # Keep all data from non-target seasons, plus only specified weeks from target season
        df = df.filter(
            (pl.col("season") != target_season) |
            ((pl.col("season") == target_season) & (pl.col("week").is_in(include_weeks)))
        )
        logger.info(f"After filtering: {len(df)} rows")

    return df


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train all LineupIQ prediction models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--positions",
        nargs="+",
        choices=["QB", "RB", "WR", "TE", "K", "DEF"],
        default=["QB", "RB", "WR", "TE", "K", "DEF"],
        help="Positions to train (default: all)"
    )

    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        default=[2022, 2023, 2024, 2025],
        help="Seasons to train on (default: 2022-2025)"
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=50,
        help="Number of Optuna trials for hyperparameter tuning (default: 50)"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick training mode (10 trials, useful for testing)"
    )

    # --model-types (plural, new default: all three)
    parser.add_argument(
        "--model-types",
        nargs="+",
        choices=["lightgbm", "xgboost", "catboost"],
        default=["lightgbm", "xgboost", "catboost"],
        help="Model types to train (default: all three)"
    )

    # --model-type (singular, deprecated alias)
    parser.add_argument(
        "--model-type",
        choices=["lightgbm", "xgboost", "catboost"],
        default=None,
        help="(Deprecated: use --model-types) Single model type to train"
    )

    parser.add_argument(
        "--no-ensemble",
        action="store_true",
        help="Skip ensemble building after individual model training"
    )

    parser.add_argument(
        "--rolling-window",
        type=int,
        default=5,
        help="Rolling window size for feature engineering (default: 5)"
    )

    # Simulation mode arguments
    parser.add_argument(
        "--target-season",
        type=int,
        help="Target season for simulation (used with --include-weeks)"
    )

    parser.add_argument(
        "--include-weeks",
        nargs="+",
        type=int,
        help="Weeks from target-season to include in training (e.g., --include-weeks 1 2 3)"
    )

    return parser.parse_args()


def train_position(
    position: str,
    seasons: list[int],
    n_trials: int,
    rolling_window: int,
    model_type: str = "lightgbm",
    df: pl.DataFrame | None = None,
    target_season: int | None = None,
    include_weeks: list[int] | None = None,
) -> dict[str, Any]:
    """Train all models for a specific position.

    Args:
        position: Position to train (QB, RB, WR, TE, K, DEF).
        seasons: List of seasons to train on.
        n_trials: Number of Optuna trials for hyperparameter tuning.
        rolling_window: Rolling window size for feature computation.
        model_type: Model type - "lightgbm", "xgboost", or "catboost".
        df: Optional pre-computed feature DataFrame. If None, features will
            be computed within the position training function.
        target_season: Season to filter for partial week training (simulation mode).
        include_weeks: Weeks to include from target_season (simulation mode).
    """
    if position == "QB":
        from lineupiq.models.qb import train_qb_models
        logger.info("=" * 80)
        logger.info(f"TRAINING QB MODELS (6 targets) [{model_type}]")
        logger.info("=" * 80)
        results = train_qb_models(
            seasons=seasons, n_trials=n_trials, model_type=model_type, df=df
        )
        return {f"QB_{k}": v for k, v in results.items()}

    elif position == "RB":
        from lineupiq.models.rb import train_rb_models
        logger.info("=" * 80)
        logger.info(f"TRAINING RB MODELS (7 targets) [{model_type}]")
        logger.info("=" * 80)
        results = train_rb_models(
            seasons=seasons, n_trials=n_trials, model_type=model_type,
            rolling_window=rolling_window, df=df
        )
        return {f"RB_{k}": v for k, v in results.items()}

    elif position == "WR":
        from lineupiq.models.receiver import train_wr_models
        logger.info("=" * 80)
        logger.info(f"TRAINING WR MODELS (4 targets) [{model_type}]")
        logger.info("=" * 80)
        results = train_wr_models(
            seasons=seasons, n_trials=n_trials, model_type=model_type, df=df
        )
        return {f"WR_{k}": v for k, v in results.items()}

    elif position == "TE":
        from lineupiq.models.receiver import train_te_models
        logger.info("=" * 80)
        logger.info(f"TRAINING TE MODELS (4 targets) [{model_type}]")
        logger.info("=" * 80)
        results = train_te_models(
            seasons=seasons, n_trials=n_trials, model_type=model_type, df=df
        )
        return {f"TE_{k}": v for k, v in results.items()}

    elif position == "K":
        from lineupiq.models.kicker import train_kicker_models
        logger.info("=" * 80)
        logger.info(f"TRAINING KICKER MODELS (5 targets) [{model_type}]")
        logger.info("=" * 80)
        # K and DEF have different data pipelines, don't use cached features
        results = train_kicker_models(
            seasons=seasons,
            n_trials=n_trials,
            model_type=model_type,
            target_season=target_season,
            include_weeks=include_weeks,
        )
        return {f"K_{k}": v for k, v in results.items()}

    elif position == "DEF":
        from lineupiq.models.defense import train_defense_models
        logger.info("=" * 80)
        logger.info(f"TRAINING DEFENSE MODELS (5 targets) [{model_type}]")
        logger.info("=" * 80)
        # K and DEF have different data pipelines, don't use cached features
        results = train_defense_models(
            seasons=seasons,
            n_trials=n_trials,
            model_type=model_type,
            target_season=target_season,
            include_weeks=include_weeks,
        )
        return {f"DEF_{k}": v for k, v in results.items()}

    else:
        raise ValueError(f"Unknown position: {position}")


def _get_position_targets(position: str) -> list[str]:
    """Get target names for a position."""
    if position == "QB":
        from lineupiq.models.qb import QB_TARGETS
        return QB_TARGETS
    elif position == "RB":
        from lineupiq.models.rb import RB_TARGETS
        return RB_TARGETS
    elif position in ("WR", "TE"):
        from lineupiq.models.receiver import RECEIVER_TARGETS
        return RECEIVER_TARGETS
    elif position == "K":
        from lineupiq.data.kicker_processing import get_kicker_target_columns
        return get_kicker_target_columns()
    elif position == "DEF":
        from lineupiq.data.defense_processing import get_defense_target_columns
        return get_defense_target_columns()
    else:
        raise ValueError(f"Unknown position: {position}")


def _get_position_data(
    position: str,
    df: pl.DataFrame,
) -> tuple[Any, dict[str, Any]]:
    """Get X, y_dict for a position from cached features.

    Returns (X, y_dict) for skill positions only (QB, RB, WR, TE).
    K and DEF use separate data pipelines and cannot use cached features.
    """
    if position == "QB":
        from lineupiq.models.qb import prepare_qb_data
        return prepare_qb_data(df)
    elif position == "RB":
        from lineupiq.models.rb import prepare_rb_data
        return prepare_rb_data(df)
    elif position == "WR":
        from lineupiq.models.receiver import prepare_receiver_data
        return prepare_receiver_data(df, "WR")
    elif position == "TE":
        from lineupiq.models.receiver import prepare_receiver_data
        return prepare_receiver_data(df, "TE")
    else:
        raise ValueError(f"Cannot get data for {position} from cached features")


def build_ensembles(
    positions: list[str],
    model_types: list[str],
    trained_models: dict[tuple[str, str, str], Any],
    df_cached: pl.DataFrame | None = None,
    seasons: list[int] | None = None,
    target_season: int | None = None,
    include_weeks: list[int] | None = None,
) -> int:
    """Build and save ensembles for all position/target combos.

    For each position/target, gathers trained models across model types,
    creates an 80/20 holdout split for weight optimization, and builds
    a weighted voting ensemble.

    Args:
        positions: List of positions to build ensembles for.
        model_types: List of model types that were trained.
        trained_models: Dict keyed by (position, target, model_type) → model object.
        df_cached: Cached feature DataFrame for skill positions.
        seasons: Training seasons (for K/DEF data loading).
        target_season: Target season for simulation mode.
        include_weeks: Weeks from target season for simulation mode.

    Returns:
        Number of ensembles built.
    """
    from lineupiq.models.ensemble import build_and_save_ensemble
    from lineupiq.models.persistence import get_save_target

    # Map model_type to ensemble key name
    model_type_keys = {
        "lightgbm": "lgbm",
        "xgboost": "xgb",
        "catboost": "catboost",
    }

    n_ensembles = 0

    for position in positions:
        targets = _get_position_targets(position)

        # Get position data for holdout split
        skill_positions = {"QB", "RB", "WR", "TE"}
        X = None
        y_dict = None

        if position in skill_positions and df_cached is not None:
            try:
                X, y_dict = _get_position_data(position, df_cached)
            except Exception as e:
                logger.warning(f"Could not load data for {position} ensembles: {e}")
                continue
        elif position == "K":
            from lineupiq.data.kicker_processing import (
                get_kicker_feature_columns,
                process_kicker_data,
            )
            try:
                df = process_kicker_data(
                    seasons or [2022, 2023, 2024, 2025],
                    target_season=target_season,
                    include_weeks=include_weeks,
                )
                feature_cols = get_kicker_feature_columns()
                X = df.select(feature_cols).to_numpy().astype(np.float64)
                y_dict = {}
                for t in targets:
                    if t in df.columns:
                        y_arr = df.select(t).to_numpy().flatten().astype(np.float64)
                        y_dict[t] = y_arr
            except Exception as e:
                logger.warning(f"Could not load data for K ensembles: {e}")
                continue
        elif position == "DEF":
            from lineupiq.data.defense_processing import (
                get_defense_feature_columns,
                process_defense_data,
            )
            try:
                df = process_defense_data(
                    seasons or [2022, 2023, 2024, 2025],
                    target_season=target_season,
                    include_weeks=include_weeks,
                )
                feature_cols = get_defense_feature_columns()
                X = df.select(feature_cols).to_numpy().astype(np.float64)
                y_dict = {}
                for t in targets:
                    if t in df.columns:
                        y_arr = df.select(t).to_numpy().flatten().astype(np.float64)
                        y_dict[t] = y_arr
            except Exception as e:
                logger.warning(f"Could not load data for DEF ensembles: {e}")
                continue

        if X is None or y_dict is None:
            continue

        for target in targets:
            if target not in y_dict:
                continue

            y = y_dict[target]

            # Remove NaN rows
            valid_mask = ~np.isnan(y)
            if hasattr(X, '__len__') and len(X) == len(y):
                X_valid = X[valid_mask]
                y_valid = y[valid_mask]
            else:
                X_valid = X
                y_valid = y

            # Gather available models for this position/target
            ensemble_models: dict[str, Any] = {}
            for mt in model_types:
                key = (position, target, mt)
                if key in trained_models:
                    ensemble_models[model_type_keys[mt]] = trained_models[key]

            if len(ensemble_models) < 2:
                logger.info(
                    f"Skipping ensemble for {position}_{target}: "
                    f"only {len(ensemble_models)} model(s) available"
                )
                continue

            # Create 80/20 holdout split for weight optimization
            try:
                X_train, X_val, y_train, y_val = train_test_split(
                    X_valid, y_valid, test_size=0.2, random_state=42
                )
            except ValueError as e:
                logger.warning(f"Could not split data for {position}_{target}: {e}")
                continue

            # Build and save ensemble
            try:
                build_and_save_ensemble(
                    models=ensemble_models,
                    position=position,
                    target=target,
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                )
                n_ensembles += 1
            except Exception as e:
                logger.error(f"Failed to build ensemble for {position}_{target}: {e}")
                continue

    return n_ensembles


def print_summary(all_results: dict[str, Any], n_ensembles: int = 0):
    """Print training summary table."""
    print("\n" + "=" * 80)
    print("MODEL PERFORMANCE SUMMARY")
    print("=" * 80)
    print(f"{'Position_Target':<35} {'RMSE Mean':>12} {'RMSE Std':>12} {'Samples':>10}")
    print("-" * 80)

    for model_name in sorted(all_results.keys()):
        model, metrics = all_results[model_name]
        print(
            f"{model_name:<35} "
            f"{metrics['cv_rmse_mean']:>12.2f} "
            f"{metrics['cv_rmse_std']:>12.2f} "
            f"{metrics['n_samples']:>10}"
        )

    print("=" * 80)
    print(f"Total individual models trained: {len(all_results)}")
    if n_ensembles > 0:
        print(f"Total ensembles built: {n_ensembles}")
    print("=" * 80)


def train_all_models(
    positions: list[str] | None = None,
    seasons: list[int] | None = None,
    n_trials: int = 50,
    rolling_window: int = 5,
    model_types: list[str] | None = None,
    model_type: str | None = None,
    no_ensemble: bool = False,
    target_season: int | None = None,
    include_weeks: list[int] | None = None,
) -> dict[str, Any] | None:
    """
    Train all models programmatically (callable from other Python code).

    Trains all specified model types for each position, then builds weighted
    voting ensembles combining the trained models.

    Uses feature caching to compute features once and share across QB, RB, WR, TE
    positions, reducing total training time by ~50-60%.

    Args:
        positions: List of positions to train (default: all)
        seasons: List of seasons to train on (default: 2022-2025)
        n_trials: Number of Optuna trials (default: 50)
        rolling_window: Rolling window size (default: 5)
        model_types: List of model types to train (default: all three)
        model_type: (Deprecated) Single model type. Use model_types instead.
        no_ensemble: Skip ensemble building (default: False)
        target_season: Season to filter for partial week training (simulation mode)
        include_weeks: Weeks to include from target_season (simulation mode)

    Returns:
        Dict of all trained models with their metrics
    """
    if positions is None:
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
    if seasons is None:
        seasons = [2022, 2023, 2024, 2025]

    # Handle deprecated --model-type
    if model_type is not None:
        warnings.warn(
            "model_type is deprecated, use model_types instead",
            DeprecationWarning,
            stacklevel=2,
        )
        effective_model_types = [model_type]
    elif model_types is not None:
        effective_model_types = model_types
    else:
        effective_model_types = ["lightgbm", "xgboost", "catboost"]

    # Auto-disable ensemble if only 1 model type
    build_ensemble = not no_ensemble and len(effective_model_types) >= 2

    # Print configuration
    logger.info("=" * 80)
    logger.info("LINEUPIQ MODEL TRAINING")
    logger.info("=" * 80)
    logger.info(f"Positions: {', '.join(positions)}")
    logger.info(f"Seasons: {seasons} ({len(seasons)} years)")
    if target_season and include_weeks:
        logger.info(f"Simulation mode: {target_season} filtered to weeks {include_weeks}")
    logger.info(f"Model types: {', '.join(effective_model_types)}")
    logger.info(f"Optuna trials: {n_trials}")
    logger.info(f"Rolling window: {rolling_window} games")
    logger.info(f"Build ensembles: {build_ensemble}")
    logger.info("=" * 80)

    # Pre-compute features once for positions that share the same data pipeline
    # QB, RB, WR, TE all use build_features() from the features pipeline
    # K and DEF have separate data pipelines (process_kicker_data, process_defense_data)
    skill_positions = {"QB", "RB", "WR", "TE"}
    needs_cached_features = bool(set(positions) & skill_positions)

    df_cached: pl.DataFrame | None = None
    if needs_cached_features:
        logger.info("Pre-computing features for skill positions (will be cached)...")
        include_weeks_tuple = tuple(include_weeks) if include_weeks else None
        df_cached = get_cached_features(
            tuple(seasons),
            rolling_window,
            target_season=target_season,
            include_weeks_tuple=include_weeks_tuple,
        )
        logger.info(f"Cached features: {df_cached.shape[0]} rows, {df_cached.shape[1]} columns")

    # Train all model types for all positions
    all_results: dict[str, Any] = {}
    # Track trained model objects for ensemble building: (position, target, model_type) → model
    trained_model_objects: dict[tuple[str, str, str], Any] = {}

    for mt in effective_model_types:
        logger.info(f"\n{'#' * 80}")
        logger.info(f"# TRAINING {mt.upper()} MODELS")
        logger.info(f"{'#' * 80}")

        for position in positions:
            try:
                # Use cached features for skill positions, None for K/DEF
                df_for_position = df_cached if position in skill_positions else None

                results = train_position(
                    position=position,
                    seasons=seasons,
                    n_trials=n_trials,
                    rolling_window=rolling_window,
                    model_type=mt,
                    df=df_for_position,
                    target_season=target_season,
                    include_weeks=include_weeks,
                )

                # Collect results, keyed with model_type suffix for non-lightgbm
                for result_key, (model, metrics) in results.items():
                    # result_key is like "QB_passing_yards"
                    # Parse position and target
                    pos_prefix = result_key.split("_", 1)[0]
                    target_name = result_key.split("_", 1)[1]

                    # Store model object for ensemble building
                    trained_model_objects[(pos_prefix, target_name, mt)] = model

                    # Store in all_results with model_type suffix for display
                    if mt == "lightgbm":
                        display_key = result_key
                    else:
                        suffix = "_xgb" if mt == "xgboost" else "_catboost"
                        display_key = f"{result_key}{suffix}"
                    all_results[display_key] = (model, metrics)

                logger.info(f"\n✓ {position} {mt} training complete ({len(results)} models)")

            except Exception as e:
                logger.error(f"✗ {position} {mt} training failed: {e}", exc_info=True)
                continue

    # Build ensembles
    n_ensembles = 0
    if build_ensemble and trained_model_objects:
        logger.info(f"\n{'#' * 80}")
        logger.info("# BUILDING ENSEMBLES")
        logger.info(f"{'#' * 80}")

        n_ensembles = build_ensembles(
            positions=positions,
            model_types=effective_model_types,
            trained_models=trained_model_objects,
            df_cached=df_cached,
            seasons=seasons,
            target_season=target_season,
            include_weeks=include_weeks,
        )

        logger.info(f"\n✓ Built {n_ensembles} ensembles")

    # Print final summary
    if all_results:
        print_summary(all_results, n_ensembles=n_ensembles)
        logger.info(f"\n✓ Training complete! {len(all_results)} models + {n_ensembles} ensembles saved to packages/backend/models/")
        return all_results
    else:
        logger.error("\n✗ No models were successfully trained!")
        return None


def main():
    """Main CLI entrypoint."""
    args = parse_args()

    # Override trials if quick mode
    n_trials = 10 if args.quick else args.trials

    # Validate simulation mode args
    if args.include_weeks and not args.target_season:
        logger.error("--include-weeks requires --target-season")
        return 1

    # Handle deprecated --model-type
    model_types = args.model_types
    model_type_deprecated = None
    if args.model_type is not None:
        warnings.warn(
            "--model-type is deprecated, use --model-types instead",
            DeprecationWarning,
            stacklevel=2,
        )
        model_type_deprecated = args.model_type

    # Call the programmatic function
    results = train_all_models(
        positions=args.positions,
        seasons=args.seasons,
        n_trials=n_trials,
        rolling_window=args.rolling_window,
        model_types=model_types if model_type_deprecated is None else None,
        model_type=model_type_deprecated,
        no_ensemble=args.no_ensemble,
        target_season=args.target_season,
        include_weeks=args.include_weeks,
    )

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
