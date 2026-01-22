"""
Walk-forward validation for time-series prediction validation.

Provides functions for proper time-series validation by retraining models
week-by-week and predicting future weeks using only past data.

Key functions:
- retrain_models_through_week: Retrain all models using data through specified week
- predict_week: Generate predictions for a specific week using trained models
- run_walkforward_validation: Orchestrate multi-week validation

This ensures proper temporal validation with no data leakage - each week is
predicted using only data available before that week.
"""

import logging
import tempfile
from pathlib import Path
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
from lineupiq.models.persistence import save_model

logger = logging.getLogger(__name__)

# Position to target mapping
POSITION_TARGETS = {
    "QB": [
        "passing_yards",
        "passing_tds",
        "interceptions",
        "rushing_yards",
        "rushing_tds",
        "fumbles_lost",
    ],
    "RB": [
        "carries",
        "rushing_yards",
        "rushing_tds",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "fumbles_lost",
    ],
    "WR": [
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
    ],
    "TE": [
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
    ],
    "K": [
        "fg_att",
        "fg_made_0_39",
        "fg_made_40_49",
        "fg_made_50_plus",
        "xp_made",
    ],
    "DEF": [
        "sacks",
        "interceptions",
        "fumbles_recovered",
        "def_tds",
        "points_allowed",
    ],
}


def retrain_models_through_week(
    season: int,
    week: int,
    positions: list[str],
    n_trials: int = 30,
    rolling_window: int = 5,
) -> dict[str, dict[str, Path]]:
    """Retrain all models using data through specified week of specified season.

    Trains models using all available data up to and including the specified week,
    then saves them to a temporary directory for use in predictions.

    Args:
        season: Season year (e.g., 2025)
        week: Week number (1-18) - trains through end of this week
        positions: List of positions to train (e.g., ["QB", "RB", "WR", "TE", "K", "DEF"])
        n_trials: Number of Optuna trials for hyperparameter tuning (default: 30)
        rolling_window: Rolling window size for features (default: 5)

    Returns:
        Dict mapping position to dict of {target: model_path} for all trained models.
        Model paths point to temporary directory: models_walkforward_{season}_week{week}/

    Example:
        >>> model_paths = retrain_models_through_week(2025, 1, ["QB"])
        >>> "QB" in model_paths
        True
        >>> "passing_yards" in model_paths["QB"]
        True
    """
    logger.info(
        f"Retraining models through season {season} week {week} "
        f"for positions: {positions}"
    )

    # Determine training seasons - need prior seasons for features
    # Training through week N of season S means we include:
    # - All of seasons [S-3, S-2, S-1]
    # - Weeks 1 through N of season S
    training_seasons = list(range(season - 3, season + 1))

    # Create temporary directory for this training run
    temp_dir = Path(tempfile.gettempdir()) / f"models_walkforward_{season}_week{week}"
    temp_dir.mkdir(exist_ok=True, parents=True)
    logger.info(f"Saving models to: {temp_dir}")

    model_paths: dict[str, dict[str, Path]] = {}

    # Train skill positions (QB, RB, WR, TE)
    skill_positions = [p for p in positions if p in ["QB", "RB", "WR", "TE"]]
    if skill_positions:
        logger.info("Building features for skill positions...")
        df = build_features(training_seasons, rolling_window=rolling_window)

        # Filter to only data through target week
        df = df.filter(
            (pl.col("season") < season) | (
                (pl.col("season") == season) & (pl.col("week") <= week)
            )
        )
        logger.info(f"Filtered to {len(df)} rows through {season} week {week}")

        for position in skill_positions:
            logger.info(f"Training {position} models...")
            model_paths[position] = _train_position_models(
                position, df, n_trials, temp_dir
            )

    # Train kicker models
    if "K" in positions:
        logger.info("Training kicker models...")
        kicker_df = process_kicker_data(training_seasons)
        kicker_df = kicker_df.filter(
            (pl.col("season") < season) | (
                (pl.col("season") == season) & (pl.col("week") <= week)
            )
        )
        model_paths["K"] = _train_kicker_models(kicker_df, n_trials, temp_dir)

    # Train defense models
    if "DEF" in positions:
        logger.info("Training defense models...")
        defense_df = process_defense_data(training_seasons)
        defense_df = defense_df.filter(
            (pl.col("season") < season) | (
                (pl.col("season") == season) & (pl.col("week") <= week)
            )
        )
        model_paths["DEF"] = _train_defense_models(defense_df, n_trials, temp_dir)

    logger.info(f"Retraining complete. Models saved to {temp_dir}")
    return model_paths


def _train_position_models(
    position: str,
    df: pl.DataFrame,
    n_trials: int,
    output_dir: Path,
) -> dict[str, Path]:
    """Train models for a skill position (QB, RB, WR, TE).

    Args:
        position: Position code (QB, RB, WR, or TE)
        df: Feature DataFrame with all positions
        n_trials: Number of Optuna trials
        output_dir: Directory to save models

    Returns:
        Dict mapping target name to model file path
    """
    from lineupiq.models.training import tune_hyperparameters, train_model

    # Import position-specific prepare function
    if position == "QB":
        from lineupiq.models.qb import prepare_qb_data

        X, y_dict = prepare_qb_data(df)
    elif position == "RB":
        from lineupiq.models.rb import prepare_rb_data

        X, y_dict = prepare_rb_data(df)
    elif position == "WR":
        from lineupiq.models.receiver import prepare_wr_data

        X, y_dict = prepare_wr_data(df)
    elif position == "TE":
        from lineupiq.models.receiver import prepare_te_data

        X, y_dict = prepare_te_data(df)
    else:
        raise ValueError(f"Unknown position: {position}")

    model_paths = {}
    targets = POSITION_TARGETS[position]

    for target in targets:
        if target not in y_dict:
            logger.warning(f"Target {target} not available for {position}, skipping")
            continue

        logger.info(f"Training {position}_{target}...")
        y = y_dict[target]

        # Tune hyperparameters
        best_params, _ = tune_hyperparameters(
            X, y, n_trials=n_trials, model_type="lightgbm"
        )

        # Train final model
        model, cv_scores = train_model(X, y, params=best_params, model_type="lightgbm")

        # Save model with metadata
        cv_rmse = -cv_scores
        metrics = {
            "position": position,
            "target": target,
            "model_type": "lightgbm",
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "best_params": best_params,
            "n_samples": len(y),
            "n_features": X.shape[1],
            "n_trials": n_trials,
        }

        # Save to custom directory
        model_path = output_dir / f"{position}_{target}.joblib"
        import joblib

        joblib.dump({"model": model, "metadata": metrics}, model_path)
        model_paths[target] = model_path

        logger.info(
            f"{position}_{target}: RMSE {metrics['cv_rmse_mean']:.2f} "
            f"+/- {metrics['cv_rmse_std']:.2f}"
        )

    return model_paths


def _train_kicker_models(
    df: pl.DataFrame, n_trials: int, output_dir: Path
) -> dict[str, Path]:
    """Train all kicker models.

    Args:
        df: Processed kicker DataFrame
        n_trials: Number of Optuna trials
        output_dir: Directory to save models

    Returns:
        Dict mapping target name to model file path
    """
    from lineupiq.models.training import tune_hyperparameters, train_model

    feature_cols = get_kicker_feature_columns()
    target_cols = get_kicker_target_columns()

    # Drop nulls
    all_cols = feature_cols + target_cols
    df = df.drop_nulls(subset=all_cols)

    X = df.select(feature_cols).to_numpy().astype(np.float64)

    model_paths = {}

    for target in target_cols:
        logger.info(f"Training K_{target}...")
        y = df.select(target).to_numpy().flatten().astype(np.float64)

        best_params, _ = tune_hyperparameters(
            X, y, n_trials=n_trials, model_type="lightgbm"
        )

        model, cv_scores = train_model(X, y, params=best_params, model_type="lightgbm")

        cv_rmse = -cv_scores
        metrics = {
            "position": "K",
            "target": target,
            "model_type": "lightgbm",
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "best_params": best_params,
            "n_samples": len(y),
            "n_features": X.shape[1],
            "n_trials": n_trials,
        }

        model_path = output_dir / f"K_{target}.joblib"
        import joblib

        joblib.dump({"model": model, "metadata": metrics}, model_path)
        model_paths[target] = model_path

        logger.info(f"K_{target}: RMSE {metrics['cv_rmse_mean']:.2f}")

    return model_paths


def _train_defense_models(
    df: pl.DataFrame, n_trials: int, output_dir: Path
) -> dict[str, Path]:
    """Train all defense models.

    Args:
        df: Processed defense DataFrame
        n_trials: Number of Optuna trials
        output_dir: Directory to save models

    Returns:
        Dict mapping target name to model file path
    """
    from lineupiq.models.training import tune_hyperparameters, train_model

    feature_cols = get_defense_feature_columns()
    target_cols = get_defense_target_columns()

    all_cols = feature_cols + target_cols
    df = df.drop_nulls(subset=all_cols)

    X = df.select(feature_cols).to_numpy().astype(np.float64)

    model_paths = {}

    for target in target_cols:
        logger.info(f"Training DEF_{target}...")
        y = df.select(target).to_numpy().flatten().astype(np.float64)

        best_params, _ = tune_hyperparameters(
            X, y, n_trials=n_trials, model_type="lightgbm"
        )

        model, cv_scores = train_model(X, y, params=best_params, model_type="lightgbm")

        cv_rmse = -cv_scores
        metrics = {
            "position": "DEF",
            "target": target,
            "model_type": "lightgbm",
            "cv_rmse_mean": float(cv_rmse.mean()),
            "cv_rmse_std": float(cv_rmse.std()),
            "best_params": best_params,
            "n_samples": len(y),
            "n_features": X.shape[1],
            "n_trials": n_trials,
        }

        model_path = output_dir / f"DEF_{target}.joblib"
        import joblib

        joblib.dump({"model": model, "metadata": metrics}, model_path)
        model_paths[target] = model_path

        logger.info(f"DEF_{target}: RMSE {metrics['cv_rmse_mean']:.2f}")

    return model_paths


def predict_week(
    season: int,
    week: int,
    model_paths: dict[str, dict[str, Path]],
    positions: list[str],
    rolling_window: int = 5,
) -> pl.DataFrame:
    """Generate predictions for a specific week using provided models.

    Loads player data for the specified week, computes features, runs predictions
    using the provided model paths, and returns predictions alongside actuals.

    Args:
        season: Season year (e.g., 2025)
        week: Week number (1-18) to predict
        model_paths: Dict from retrain_models_through_week with model file paths
        positions: List of positions to predict
        rolling_window: Rolling window size for features (default: 5)

    Returns:
        DataFrame with columns:
        [player_id, player_name, position, season, week, target,
         predicted_value, actual_value]

    Example:
        >>> model_paths = retrain_models_through_week(2025, 1, ["QB"])
        >>> predictions = predict_week(2025, 2, model_paths, ["QB"])
        >>> "predicted_value" in predictions.columns
        True
        >>> "actual_value" in predictions.columns
        True
    """
    logger.info(f"Predicting season {season} week {week} for positions: {positions}")

    all_predictions = []

    # Predict skill positions
    skill_positions = [p for p in positions if p in ["QB", "RB", "WR", "TE"]]
    if skill_positions:
        # Build features including target week
        # Need prior season for rolling stats
        seasons_to_load = list(range(season - 1, season + 1))
        df = build_features(seasons_to_load, rolling_window=rolling_window)

        # Filter to only the target week
        week_df = df.filter(
            (pl.col("season") == season) & (pl.col("week") == week)
        )

        if len(week_df) == 0:
            logger.warning(f"No data found for {season} week {week}")
        else:
            for position in skill_positions:
                if position not in model_paths:
                    logger.warning(f"No models available for {position}")
                    continue

                pos_predictions = _predict_position(
                    position, week_df, model_paths[position], season, week
                )
                all_predictions.append(pos_predictions)

    # Predict kickers
    if "K" in positions and "K" in model_paths:
        seasons_to_load = list(range(season - 1, season + 1))
        kicker_df = process_kicker_data(seasons_to_load)
        week_df = kicker_df.filter(
            (pl.col("season") == season) & (pl.col("week") == week)
        )

        if len(week_df) > 0:
            k_predictions = _predict_kicker(week_df, model_paths["K"], season, week)
            all_predictions.append(k_predictions)

    # Predict defense
    if "DEF" in positions and "DEF" in model_paths:
        seasons_to_load = list(range(season - 1, season + 1))
        defense_df = process_defense_data(seasons_to_load)
        week_df = defense_df.filter(
            (pl.col("season") == season) & (pl.col("week") == week)
        )

        if len(week_df) > 0:
            def_predictions = _predict_defense(week_df, model_paths["DEF"], season, week)
            all_predictions.append(def_predictions)

    if not all_predictions:
        logger.warning("No predictions generated")
        return pl.DataFrame()

    # Combine all predictions
    result = pl.concat(all_predictions, how="vertical")
    logger.info(f"Generated {len(result)} predictions for week {week}")

    return result


def _predict_position(
    position: str,
    df: pl.DataFrame,
    model_paths: dict[str, Path],
    season: int,
    week: int,
) -> pl.DataFrame:
    """Generate predictions for a skill position.

    Args:
        position: Position code (QB, RB, WR, TE)
        df: Feature DataFrame for the week
        model_paths: Dict of {target: model_path}
        season: Season year
        week: Week number

    Returns:
        DataFrame with predictions and actuals for this position
    """
    import joblib

    feature_cols = get_feature_columns()

    # Filter to position
    pos_df = df.filter(pl.col("position") == position)

    if len(pos_df) == 0:
        logger.warning(f"No data for {position} in week {week}")
        return pl.DataFrame()

    predictions = []

    for target, model_path in model_paths.items():
        # Load model
        model_data = joblib.load(model_path)
        model = model_data["model"]

        # Verify target column exists
        if target not in pos_df.columns:
            logger.warning(f"Target {target} not in data for {position}")
            continue

        # Get features and actuals
        X = pos_df.select(feature_cols).to_numpy()
        y_actual = pos_df.select(target).to_numpy().flatten()

        # Generate predictions
        y_pred = model.predict(X)

        # Build result DataFrame for this target
        for i, (pred, actual) in enumerate(zip(y_pred, y_actual)):
            row_data = pos_df.row(i, named=True)
            predictions.append({
                "player_id": row_data.get("player_id", ""),
                "player_name": row_data.get("player_name", ""),
                "position": position,
                "season": season,
                "week": week,
                "target": target,
                "predicted_value": float(pred),
                "actual_value": float(actual),
            })

    return pl.DataFrame(predictions)


def _predict_kicker(
    df: pl.DataFrame,
    model_paths: dict[str, Path],
    season: int,
    week: int,
) -> pl.DataFrame:
    """Generate predictions for kickers."""
    import joblib

    feature_cols = get_kicker_feature_columns()
    predictions = []

    for target, model_path in model_paths.items():
        model_data = joblib.load(model_path)
        model = model_data["model"]

        if target not in df.columns:
            continue

        X = df.select(feature_cols).to_numpy()
        y_actual = df.select(target).to_numpy().flatten()
        y_pred = model.predict(X)

        for i, (pred, actual) in enumerate(zip(y_pred, y_actual)):
            row_data = df.row(i, named=True)
            predictions.append({
                "player_id": row_data.get("player_id", ""),
                "player_name": row_data.get("player_name", ""),
                "position": "K",
                "season": season,
                "week": week,
                "target": target,
                "predicted_value": float(pred),
                "actual_value": float(actual),
            })

    return pl.DataFrame(predictions)


def _predict_defense(
    df: pl.DataFrame,
    model_paths: dict[str, Path],
    season: int,
    week: int,
) -> pl.DataFrame:
    """Generate predictions for team defenses."""
    import joblib

    feature_cols = get_defense_feature_columns()
    predictions = []

    for target, model_path in model_paths.items():
        model_data = joblib.load(model_path)
        model = model_data["model"]

        if target not in df.columns:
            continue

        X = df.select(feature_cols).to_numpy()
        y_actual = df.select(target).to_numpy().flatten()
        y_pred = model.predict(X)

        for i, (pred, actual) in enumerate(zip(y_pred, y_actual)):
            row_data = df.row(i, named=True)
            # For defense, use team as identifier
            team_abbr = row_data.get("team", "")
            predictions.append({
                "player_id": team_abbr,  # Team abbr as ID for defense
                "player_name": f"{team_abbr} Defense",
                "position": "DEF",
                "season": season,
                "week": week,
                "target": target,
                "predicted_value": float(pred),
                "actual_value": float(actual),
            })

    return pl.DataFrame(predictions)


def run_walkforward_validation(
    season: int,
    weeks: list[int],
    positions: list[str],
    n_trials: int = 30,
    rolling_window: int = 5,
) -> pl.DataFrame:
    """Run walk-forward validation for multiple weeks.

    Orchestrates the full validation process:
    1. For each week: retrain models through (week-1)
    2. Predict the target week
    3. Accumulate all predictions

    This ensures proper time-series validation - each week is predicted using
    only data available before that week.

    Args:
        season: Season year to validate (e.g., 2025)
        weeks: List of week numbers to validate (e.g., [1, 2, 3, 4])
        positions: List of positions to validate
        n_trials: Number of Optuna trials for training (default: 30)
        rolling_window: Rolling window size (default: 5)

    Returns:
        Combined DataFrame with all predictions and actuals across all weeks

    Example:
        >>> results = run_walkforward_validation(2025, [1, 2], ["QB"], n_trials=10)
        >>> results["week"].unique().sort().to_list()
        [1, 2]
        >>> "predicted_value" in results.columns
        True
    """
    logger.info(
        f"Starting walk-forward validation for season {season}, "
        f"weeks {weeks}, positions {positions}"
    )

    all_predictions = []

    for week in weeks:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"WEEK {week}/{len(weeks)}")
        logger.info(f"{'=' * 80}")

        # Retrain models through previous week
        # For week 1, we train through end of previous season (week 18)
        if week == 1:
            train_season = season - 1
            train_week = 18
        else:
            train_season = season
            train_week = week - 1

        logger.info(f"Step 1: Retraining models through {train_season} week {train_week}...")
        model_paths = retrain_models_through_week(
            train_season, train_week, positions, n_trials, rolling_window
        )

        logger.info(f"Step 2: Predicting {season} week {week}...")
        week_predictions = predict_week(
            season, week, model_paths, positions, rolling_window
        )

        if len(week_predictions) > 0:
            all_predictions.append(week_predictions)
            logger.info(f"✓ Week {week} complete: {len(week_predictions)} predictions")
        else:
            logger.warning(f"✗ Week {week}: No predictions generated")

    if not all_predictions:
        logger.error("No predictions generated for any week")
        return pl.DataFrame()

    # Combine all weeks
    result = pl.concat(all_predictions, how="vertical")

    logger.info(f"\n{'=' * 80}")
    logger.info(f"VALIDATION COMPLETE")
    logger.info(f"{'=' * 80}")
    logger.info(f"Total predictions: {len(result)}")
    logger.info(f"Weeks covered: {sorted(result['week'].unique().to_list())}")
    logger.info(f"Positions: {sorted(result['position'].unique().to_list())}")

    return result
