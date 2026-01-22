"""
Matchup-specific feature engineering for NFL games.

Provides Vegas betting lines (spreads, totals), home/away context, and divisional
game flags to capture market efficiency signals and contextual game factors.
"""

import logging

import polars as pl

logger = logging.getLogger(__name__)


def engineer_matchup_features(
    schedule_df: pl.DataFrame,
    odds_df: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Add matchup features to schedule data.

    Joins Vegas betting lines (if available) and computes matchup-specific
    features like divisional games, home field advantage, and market signals.

    Vegas line features (when odds_df provided):
    - home_spread: Averaged spread across bookmakers (negative = home favored)
    - total_points: Averaged over/under total
    - vegas_strength_diff: abs(home_spread) as proxy for game competitiveness
    - home_favored: Binary flag (1 if home_spread < 0, 0 otherwise)

    Divisional game features (from schedule):
    - is_divisional: Binary flag (1 if opponent in same division, 0 otherwise)

    For games without odds (pre-2020 or missing data):
    - home_spread: 0.0 (neutral, no favorite)
    - total_points: 45.0 (approximate NFL average)
    - vegas_strength_diff: 0.0
    - home_favored: 0

    Args:
        schedule_df: Schedule DataFrame with season, week, home_team, away_team.
        odds_df: Optional Vegas odds DataFrame with game_id, home_spread, total_points.
                 If None, only divisional features are added.

    Returns:
        Schedule DataFrame with added matchup features (5 new columns with odds,
        1 column without odds).

    Example:
        >>> schedule = pl.DataFrame({
        ...     "game_id": ["2024_01_KC_BUF"],
        ...     "season": [2024],
        ...     "week": [1],
        ...     "home_team": ["KC"],
        ...     "away_team": ["BUF"]
        ... })
        >>> odds = pl.DataFrame({
        ...     "game_id": ["2024_01_KC_BUF"],
        ...     "home_spread": [-3.5],
        ...     "total_points": [52.5]
        ... })
        >>> result = engineer_matchup_features(schedule, odds)
        >>> result["home_spread"][0]
        -3.5
        >>> result["home_favored"][0]
        1
        >>> result["is_divisional"][0]
        0
    """
    logger.info(f"Engineering matchup features for {len(schedule_df)} games")

    # Start with a copy of the schedule
    df = schedule_df.clone()

    # Step 1: Add Vegas line features if odds provided
    if odds_df is not None and len(odds_df) > 0:
        logger.info(f"Joining Vegas odds for {len(odds_df)} games")

        # Join odds to schedule on game_id
        df = df.join(
            odds_df.select(["game_id", "home_spread", "total_points"]),
            on="game_id",
            how="left",
        )

        # Fill missing odds with neutral values (pre-2020 games)
        df = df.with_columns([
            pl.col("home_spread").fill_null(0.0),
            pl.col("total_points").fill_null(45.0),  # NFL average ~45 points
        ])

        # Compute derived Vegas features
        df = df.with_columns([
            # Vegas strength difference (game competitiveness proxy)
            pl.col("home_spread").abs().alias("vegas_strength_diff"),
            # Home favored flag (negative spread means home favored)
            (pl.col("home_spread") < 0).cast(pl.Int8).alias("home_favored"),
        ])

        logger.info("Added 4 Vegas features: home_spread, total_points, vegas_strength_diff, home_favored")
    else:
        logger.warning(
            "No odds data provided. Skipping Vegas features. "
            "Set ODDS_API_KEY in .env to enable spreads/totals."
        )

    # Step 2: Add divisional game flag
    # Load team divisions from nflreadpy
    try:
        import nflreadpy as nfl  # noqa: PLC0415

        teams_df = nfl.load_teams()

        # Create division mapping: team_abbr -> team_division
        # nflreadpy uses team_abbr (e.g., "KC") and team_division (e.g., "AFC West")
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
        # Add is_divisional as 0 (unknown) if teams data unavailable
        df = df.with_columns([pl.lit(0).cast(pl.Int8).alias("is_divisional")])

    feature_count = 5 if odds_df is not None else 1
    logger.info(f"Matchup feature engineering complete: {feature_count} features added")

    return df
