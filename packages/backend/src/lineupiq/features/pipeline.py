"""
Unified feature engineering pipeline for ML-ready datasets.

Provides a single entry point (build_features) that orchestrates rolling stats,
opponent strength, and weather features into a complete feature set ready for
model training.

This is THE main API for feature engineering - call build_features() and get
ML-ready data.
"""

import logging
from pathlib import Path

import polars as pl

from lineupiq.data import process_player_stats
from lineupiq.features.opponent_features import add_opponent_strength
from lineupiq.features.rolling_stats import compute_rolling_stats

logger = logging.getLogger(__name__)

# Features directory for saved feature files
FEATURES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "features"


def build_features(seasons: list[int], rolling_window: int = 3) -> pl.DataFrame:
    """Build ML-ready feature dataset from raw NFL data.

    This is the main entry point for feature engineering. It orchestrates:
    1. Load processed data via process_player_stats(seasons)
    2. Add rolling stats via compute_rolling_stats(df, rolling_window)
    3. Add opponent strength via add_opponent_strength(df)
    4. Weather features are already included from process_player_stats

    Args:
        seasons: List of seasons to process (e.g., [2023, 2024]).
        rolling_window: Number of games for rolling averages (default: 3).

    Returns:
        Complete feature DataFrame ready for ML training, with:
        - Player identifiers (player_id, player_name, position, etc.)
        - Rolling stats (passing_yards_roll3, rushing_yards_roll3, etc.)
        - Opponent strength (opp_pass_defense_strength, opp_rush_defense_strength)
        - Weather features (temp_normalized, wind_normalized, is_dome)
        - Game context (is_home, opponent, week, season)

    Example:
        >>> df = build_features([2024])
        >>> "passing_yards_roll3" in df.columns
        True
        >>> "opp_pass_defense_strength" in df.columns
        True
    """
    logger.info(f"Building features for seasons {seasons} with rolling_window={rolling_window}")

    # Step 1: Load and process base data
    logger.info("Step 1: Loading processed player data...")
    df = process_player_stats(seasons)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Step 2: Add rolling stats
    logger.info("Step 2: Computing rolling statistics...")
    df = compute_rolling_stats(df, window=rolling_window)
    rolling_cols = [c for c in df.columns if f"_roll{rolling_window}" in c]
    logger.info(f"Added {len(rolling_cols)} rolling columns")

    # Step 3: Add opponent strength
    logger.info("Step 3: Adding opponent strength features...")
    df = add_opponent_strength(df)
    opp_cols = [c for c in df.columns if "opp_" in c]
    logger.info(f"Added {len(opp_cols)} opponent columns")

    # Step 4: Weather features already included from process_player_stats
    # Verify they exist
    weather_cols = ["temp_normalized", "wind_normalized"]
    for col in weather_cols:
        if col not in df.columns:
            logger.warning(f"Expected weather column {col} not found")

    # Sort for consistent ordering
    df = df.sort(["season", "week", "player_id"])

    logger.info(
        f"Feature build complete: {len(df)} rows, {len(df.columns)} columns"
    )
    logger.info(f"Feature types: {len(rolling_cols)} rolling, {len(opp_cols)} opponent, {len(weather_cols)} weather")

    return df


def get_feature_columns() -> list[str]:
    """Get list of all feature column names for ML.

    Returns a categorized list of columns that are actual features
    (not identifiers like player_id or player_name).

    Returns:
        List of feature column names.

    Example:
        >>> cols = get_feature_columns()
        >>> "passing_yards_roll3" in cols
        True
        >>> "player_id" in cols
        False
    """
    # Rolling features (default window=3)
    # Note: interceptions not available in cleaned data
    rolling_features = [
        "passing_yards_roll3",
        "passing_tds_roll3",
        "rushing_yards_roll3",
        "rushing_tds_roll3",
        "carries_roll3",
        "receiving_yards_roll3",
        "receiving_tds_roll3",
        "receptions_roll3",
    ]

    # Opponent features
    opponent_features = [
        "opp_pass_defense_strength",
        "opp_rush_defense_strength",
        "opp_pass_yards_allowed_rank",
        "opp_rush_yards_allowed_rank",
        "opp_total_yards_allowed_rank",
    ]

    # Weather features
    weather_features = [
        "temp_normalized",
        "wind_normalized",
    ]

    # Context features (binary/categorical)
    context_features = [
        "is_home",
        "is_dome",
    ]

    return rolling_features + opponent_features + weather_features + context_features


def get_target_columns() -> dict[str, list[str]]:
    """Get target columns by position for model training.

    Returns a mapping of position to the stat columns that should be
    predicted for that position.

    Returns:
        Dict mapping position to list of target column names.

    Example:
        >>> targets = get_target_columns()
        >>> "passing_yards" in targets["QB"]
        True
        >>> "rushing_yards" in targets["RB"]
        True
    """
    # Note: interceptions not available in cleaned data,
    # could be added later by including in ML column selection
    return {
        "QB": [
            "passing_yards",
            "passing_tds",
        ],
        "RB": [
            "rushing_yards",
            "rushing_tds",
            "carries",
            "receiving_yards",
            "receptions",
        ],
        "WR": [
            "receiving_yards",
            "receiving_tds",
            "receptions",
        ],
        "TE": [
            "receiving_yards",
            "receiving_tds",
            "receptions",
        ],
    }


def save_features(df: pl.DataFrame, name: str = "features") -> Path:
    """Save feature DataFrame to Parquet file.

    Saves to data/features/ directory, creating it if needed.

    Args:
        df: Feature DataFrame to save.
        name: File name without extension (default: "features").

    Returns:
        Path to the saved file.

    Example:
        >>> df = build_features([2024])
        >>> path = save_features(df, "features_2024")
        >>> path.exists()
        True
    """
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FEATURES_DIR / f"{name}.parquet"

    df.write_parquet(output_path)
    logger.info(f"Saved {len(df)} rows to {output_path}")

    return output_path
