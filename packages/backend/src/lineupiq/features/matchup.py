"""
Matchup-specific feature engineering for NFL games.

Provides Vegas betting lines (spreads, totals) from nflreadpy schedule data,
home/away context, and divisional game flags to capture market efficiency
signals and contextual game factors.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def engineer_matchup_features(
    schedule_df: pl.DataFrame,
) -> pl.DataFrame:
    """Add matchup features to schedule data.

    Extracts Vegas betting lines from nflreadpy's schedule data (spread_line,
    total_line columns) and computes matchup-specific features like divisional
    games, home field advantage, and market signals.

    Vegas line features (when spread_line/total_line available in schedule):
    - home_spread: Spread from schedule (positive = home favored)
    - total_points: Over/under total from schedule
    - vegas_strength_diff: abs(home_spread) as proxy for game competitiveness
    - home_favored: Binary flag (1 if home_spread > 0, 0 otherwise)

    Divisional game features (from nflreadpy teams data):
    - is_divisional: Binary flag (1 if opponent in same division, 0 otherwise)

    For games without spread/total data:
    - home_spread: 0.0 (neutral, no favorite)
    - total_points: 45.0 (approximate NFL average)
    - vegas_strength_diff: 0.0
    - home_favored: 0

    Args:
        schedule_df: Schedule DataFrame from nflreadpy with season, week,
                     home_team, away_team, and optionally spread_line, total_line.

    Returns:
        Schedule DataFrame with added matchup features (5 new columns).

    Example:
        >>> import nflreadpy as nfl
        >>> schedule = nfl.load_schedules([2024])
        >>> result = engineer_matchup_features(schedule)
        >>> "home_spread" in result.columns
        True
        >>> "is_divisional" in result.columns
        True
    """
    logger.info(f"Engineering matchup features for {len(schedule_df)} games")

    # Start with a copy of the schedule
    df = schedule_df.clone()

    # Step 1: Add Vegas line features from nflreadpy schedule columns
    has_spread = "spread_line" in df.columns
    has_total = "total_line" in df.columns

    if has_spread or has_total:
        logger.info("Found Vegas line columns in schedule data (spread_line/total_line)")

        # Map nflreadpy column names to our feature names
        if has_spread:
            df = df.with_columns(
                pl.col("spread_line").cast(pl.Float64).fill_null(0.0).alias("home_spread")
            )
        else:
            df = df.with_columns(pl.lit(0.0).alias("home_spread"))

        if has_total:
            df = df.with_columns(
                pl.col("total_line").cast(pl.Float64).fill_null(45.0).alias("total_points")
            )
        else:
            df = df.with_columns(pl.lit(45.0).alias("total_points"))

        # Compute derived Vegas features
        # nflverse convention: spread_line > 0 means the HOME team is favored.
        df = df.with_columns([
            pl.col("home_spread").abs().alias("vegas_strength_diff"),
            (pl.col("home_spread") > 0).cast(pl.Int8).alias("home_favored"),
        ])

        logger.info("Added 4 Vegas features: home_spread, total_points, vegas_strength_diff, home_favored")
    else:
        logger.warning(
            "No spread_line/total_line columns in schedule data. "
            "Using neutral Vegas features."
        )
        df = df.with_columns([
            pl.lit(0.0).alias("home_spread"),
            pl.lit(45.0).alias("total_points"),
            pl.lit(0.0).alias("vegas_strength_diff"),
            pl.lit(0).cast(pl.Int8).alias("home_favored"),
        ])
        logger.info("Added 4 neutral Vegas features (no spread/total data)")

    # Step 2: Add divisional game flag
    try:
        import nflreadpy as nfl  # noqa: PLC0415

        teams_df = nfl.load_teams()

        # Create division mapping: team_abbr -> team_division
        division_map = teams_df.select(["team_abbr", "team_division"])

        # Join home team division
        df = df.join(
            division_map.rename({"team_abbr": "home_team", "team_division": "home_division"}),
            on="home_team",
            how="left",
        )

        # Join away team division
        df = df.join(
            division_map.rename({"team_abbr": "away_team", "team_division": "away_division"}),
            on="away_team",
            how="left",
        )

        # Flag divisional games (both teams in same division)
        df = df.with_columns([
            (pl.col("home_division") == pl.col("away_division"))
            .fill_null(False)
            .cast(pl.Int8)
            .alias("is_divisional")
        ])

        # Drop temporary division columns
        df = df.drop(["home_division", "away_division"])

        logger.info("Added divisional game flag: is_divisional")

    except Exception as e:
        logger.error(f"Failed to add divisional flag: {e}")
        df = df.with_columns([pl.lit(0).cast(pl.Int8).alias("is_divisional")])

    logger.info("Matchup feature engineering complete: 5 features added")

    return df
