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
from lineupiq.data.fetchers import fetch_injuries, fetch_schedules
from lineupiq.features.epa_features import compute_epa_features, get_epa_columns
from lineupiq.features.depth_chart_features import add_depth_chart_features, get_depth_chart_columns
from lineupiq.features.game_context import (
    compute_implied_team_total,
    compute_rest_features,
    get_game_context_columns,
)
from lineupiq.features.live_feature_service import (
    compute_interaction_features,
    compute_multiwindow_features,
)
from lineupiq.features.opponent_features import add_opponent_strength
from lineupiq.features.injury import engineer_injury_features
from lineupiq.features.nextgen_features import add_nextgen_features, get_nextgen_columns
from lineupiq.features.opportunity_features import add_opportunity_features, get_opportunity_columns
from lineupiq.features.pfr_features import add_pfr_features, get_pfr_columns
from lineupiq.features.qb_connection_features import add_qb_connection_features, get_qb_connection_columns
from lineupiq.features.rolling_stats import (
    compute_rolling_stats,
    compute_volatility_features,
    get_volatility_columns,
)
from lineupiq.features.team_strength import compute_team_strength, get_team_strength_columns
from lineupiq.features.usage_features import compute_usage_features, get_usage_columns
from lineupiq.features.weather import engineer_weather_features
from lineupiq.features.matchup import engineer_matchup_features

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
    7. Add matchup features (Vegas spreads/totals, divisional games)

    Rolling window expanded from 3 to 5 games (Phase 19.1) to better capture
    recent performance trends, especially for volatile stats like touchdowns.

    Vegas lines provide market efficiency signal - spreads/totals from nflreadpy
    schedule data capture expected team performance.

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
        - Matchup features (home_spread, total_points, vegas_strength_diff, home_favored, is_divisional)
        - Game context (is_home, opponent, week, season)

    Example:
        >>> df = build_features([2024])
        >>> "passing_yards_roll5" in df.columns
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

    # Step 3.5: Add injury features
    logger.info("Step 3.5: Adding injury features...")
    try:
        injuries_df = fetch_injuries(seasons)
        if not injuries_df.is_empty():
            df = engineer_injury_features(df, injuries_df)
            logger.info("Added injury_severity and on_injury_report features")
        else:
            df = df.with_columns(
                pl.lit(0.0).alias("injury_severity"),
                pl.lit(0).alias("on_injury_report"),
            )
    except Exception as exc:
        logger.warning("Failed to add injury features: %s", exc)
        df = df.with_columns(
            pl.lit(0.0).alias("injury_severity"),
            pl.lit(0).alias("on_injury_report"),
        )

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
    # engineer_weather_features uses temp/wind/roof from nflreadpy schedules (no API needed)
    logger.info("Step 6: Adding detailed weather features...")
    schedules_with_weather = engineer_weather_features(schedules_df)

    if "game_id" not in df.columns:
        logger.warning("No game_id in player data, skipping detailed weather features")
        detailed_weather_cols = []
    else:
        weather_feature_cols = [
            "game_id", "extreme_cold", "freezing", "extreme_heat",
            "temp_filled", "high_wind", "very_high_wind", "wind_filled",
            "has_precip", "precip_amount"
        ]
        existing_weather_cols = [c for c in weather_feature_cols if c in schedules_with_weather.columns]
        weather_features = schedules_with_weather.select(existing_weather_cols)

        df = df.join(weather_features, on="game_id", how="left")
        detailed_weather_cols = [c for c in existing_weather_cols if c != "game_id"]
        logger.info(f"Added {len(detailed_weather_cols)} detailed weather columns")

    # Verify existing weather features
    existing_weather_cols = ["temp_normalized", "wind_normalized"]
    for col in existing_weather_cols:
        if col not in df.columns:
            logger.warning(f"Expected weather column {col} not found")

    # Count total weather features (existing + detailed)
    total_weather_cols = len(existing_weather_cols) + len(detailed_weather_cols)

    # Step 7: Add matchup features (Vegas lines from schedule, divisional games)
    logger.info("Step 7: Adding matchup features...")
    # nflreadpy schedules include spread_line and total_line columns
    schedules_with_matchup = engineer_matchup_features(schedules_df)

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

    # Step 8: Add rest/bye week features
    logger.info("Step 8: Adding rest/bye week features...")
    df = compute_rest_features(df, schedules_df)
    rest_cols = ["days_since_last_game", "is_post_bye"]
    logger.info(f"Added {len(rest_cols)} rest/bye features")

    # Step 9: Add implied team total and game script features
    logger.info("Step 9: Computing implied team total features...")
    df = compute_implied_team_total(df)
    implied_cols = ["implied_team_total", "game_script_lean"]
    logger.info(f"Added {len(implied_cols)} implied total features")

    # Step 10: Add snap count / usage rate features
    logger.info("Step 10: Computing usage features...")
    df = compute_usage_features(df, seasons, window=rolling_window)
    usage_cols = get_usage_columns(rolling_window)
    logger.info(f"Added {len(usage_cols)} usage features")

    # Step 11: Add EPA features
    logger.info("Step 11: Computing EPA features...")
    df = compute_epa_features(df, seasons, window=rolling_window)
    epa_cols = get_epa_columns(rolling_window)
    logger.info(f"Added {len(epa_cols)} EPA features")

    # Step 11.5: Add depth chart features
    logger.info("Step 11.5: Computing depth chart features...")
    df = add_depth_chart_features(df, seasons)
    depth_cols = get_depth_chart_columns()
    logger.info(f"Added {len(depth_cols)} depth chart features")

    # Step 11.6: Add Next Gen Stats features
    logger.info("Step 11.6: Computing Next Gen Stats features...")
    df = add_nextgen_features(df, seasons)
    nextgen_cols = get_nextgen_columns()
    logger.info(f"Added {len(nextgen_cols)} Next Gen Stats features")

    # Step 11.7: Add expected fantasy point opportunity features (xFP)
    logger.info("Step 11.7: Computing xFP features...")
    df = add_opportunity_features(df, seasons)
    opportunity_cols = get_opportunity_columns()
    logger.info(f"Added {len(opportunity_cols)} xFP features")

    # Step 11.8: Add PFR advanced features
    logger.info("Step 11.8: Computing PFR advanced features...")
    df = add_pfr_features(df, seasons)
    pfr_cols = get_pfr_columns()
    logger.info(f"Added {len(pfr_cols)} PFR features")

    # Step 11.9: Add QB connection + TD opportunity features
    logger.info("Step 11.9: Computing QB connection features...")
    df = add_qb_connection_features(df, window=rolling_window)
    qb_connection_cols = get_qb_connection_columns()
    logger.info(f"Added {len(qb_connection_cols)} QB connection features")

    # Step 12: Add multi-window rolling features (3-game window + momentum)
    logger.info("Step 12: Computing multi-window rolling features...")
    df, multiwindow_cols = compute_multiwindow_features(df, rolling_window=rolling_window, short_window=3)
    logger.info(f"Added {len(multiwindow_cols)} multi-window features")

    # Step 13: Add interaction features
    logger.info("Step 13: Computing interaction features...")
    df, interaction_cols = compute_interaction_features(df, rolling_window=rolling_window)
    logger.info(f"Added {len(interaction_cols)} interaction features")

    # Sort for consistent ordering
    df = df.sort(["season", "week", "player_id"])

    # Count all new feature types
    new_feature_count = (
        len(rest_cols) + len(implied_cols) + len(usage_cols)
        + len(epa_cols) + len(depth_cols) + len(nextgen_cols) + len(opportunity_cols)
        + len(pfr_cols) + len(qb_connection_cols) + len(multiwindow_cols) + len(interaction_cols)
    )

    logger.info(
        f"Feature build complete: {len(df)} rows, {len(df.columns)} columns"
    )
    logger.info(
        f"Feature types: {len(rolling_cols)} rolling, {len(opp_cols)} opponent, "
        f"{len(team_cols)} team, {len(vol_cols)} volatility, "
        f"{total_weather_cols} weather ({len(detailed_weather_cols)} detailed), "
        f"{len(matchup_cols)} matchup, {new_feature_count} new (rest/usage/EPA/multiwindow/interaction)"
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
        "injury_severity",
        "on_injury_report",
    ]

    # Game context features (rest/bye, implied totals)
    game_context_features = get_game_context_columns()

    # Usage features (snap count, target/carry share)
    usage_features = get_usage_columns()

    # EPA features (team/opp/player EPA)
    epa_features = get_epa_columns()
    depth_features = get_depth_chart_columns()
    nextgen_features = get_nextgen_columns()
    opportunity_features = get_opportunity_columns()
    pfr_features = get_pfr_columns()
    qb_connection_features = get_qb_connection_columns()

    # Multi-window rolling features (3-game window + momentum)
    multiwindow_features = [
        "passing_yards_roll3",
        "rushing_yards_roll3",
        "receiving_yards_roll3",
        "receptions_roll3",
        "passing_yards_momentum",
        "rushing_yards_momentum",
        "receiving_yards_momentum",
        "receptions_momentum",
    ]

    # Interaction features
    interaction_features = [
        "rush_yards_x_opp_rush_def",
        "pass_yards_x_opp_pass_def",
        "recv_yards_x_opp_pass_def",
        "player_volume_x_team_pace",
    ]

    return (
        rolling_features
        + opponent_features
        + team_features
        + volatility_features
        + weather_features
        + matchup_features
        + context_features
        + game_context_features
        + usage_features
        + epa_features
        + depth_features
        + nextgen_features
        + opportunity_features
        + pfr_features
        + qb_connection_features
        + multiwindow_features
        + interaction_features
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
