"""
Team offensive strength features for ML models.

Computes rolling team-level metrics that provide context for individual
player performance predictions.

Key features:
- team_points_roll5: Rolling 5-game average points scored
- team_yards_roll5: Rolling 5-game average total yards
- team_plays_roll5: Rolling 5-game average plays per game (pace)
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def compute_team_strength(
    team_stats_df: pl.DataFrame,
    schedules_df: pl.DataFrame,
    window: int = 5,
) -> pl.DataFrame:
    """Compute rolling team offensive strength metrics.

    Args:
        team_stats_df: Team stats from nflreadpy load_team_stats().
        schedules_df: Schedules from nflreadpy load_schedules().
        window: Rolling window size (default: 5 games).

    Returns:
        DataFrame with columns: season, week, team, team_points_roll{window},
        team_yards_roll{window}, team_plays_roll{window}.
    """
    logger.info(f"Computing team strength features with window={window}")

    # Get points scored from schedules (need to handle home/away)
    home_points = schedules_df.select([
        pl.col("season"),
        pl.col("week"),
        pl.col("home_team").alias("team"),
        pl.col("home_score").alias("points_scored"),
    ])

    away_points = schedules_df.select([
        pl.col("season"),
        pl.col("week"),
        pl.col("away_team").alias("team"),
        pl.col("away_score").alias("points_scored"),
    ])

    points_df = pl.concat([home_points, away_points])

    # Compute total yards and plays from team_stats
    team_offense = team_stats_df.select([
        pl.col("season"),
        pl.col("week"),
        pl.col("team"),
        (pl.col("passing_yards") + pl.col("rushing_yards")).alias("total_yards"),
        (pl.col("attempts") + pl.col("carries")).alias("total_plays"),
    ])

    # Join points with yards/plays
    combined = team_offense.join(
        points_df,
        on=["season", "week", "team"],
        how="left",
    )

    # Sort for rolling calculations
    combined = combined.sort(["team", "season", "week"])

    # Compute rolling averages with shift to avoid data leakage
    # shift(1) ensures we only use prior games, not current game
    result = combined.with_columns([
        pl.col("points_scored")
        .shift(1)
        .rolling_mean(window_size=window, min_samples=1)
        .over("team")
        .alias(f"team_points_roll{window}"),

        pl.col("total_yards")
        .shift(1)
        .rolling_mean(window_size=window, min_samples=1)
        .over("team")
        .alias(f"team_yards_roll{window}"),

        pl.col("total_plays")
        .shift(1)
        .rolling_mean(window_size=window, min_samples=1)
        .over("team")
        .alias(f"team_plays_roll{window}"),
    ])

    # Select only the features we need
    features = result.select([
        "season",
        "week",
        "team",
        f"team_points_roll{window}",
        f"team_yards_roll{window}",
        f"team_plays_roll{window}",
    ])

    # Fill nulls with league averages
    for col in [f"team_points_roll{window}", f"team_yards_roll{window}", f"team_plays_roll{window}"]:
        mean_val = features.select(pl.col(col).mean()).item()
        features = features.with_columns(pl.col(col).fill_null(mean_val))

    logger.info(f"Computed team strength features: {features.shape[0]} rows")

    return features


def get_team_strength_columns(window: int = 5) -> list[str]:
    """Return list of team strength feature column names.

    Args:
        window: Rolling window size used in compute_team_strength (default: 5).

    Returns:
        List of column names for team strength features.
    """
    return [
        f"team_points_roll{window}",
        f"team_yards_roll{window}",
        f"team_plays_roll{window}",
    ]
