"""
Unified feature engineering pipeline for ML-ready datasets.

Provides a single entry point (build_features) that orchestrates rolling stats,
opponent strength, and weather features into a complete feature set ready for
model training.

This is THE main API for feature engineering - call build_features() and get
ML-ready data.
"""

import logging
import os
from pathlib import Path

import polars as pl

from lineupiq.data import process_player_stats
from lineupiq.data.fetchers import fetch_injuries, fetch_schedules
from lineupiq.features.injury import engineer_injury_features
from lineupiq.features.opponent_features import add_opponent_strength
from lineupiq.features.rolling_stats import (
    compute_rolling_stats,
    compute_volatility_features,
    get_volatility_columns,
)
from lineupiq.features.team_strength import compute_team_strength, get_team_strength_columns
from lineupiq.features.weather import engineer_weather_features
from lineupiq.features.matchup import engineer_matchup_features
from lineupiq.data.odds_cache import OddsClient

logger = logging.getLogger(__name__)

# Features directory for saved feature files
FEATURES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "features"


def build_features(seasons: list[int], rolling_window: int = 5) -> pl.DataFrame:
    """Build ML-ready feature dataset from raw NFL data.

    This is the main entry point for feature engineering. It orchestrates:
    1. Load processed data via process_player_stats(seasons)
    2. Add rolling stats via compute_rolling_stats(df, rolling_window)
    3. Add opponent strength via add_opponent_strength(df)
    4. Add team strength features (offensive points, yards, plays)
    5. Add volatility features (std, CV for key stats)
    6. Add detailed weather features (temp bins, wind thresholds, precipitation)
    7. Add injury features (severity, on_injury_report) - Phase 20
    8. Add matchup features (Vegas spreads/totals, divisional games)

    Rolling window expanded from 3 to 5 games (Phase 19.1) to better capture
    recent performance trends, especially for volatile stats like touchdowns.

    Injury features (Phase 20-02) capture 8-10% production impact from injury
    designations (Out, Doubtful, Questionable, Probable).

    Vegas lines (Phase 20-03) provide market efficiency signal - spreads/totals
    capture expected team performance. Research shows home field advantage
    averages +2.5-3 points across NFL.

    Args:
        seasons: List of seasons to process (e.g., [2023, 2024]).
        rolling_window: Number of games for rolling averages (default: 5).

    Returns:
        Complete feature DataFrame ready for ML training, with:
        - Player identifiers (player_id, player_name, position, etc.)
        - Rolling stats (passing_yards_roll5, rushing_yards_roll5, etc.)
        - Opponent strength (opp_pass_defense_strength, opp_rush_defense_strength)
        - Team strength (team_points_roll5, team_yards_roll5, team_plays_roll5)
        - Volatility metrics (passing_yards_std5, rushing_yards_cv5, etc.)
        - Weather features (extreme_cold, freezing, high_wind, has_precip, etc.)
        - Injury features (injury_severity 0.0-1.0, on_injury_report 0/1)
        - Matchup features (home_spread, total_points, vegas_strength_diff, home_favored, is_divisional)
        - Game context (is_home, opponent, week, season)

    Example:
        >>> df = build_features([2024])
        >>> "passing_yards_roll5" in df.columns
        True
        >>> "opp_pass_defense_strength" in df.columns
        True
        >>> "injury_severity" in df.columns
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

    # Step 4: Add team strength features
    logger.info("Step 4: Computing team strength features...")
    import nflreadpy as nfl  # noqa: PLC0415

    team_stats_df = nfl.load_team_stats(seasons)
    schedules_df = fetch_schedules(seasons)
    team_strength = compute_team_strength(team_stats_df, schedules_df, window=rolling_window)

    # Join team strength to player data
    df = df.join(team_strength, on=["season", "week", "team"], how="left")
    team_cols = [c for c in df.columns if c.startswith("team_") and "_roll" in c]
    logger.info(f"Added {len(team_cols)} team strength columns")

    # Step 5: Add volatility features for key stats
    logger.info("Step 5: Computing volatility features...")
    volatility_stats = ["passing_yards", "rushing_yards", "receiving_yards", "receptions"]
    df = compute_volatility_features(df, volatility_stats, window=rolling_window)
    vol_cols = [c for c in df.columns if "_std" in c or "_cv" in c]
    logger.info(f"Added {len(vol_cols)} volatility columns")

    # Step 6: Add detailed weather features
    logger.info("Step 6: Adding detailed weather features...")
    # Check if VISUAL_CROSSING_API_KEY exists
    api_key = os.getenv("VISUAL_CROSSING_API_KEY")
    if api_key:
        logger.info("VISUAL_CROSSING_API_KEY found, will add detailed weather features")
        # Engineer detailed weather features from schedule data
        # Note: schedules_df already fetched in Step 4
        schedules_with_weather = engineer_weather_features(schedules_df)

        # Join weather features to player data via game_id
        # First, create game_id in player data if not present
        if "game_id" not in df.columns:
            logger.warning("No game_id in player data, skipping detailed weather features")
        else:
            # Select only weather feature columns from schedules
            weather_feature_cols = [
                "game_id", "extreme_cold", "freezing", "extreme_heat",
                "temp_filled", "high_wind", "very_high_wind", "wind_filled",
                "has_precip", "precip_amount"
            ]
            existing_weather_cols = [c for c in weather_feature_cols if c in schedules_with_weather.columns]
            weather_features = schedules_with_weather.select(existing_weather_cols)

            # Join to player data
            df = df.join(weather_features, on="game_id", how="left")
            detailed_weather_cols = [c for c in existing_weather_cols if c != "game_id"]
            logger.info(f"Added {len(detailed_weather_cols)} detailed weather columns")
    else:
        logger.warning(
            "VISUAL_CROSSING_API_KEY not found - skipping detailed weather features. "
            "Set environment variable to enable temperature bins, wind thresholds, and precipitation features."
        )
        detailed_weather_cols = []

    # Verify existing weather features
    existing_weather_cols = ["temp_normalized", "wind_normalized"]
    for col in existing_weather_cols:
        if col not in df.columns:
            logger.warning(f"Expected weather column {col} not found")

    # Count total weather features (existing + detailed)
    total_weather_cols = len(existing_weather_cols) + len(detailed_weather_cols)

    # Step 7: Add injury features (Phase 20-02)
    logger.info("Step 7: Adding injury features...")
    injuries_df = fetch_injuries(seasons)
    df = engineer_injury_features(df, injuries_df)
    injury_cols = ["injury_severity", "on_injury_report"]
    logger.info(f"Added {len(injury_cols)} injury columns")

    # Step 8: Add matchup features (Vegas lines, divisional games)
    logger.info("Step 8: Adding matchup features...")
    # Check if ODDS_API_KEY exists
    odds_api_key = os.getenv("ODDS_API_KEY")
    if odds_api_key:
        logger.info("ODDS_API_KEY found, will fetch Vegas spreads and totals")
        try:
            # Initialize Odds API client
            odds_client = OddsClient(api_key=odds_api_key)

            # Get unique game dates from schedules (already fetched in Step 4)
            # The Odds API requires date format YYYY-MM-DD
            if "gameday" in schedules_df.columns:
                unique_dates = schedules_df.select("gameday").unique().sort("gameday")

                # Fetch odds for each date
                all_odds = []
                for row in unique_dates.iter_rows(named=True):
                    gameday = row["gameday"]
                    # Handle both datetime objects and string dates
                    if isinstance(gameday, str):
                        date_str = gameday  # Already in string format
                    else:
                        date_str = gameday.strftime("%Y-%m-%d")  # Convert datetime to string
                    try:
                        games = odds_client.get_historical_odds(date_str)
                        all_odds.extend(games)
                    except Exception as e:
                        logger.warning(f"Failed to fetch odds for {date_str}: {e}")

                # Parse odds into DataFrame
                if all_odds:
                    odds_df = odds_client.parse_odds(all_odds)
                    logger.info(f"Fetched odds for {len(odds_df)} games")

                    # Engineer matchup features with odds
                    schedules_with_matchup = engineer_matchup_features(schedules_df, odds_df)
                else:
                    logger.warning("No odds data fetched, adding matchup features without Vegas lines")
                    schedules_with_matchup = engineer_matchup_features(schedules_df, odds_df=None)
            else:
                logger.warning("No gameday column in schedules, skipping matchup features")
                schedules_with_matchup = schedules_df
        except Exception as e:
            logger.error(f"Error fetching odds: {e}. Adding matchup features without Vegas lines.")
            schedules_with_matchup = engineer_matchup_features(schedules_df, odds_df=None)
    else:
        logger.warning(
            "ODDS_API_KEY not found - skipping Vegas features. "
            "Set in .env for spreads/totals. Divisional flag will still be added."
        )
        # Still add divisional flag even without API key
        schedules_with_matchup = engineer_matchup_features(schedules_df, odds_df=None)

    # Join matchup features to player data via game_id
    if "game_id" in df.columns and "game_id" in schedules_with_matchup.columns:
        # Select matchup feature columns from schedules
        matchup_feature_cols = ["game_id"]
        if "home_spread" in schedules_with_matchup.columns:
            matchup_feature_cols.extend(["home_spread", "total_points", "vegas_strength_diff", "home_favored"])
        if "is_divisional" in schedules_with_matchup.columns:
            matchup_feature_cols.append("is_divisional")

        existing_matchup_cols = [c for c in matchup_feature_cols if c in schedules_with_matchup.columns]
        matchup_features = schedules_with_matchup.select(existing_matchup_cols)

        # Join to player data
        df = df.join(matchup_features, on="game_id", how="left")
        matchup_cols = [c for c in existing_matchup_cols if c != "game_id"]
        logger.info(f"Added {len(matchup_cols)} matchup columns")
    else:
        logger.warning("No game_id in player data or schedules, skipping matchup features")
        matchup_cols = []

    # Sort for consistent ordering
    df = df.sort(["season", "week", "player_id"])

    logger.info(
        f"Feature build complete: {len(df)} rows, {len(df.columns)} columns"
    )
    logger.info(
        f"Feature types: {len(rolling_cols)} rolling, {len(opp_cols)} opponent, "
        f"{len(team_cols)} team, {len(vol_cols)} volatility, "
        f"{total_weather_cols} weather ({len(detailed_weather_cols)} detailed), "
        f"{len(injury_cols)} injury, {len(matchup_cols)} matchup"
    )

    return df


def get_feature_columns() -> list[str]:
    """Get list of all feature column names for ML.

    Returns a categorized list of columns that are actual features
    (not identifiers like player_id or player_name).

    Returns:
        List of feature column names.

    Example:
        >>> cols = get_feature_columns()
        >>> "passing_yards_roll5" in cols
        True
        >>> "player_id" in cols
        False
    """
    # Rolling features (default window=5, expanded from 3 in Phase 19.1)
    # Note: interceptions not available in cleaned data
    rolling_features = [
        "passing_yards_roll5",
        "passing_tds_roll5",
        "rushing_yards_roll5",
        "rushing_tds_roll5",
        "carries_roll5",
        "receiving_yards_roll5",
        "receiving_tds_roll5",
        "receptions_roll5",
    ]

    # Opponent features
    opponent_features = [
        "opp_pass_defense_strength",
        "opp_rush_defense_strength",
        "opp_pass_yards_allowed_rank",
        "opp_rush_yards_allowed_rank",
        "opp_total_yards_allowed_rank",
    ]

    # Team strength features
    team_features = get_team_strength_columns()

    # Volatility features
    volatility_stats = ["passing_yards", "rushing_yards", "receiving_yards", "receptions"]
    volatility_features = get_volatility_columns(volatility_stats)

    # Weather features (Phase 20: expanded from 2 to 10 features)
    weather_features = [
        # Existing normalized features
        "temp_normalized",
        "wind_normalized",
        # New detailed features (Phase 20)
        "extreme_cold",
        "freezing",
        "extreme_heat",
        "high_wind",
        "very_high_wind",
        "has_precip",
        "precip_amount",
    ]

    # Injury features (Phase 20-02: injury designation impact)
    injury_features = [
        "injury_severity",
        "on_injury_report",
    ]

    # Matchup features (Phase 20-03: Vegas lines and divisional games)
    matchup_features = [
        "home_spread",
        "total_points",
        "vegas_strength_diff",
        "home_favored",
        "is_divisional",
    ]

    # Context features (binary/categorical)
    context_features = [
        "is_home",
        "is_dome",
    ]

    return (
        rolling_features
        + opponent_features
        + team_features
        + volatility_features
        + weather_features
        + injury_features
        + matchup_features
        + context_features
    )


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
