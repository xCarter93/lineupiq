"""
Batch prediction generation for simulation mode.

Generates predictions for all players across all weeks using trained models.
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from lineupiq.models.persistence import load_model
from lineupiq.features.pipeline import get_feature_columns
from lineupiq.data.kicker_processing import get_kicker_feature_columns
from lineupiq.data.defense_processing import get_defense_feature_columns
from lineupiq.simulation.features import generate_week_features

logger = logging.getLogger(__name__)

# Model directory
MODELS_DIR = Path(__file__).parent.parent.parent.parent / "models"

# Target stats by position
POSITION_TARGETS = {
    "QB": ["passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds", "fumbles_lost"],
    "RB": ["rushing_yards", "rushing_tds", "carries", "receiving_yards", "receptions", "receiving_tds", "fumbles_lost"],
    "WR": ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"],
    "TE": ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"],
    "K": ["fg_att", "fg_att_0_39", "fg_att_40_49", "fg_att_50_plus", "pat_att"],
    "DEF": ["points_allowed", "def_sacks", "def_interceptions", "def_fumbles", "total_def_tds"],
}


def load_position_models(position: str) -> dict[str, Any]:
    """Load all trained models for a position.

    Args:
        position: Position code (QB, RB, WR, TE, K, DEF).

    Returns:
        Dict mapping target name to loaded model.
    """
    targets = POSITION_TARGETS.get(position, [])
    models = {}

    for target in targets:
        model_path = MODELS_DIR / f"{position.lower()}_{target}.joblib"

        if model_path.exists():
            try:
                # load_model returns (model, metadata) tuple
                model, _metadata = load_model(position.lower(), target)
                models[target] = model
                logger.debug(f"Loaded model: {position.lower()}_{target}")
            except Exception as e:
                logger.warning(f"Failed to load model {position.lower()}_{target}: {e}")
        else:
            logger.warning(f"Model not found: {model_path}")

    return models


def prepare_features_for_prediction(
    features_df: pl.DataFrame,
    position: str,
) -> np.ndarray:
    """Prepare feature matrix for model prediction.

    Args:
        features_df: DataFrame with player features.
        position: Position for feature selection (K, DEF, or skill position).

    Returns:
        2D numpy array of shape (n_players, n_features).
    """
    # Use position-specific feature columns
    if position == "K":
        feature_columns = get_kicker_feature_columns()
    elif position == "DEF":
        feature_columns = get_defense_feature_columns()
    else:
        feature_columns = get_feature_columns()

    # Convert to feature matrix
    feature_values = []

    for col in feature_columns:
        if col in features_df.columns:
            values = features_df[col].to_list()
            # Convert booleans to float
            values = [float(v) if isinstance(v, bool) else v for v in values]
        else:
            # Fill missing columns with 0
            values = [0.0] * len(features_df)

        feature_values.append(values)

    # Transpose to get (n_samples, n_features)
    return np.array(feature_values, dtype=np.float32).T


def predict_for_position(
    features_df: pl.DataFrame,
    position: str,
    models: dict[str, Any],
) -> pl.DataFrame:
    """Generate predictions for all players of a position.

    Args:
        features_df: DataFrame with player features (filtered to position).
        position: Position code.
        models: Dict mapping target name to model.

    Returns:
        DataFrame with player info and predicted stats.
    """
    if features_df.is_empty():
        return pl.DataFrame()

    if not models:
        logger.warning(f"No models available for {position}")
        return pl.DataFrame()

    # Prepare feature matrix
    X = prepare_features_for_prediction(features_df, position)

    # Predict each target
    predictions = {
        "player_id": features_df["player_id"].to_list(),
        "player_name": features_df["player_name"].to_list(),
        "position": features_df["position"].to_list(),
        "team": features_df["team"].to_list(),
        "opponent": features_df["opponent"].to_list(),
        "season": features_df["season"].to_list(),
        "week": features_df["week"].to_list(),
    }

    for target, model in models.items():
        try:
            preds = model.predict(X)
            # Ensure non-negative for count stats
            if target not in ["passing_yards", "rushing_yards", "receiving_yards", "points_allowed"]:
                preds = np.maximum(preds, 0)
            predictions[target] = [round(float(p), 1) for p in preds]
        except Exception as e:
            logger.error(f"Error predicting {target}: {e}")
            predictions[target] = [0.0] * len(features_df)

    return pl.DataFrame(predictions)


def generate_batch_predictions(
    season: int,
    target_weeks: list[int],
    completed_weeks: list[int],
    positions: list[str] | None = None,
    output_dir: Path | None = None,
) -> pl.DataFrame:
    """Generate predictions for all players across multiple weeks.

    Args:
        season: NFL season year.
        target_weeks: Weeks to generate predictions for.
        completed_weeks: Weeks with actual data available.
        positions: Positions to include (default: QB, RB, WR, TE).
        output_dir: Optional directory to save predictions.

    Returns:
        DataFrame with all predictions.
    """
    if positions is None:
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    logger.info(
        f"Generating batch predictions: season={season}, "
        f"target_weeks={target_weeks}, completed_weeks={completed_weeks}"
    )

    # Load all models upfront
    position_models = {}
    for position in positions:
        models = load_position_models(position)
        if models:
            position_models[position] = models
            logger.info(f"Loaded {len(models)} models for {position}")

    all_predictions = []

    for week in target_weeks:
        logger.info(f"Generating predictions for week {week}...")

        # Generate features for the week
        features_df = generate_week_features(
            season=season,
            target_week=week,
            completed_weeks=completed_weeks,
            positions=positions,
        )

        if features_df.is_empty():
            logger.warning(f"No features for week {week}, skipping")
            continue

        # Predict for each position
        for position in positions:
            if position not in position_models:
                continue

            pos_features = features_df.filter(pl.col("position") == position)
            if pos_features.is_empty():
                continue

            preds = predict_for_position(
                pos_features,
                position,
                position_models[position],
            )

            if not preds.is_empty():
                all_predictions.append(preds)

    if not all_predictions:
        logger.warning("No predictions generated")
        return pl.DataFrame()

    # Combine all predictions (use diagonal to handle different columns per position)
    combined = pl.concat(all_predictions, how="diagonal")
    logger.info(f"Generated {len(combined)} total predictions")

    # Optionally save to disk
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"predictions_{season}_w{min(target_weeks)}-{max(target_weeks)}.parquet"
        combined.write_parquet(output_path)
        logger.info(f"Saved predictions to {output_path}")

    return combined


def load_predictions(season: int, output_dir: Path | None = None) -> pl.DataFrame | None:
    """Load previously generated predictions from disk.

    When multiple prediction files exist (from init + advance cycles),
    keeps the most recent prediction for each player/week combination.

    Args:
        season: NFL season year.
        output_dir: Directory containing prediction files.

    Returns:
        DataFrame with predictions, or None if not found.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent.parent / "data" / "simulation" / "predictions"

    # Find prediction files for this season
    pattern = f"predictions_{season}_*.parquet"
    files = list(output_dir.glob(pattern))

    if not files:
        logger.info(f"No prediction files found for {season}")
        return None

    # Sort files by modification time (newest first) so newer predictions take precedence
    files_sorted = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

    # Load and combine all files (use diagonal to handle different columns per position)
    dfs = [pl.read_parquet(f) for f in files_sorted]
    combined = pl.concat(dfs, how="diagonal")

    # Deduplicate: keep first occurrence of each (player_id, week) pair
    # Since files are sorted newest first, this keeps the most recent prediction
    combined = combined.unique(subset=["player_id", "week"], keep="first")

    logger.info(f"Loaded {len(combined)} predictions from {len(files_sorted)} files (deduplicated)")
    return combined
