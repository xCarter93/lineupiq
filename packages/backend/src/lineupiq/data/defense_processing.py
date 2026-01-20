"""
Team defense data processing for ML model training.

Processes team-level defensive stats for predicting fantasy DST points.
Defense is modeled at team level (not individual players) since fantasy
leagues use team defense/special teams as a single unit.

Target stats for prediction:
- Points allowed (from opponent score)
- Sacks
- Interceptions
- Fumble recoveries
- Defensive/ST touchdowns
"""

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_schedules, fetch_team_defense_stats

logger = logging.getLogger(__name__)

# Defense stat columns from nflreadpy team stats
# nflreadpy uses def_ prefix for defensive stats
DEFENSE_STAT_COLUMNS = [
    "def_sacks",
    "def_interceptions",
    "def_fumbles",  # Fumble recoveries
    "def_tds",
    "def_safeties",
    "special_teams_tds",
]

# Target columns for defense models
# Named to match fantasy DST scoring categories
DEFENSE_TARGETS = [
    "points_allowed",
    "def_sacks",
    "def_interceptions",
    "def_fumbles",
    "total_def_tds",  # def_tds + special_teams_tds
]


def process_defense_data(seasons: list[int]) -> pl.DataFrame:
    """Process team defense data for model training.

    Args:
        seasons: List of seasons to process.

    Returns:
        DataFrame with defense features and targets, one row per team-game.

    Example:
        >>> df = process_defense_data([2024])
        >>> "points_allowed_roll5" in df.columns
        True
    """
    logger.info(f"Processing defense data for seasons: {seasons}")

    # Fetch team stats
    team_df = fetch_team_defense_stats(seasons)

    # Fetch schedules for points allowed
    schedules = fetch_schedules(seasons)

    # Compute points allowed from schedules
    # For home team: points_allowed = away_score
    # For away team: points_allowed = home_score
    home_pa = schedules.select(
        [
            pl.col("season"),
            pl.col("week"),
            pl.col("home_team").alias("team"),
            pl.col("away_score").alias("points_allowed"),
        ]
    )

    away_pa = schedules.select(
        [
            pl.col("season"),
            pl.col("week"),
            pl.col("away_team").alias("team"),
            pl.col("home_score").alias("points_allowed"),
        ]
    )

    points_allowed = pl.concat([home_pa, away_pa])

    # Select relevant columns from team stats
    # team_df may have 'team' or 'recent_team' column depending on nflreadpy version
    team_col = "recent_team" if "recent_team" in team_df.columns else "team"
    id_cols = ["season", "week", team_col]
    available_stats = [c for c in DEFENSE_STAT_COLUMNS if c in team_df.columns]

    # Rename team column if needed
    df = team_df.select(
        [
            pl.col("season"),
            pl.col("week"),
            pl.col(team_col).alias("team"),
        ]
        + [pl.col(c) for c in available_stats]
    )

    # Join points allowed
    df = df.join(points_allowed, on=["season", "week", "team"], how="left")

    # Fill nulls
    for col in available_stats + ["points_allowed"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).fill_null(0))

    # Create combined TD column
    def_tds_col = "def_tds" if "def_tds" in df.columns else None
    st_tds_col = "special_teams_tds" if "special_teams_tds" in df.columns else None

    if def_tds_col and st_tds_col:
        df = df.with_columns(
            (pl.col("def_tds").fill_null(0) + pl.col("special_teams_tds").fill_null(0)).alias(
                "total_def_tds"
            )
        )
    elif def_tds_col:
        df = df.with_columns(pl.col("def_tds").fill_null(0).alias("total_def_tds"))
    else:
        df = df.with_columns(pl.lit(0).alias("total_def_tds"))

    # Sort for rolling calculations
    df = df.sort(["team", "season", "week"])

    # Add rolling features (opponent-adjusted strength)
    rolling_configs = [
        ("points_allowed", "points_allowed_roll5"),
        ("def_sacks", "def_sacks_roll5"),
        ("def_interceptions", "def_ints_roll5"),
        ("def_fumbles", "def_fumbles_roll5"),
        ("total_def_tds", "def_tds_roll5"),
    ]

    for src_col, dest_col in rolling_configs:
        if src_col in df.columns:
            df = df.with_columns(
                pl.col(src_col)
                .shift(1)
                .rolling_mean(window_size=3, min_samples=1)
                .over("team")
                .alias(dest_col)
            )

    # Fill rolling nulls with league averages
    rolling_cols = [
        "points_allowed_roll5",
        "def_sacks_roll5",
        "def_ints_roll5",
        "def_fumbles_roll5",
        "def_tds_roll5",
    ]
    for col in rolling_cols:
        if col in df.columns:
            mean_val = df.select(pl.col(col).mean()).item() or 0.0
            df = df.with_columns(pl.col(col).fill_null(mean_val))

    logger.info(f"Processed defense data: {df.shape[0]} rows, {df.shape[1]} columns")

    return df


def get_defense_feature_columns() -> list[str]:
    """Return feature columns for defense models."""
    return [
        "points_allowed_roll5",
        "def_sacks_roll5",
        "def_ints_roll5",
        "def_fumbles_roll5",
        "def_tds_roll5",
    ]


def get_defense_target_columns() -> list[str]:
    """Return target columns for defense models."""
    return DEFENSE_TARGETS
