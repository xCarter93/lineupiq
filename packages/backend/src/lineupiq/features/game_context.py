"""
Game context features: rest days, bye weeks, and implied team totals.

Adds high-value features based on scheduling and Vegas lines:
- days_since_last_game: Rest advantage (post-bye boost, Thursday penalty)
- is_post_bye: Binary flag for post-bye week games
- implied_team_total: Vegas-derived expected team scoring
- game_script_lean: Expected pass/rush split based on spread
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def compute_rest_features(df: pl.DataFrame, schedules_df: pl.DataFrame) -> pl.DataFrame:
    """Add rest/bye week features to player data.

    Computes days since last game for each team and flags post-bye weeks.
    Research shows:
    - Post-bye: +1-2 fantasy point boost
    - Thursday (short rest): slight penalty
    - 10+ days rest: meaningful advantage

    Args:
        df: Player stats DataFrame with season, week, team columns.
        schedules_df: Schedules DataFrame with season, week, home/away teams and
            nflreadpy's native home_rest/away_rest columns.

    Returns:
        DataFrame with added columns: days_since_last_game, is_post_bye.
    """
    logger.info("Computing rest/bye week features")

    # nflreadpy carries native per-team rest days; a hand-rolled diff over consecutive
    # games has no season boundary and mislabels every Week 1 row as a ~207-day post-bye.
    home_games = schedules_df.select([
        pl.col("season"),
        pl.col("week"),
        pl.col("home_team").alias("team"),
        pl.col("home_rest").cast(pl.Float64).alias("days_since_last_game"),
    ])
    away_games = schedules_df.select([
        pl.col("season"),
        pl.col("week"),
        pl.col("away_team").alias("team"),
        pl.col("away_rest").cast(pl.Float64).alias("days_since_last_game"),
    ])
    team_games = pl.concat([home_games, away_games])

    # Fill any missing rest with the league-average week (7 days)
    team_games = team_games.with_columns(
        pl.col("days_since_last_game").fill_null(7.0)
    )

    # Flag post-bye: days_since_last_game >= 12 (bye = no game for ~13-14 days)
    rest_features = team_games.with_columns(
        (pl.col("days_since_last_game") >= 12).alias("is_post_bye")
    ).select([
        "season", "week", "team",
        "days_since_last_game", "is_post_bye",
    ])

    # Join to player data
    result = df.join(rest_features, on=["season", "week", "team"], how="left")

    # Fill any remaining nulls with defaults
    result = result.with_columns([
        pl.col("days_since_last_game").fill_null(7.0),
        pl.col("is_post_bye").fill_null(False),
    ])

    matched = result.filter(pl.col("days_since_last_game").is_not_null()).shape[0]
    logger.info(f"Added rest features: {matched}/{len(result)} rows matched")

    return result


def compute_implied_team_total(df: pl.DataFrame) -> pl.DataFrame:
    """Compute implied team total from Vegas spread and total.

    Implied team total = (total_points +/- home_spread) / 2
    This is THE strongest predictor of fantasy production in DFS.

    home_spread follows the nflverse spread_line convention: positive means the
    home team is favored, so the home team's implied total adds the spread.

    Also computes game_script_lean (expected pass/rush split from spread).

    Args:
        df: DataFrame with home_spread, total_points, and is_home columns.

    Returns:
        DataFrame with added columns: implied_team_total, game_script_lean.
    """
    logger.info("Computing implied team total features")

    # Check required columns exist
    if "total_points" not in df.columns or "home_spread" not in df.columns:
        logger.warning("Missing total_points or home_spread, using defaults")
        return df.with_columns([
            pl.lit(22.5).alias("implied_team_total"),
            pl.lit(0.0).alias("game_script_lean"),
        ])

    # Implied team total:
    # nflverse convention: home_spread > 0 means the HOME team is favored.
    # For home team: (total + spread) / 2
    # For away team: (total - spread) / 2
    result = df.with_columns(
        pl.when(pl.col("is_home"))
        .then((pl.col("total_points") + pl.col("home_spread")) / 2)
        .otherwise((pl.col("total_points") - pl.col("home_spread")) / 2)
        .fill_null(22.5)  # League average if missing
        .alias("implied_team_total")
    )

    # Game script lean: positive = expected to trail (more passing)
    # negative = expected to lead (more rushing)
    # Sign is inverted from home_spread, which is positive when the home team is favored.
    result = result.with_columns(
        pl.when(pl.col("is_home"))
        .then(-pl.col("home_spread"))
        .otherwise(pl.col("home_spread"))
        .fill_null(0.0)
        .alias("game_script_lean")
    )

    logger.info("Added implied_team_total and game_script_lean features")

    return result


def get_game_context_columns() -> list[str]:
    """Return list of game context feature column names."""
    return [
        "days_since_last_game",
        "is_post_bye",
        "implied_team_total",
        "game_script_lean",
    ]
