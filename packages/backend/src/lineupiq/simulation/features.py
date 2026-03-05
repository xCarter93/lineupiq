"""
Feature generation for simulation mode.

Generates features for future weeks using available historical data.
For predicting week N when weeks 1..M are complete (M < N):
- Rolling stats: Use last 5 completed games (actual data)
- Opponent strength: Computed from weeks 1..M
- Schedule context: is_home, is_dome from nflreadpy schedule
"""

import logging
from typing import Any

import polars as pl
import nflreadpy as nfl

from lineupiq.data.fetchers import fetch_rosters, fetch_schedules, fetch_player_stats, fetch_kicker_stats
from lineupiq.data.defense_processing import process_defense_data
from lineupiq.features.pipeline import build_features

logger = logging.getLogger(__name__)

# NFL teams for DEF position
NFL_TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
    "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
    "LV", "LAC", "LAR", "MIA", "MIN", "NE", "NO", "NYG",
    "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WAS"
]


def get_schedule_for_week(season: int, week: int) -> pl.DataFrame:
    """Get schedule data for a specific week.

    Args:
        season: NFL season year.
        week: Week number (1-18).

    Returns:
        DataFrame with game matchups for the week including:
        - home_team, away_team, game_id
        - Stadium/venue info (roof type for dome detection)
    """
    schedules = fetch_schedules([season])

    week_schedule = schedules.filter(pl.col("week") == week)

    logger.info(f"Found {len(week_schedule)} games for week {week} of {season}")
    return week_schedule


def get_active_players(season: int, positions: list[str] | None = None) -> pl.DataFrame:
    """Get roster of active players for a season.

    Args:
        season: NFL season year.
        positions: Filter to specific positions (default: QB, RB, WR, TE, K, DEF).

    Returns:
        DataFrame with player roster data.
    """
    if positions is None:
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    # Filter out DEF for roster fetch (handled separately)
    player_positions = [p for p in positions if p != "DEF"]

    roster = fetch_rosters([season])
    roster = roster.filter(pl.col("position").is_in(player_positions))

    # Add team defenses as synthetic "players" if DEF is requested
    if "DEF" in positions:
        def_rows = []
        for team in NFL_TEAMS:
            def_rows.append({
                "gsis_id": f"DEF_{team}",
                "full_name": f"{team} Defense",
                "position": "DEF",
                "team": team,
            })
        def_df = pl.DataFrame(def_rows)
        roster = pl.concat([roster, def_df], how="diagonal")

    logger.info(f"Found {len(roster)} active players/defenses for {season}")
    return roster


def compute_rolling_features_for_player(
    player_stats: pl.DataFrame,
    completed_weeks: list[int],
    window: int = 5,
) -> dict[str, float]:
    """Compute rolling stats from player's completed games in simulation.

    Args:
        player_stats: Player's historical stats DataFrame.
        completed_weeks: List of weeks with actual data available.
        window: Rolling window size (default: 5).

    Returns:
        Dict with rolling feature values.
    """
    if player_stats.is_empty():
        return {}

    # Filter to completed weeks only
    df = player_stats.filter(pl.col("week").is_in(completed_weeks))

    if df.is_empty():
        return {}

    # Sort by season and week descending to get most recent games first
    df = df.sort(["season", "week"], descending=True)

    # Take last `window` games
    recent = df.head(window)

    # Compute rolling means
    stats = {}
    stat_mappings = {
        # Skill position stats
        f"passing_yards_roll{window}": "passing_yards",
        f"passing_tds_roll{window}": "passing_tds",
        f"rushing_yards_roll{window}": "rushing_yards",
        f"rushing_tds_roll{window}": "rushing_tds",
        f"carries_roll{window}": "carries",
        f"receiving_yards_roll{window}": "receiving_yards",
        f"receiving_tds_roll{window}": "receiving_tds",
        f"receptions_roll{window}": "receptions",
        # Kicker stats
        f"fg_att_roll{window}": "fg_att",
        f"fg_made_roll{window}": "fg_made",
        f"pat_att_roll{window}": "pat_att",
        f"pat_made_roll{window}": "pat_made",
        # Defense stats (note: def_ints_roll5 to match training pipeline)
        f"points_allowed_roll{window}": "points_allowed",
        f"def_sacks_roll{window}": "def_sacks",
        f"def_ints_roll{window}": "def_interceptions",  # Renamed to match training
        f"def_fumbles_roll{window}": "def_fumbles",
        f"def_tds_roll{window}": "total_def_tds",  # Added for DEF model
    }

    for roll_name, stat_col in stat_mappings.items():
        if stat_col in recent.columns:
            values = recent[stat_col].drop_nulls()
            if len(values) > 0:
                stats[roll_name] = round(float(values.mean()), 2)
            else:
                stats[roll_name] = 0.0
        else:
            stats[roll_name] = 0.0

    # Compute fg_pct_roll5 for kickers (FG success rate)
    fg_att_vals = recent["fg_att"].drop_nulls() if "fg_att" in recent.columns else []
    fg_made_vals = recent["fg_made"].drop_nulls() if "fg_made" in recent.columns else []
    if len(fg_att_vals) > 0 and len(fg_made_vals) > 0:
        total_att = float(fg_att_vals.sum())
        total_made = float(fg_made_vals.sum())
        stats[f"fg_pct_roll{window}"] = round(total_made / total_att, 3) if total_att > 0 else 0.0
    else:
        stats[f"fg_pct_roll{window}"] = 0.0

    return stats


def compute_volatility_for_player(
    player_stats: pl.DataFrame,
    completed_weeks: list[int],
    window: int = 5,
) -> dict[str, float]:
    """Compute volatility features from player's completed games.

    Args:
        player_stats: Player's historical stats DataFrame.
        completed_weeks: List of weeks with actual data.
        window: Rolling window size (default: 5).

    Returns:
        Dict with volatility feature values (std, CV).
    """
    if player_stats.is_empty():
        return _default_volatility(window)

    df = player_stats.filter(pl.col("week").is_in(completed_weeks))

    if len(df) < 2:
        return _default_volatility(window)

    df = df.sort(["season", "week"], descending=True).head(window)

    volatility = {}
    stat_cols = [
        "passing_yards", "rushing_yards", "receiving_yards", "receptions",
        "fg_att", "pat_att", "points_allowed", "def_sacks"
    ]

    for col in stat_cols:
        if col in df.columns:
            values = df[col].drop_nulls()
            if len(values) >= 2:
                std_val = float(values.std())
                mean_val = float(values.mean())
                cv_val = std_val / mean_val if mean_val > 0 else 0.0
            else:
                std_val = 0.0
                cv_val = 0.0
        else:
            std_val = 0.0
            cv_val = 0.0

        volatility[f"{col}_std{window}"] = round(std_val, 2)
        volatility[f"{col}_cv{window}"] = round(cv_val, 2)

    return volatility


def _default_volatility(window: int = 5) -> dict[str, float]:
    """Return default volatility values."""
    return {
        f"passing_yards_std{window}": 0.0,
        f"passing_yards_cv{window}": 0.0,
        f"rushing_yards_std{window}": 0.0,
        f"rushing_yards_cv{window}": 0.0,
        f"receiving_yards_std{window}": 0.0,
        f"receiving_yards_cv{window}": 0.0,
        f"receptions_std{window}": 0.0,
        f"receptions_cv{window}": 0.0,
        # Kicker stats
        f"fg_att_std{window}": 0.0,
        f"fg_att_cv{window}": 0.0,
        f"pat_att_std{window}": 0.0,
        f"pat_att_cv{window}": 0.0,
        # Defense stats
        f"points_allowed_std{window}": 0.0,
        f"points_allowed_cv{window}": 0.0,
        f"def_sacks_std{window}": 0.0,
        f"def_sacks_cv{window}": 0.0,
    }


def _compute_def_rolling_features(defense_stats: pl.DataFrame, window: int = 5) -> dict[str, float]:
    """Compute rolling features for defense from team defense stats.

    Args:
        defense_stats: DataFrame with team defense history.
        window: Rolling window size (default: 5).

    Returns:
        Dict with defense rolling feature values matching model expectations.
    """
    if defense_stats.is_empty():
        return {
            "points_allowed_roll5": 22.0,  # League average
            "def_sacks_roll5": 2.5,
            "def_ints_roll5": 1.0,
            "def_fumbles_roll5": 0.5,
            "def_tds_roll5": 0.2,
        }

    # Sort by season and week descending to get most recent games first
    df = defense_stats.sort(["season", "week"], descending=True).head(window)

    features = {}

    # Compute rolling means for each stat
    stat_mappings = {
        "points_allowed_roll5": "points_allowed",
        "def_sacks_roll5": "def_sacks",
        "def_ints_roll5": "def_interceptions",  # Column name in process_defense_data
        "def_fumbles_roll5": "def_fumbles",
        "def_tds_roll5": "total_def_tds",
    }

    for feature_name, stat_col in stat_mappings.items():
        if stat_col in df.columns:
            values = df[stat_col].drop_nulls()
            if len(values) > 0:
                features[feature_name] = round(float(values.mean()), 2)
            else:
                # Default values
                features[feature_name] = 22.0 if "points" in feature_name else 1.0
        else:
            features[feature_name] = 22.0 if "points" in feature_name else 1.0

    return features


def get_default_context_features(is_home: bool = True) -> dict[str, Any]:
    """Get default context features when data is unavailable.

    Args:
        is_home: Whether player is playing at home.

    Returns:
        Dict with neutral/average feature values.
    """
    return {
        # Opponent features (neutral)
        "opp_pass_defense_strength": 0.5,
        "opp_rush_defense_strength": 0.5,
        "opp_pass_yards_allowed_rank": 16.0,
        "opp_rush_yards_allowed_rank": 16.0,
        "opp_total_yards_allowed_rank": 16.0,
        # Team strength (league average)
        "team_points_roll5": 22.0,
        "team_yards_roll5": 340.0,
        "team_plays_roll5": 65.0,
        # Weather (neutral)
        "temp_normalized": 0.5,
        "wind_normalized": 0.2,
        "extreme_cold": False,
        "freezing": False,
        "extreme_heat": False,
        "high_wind": False,
        "very_high_wind": False,
        "has_precip": False,
        "precip_amount": 0.0,
        # Matchup (neutral)
        "home_spread": 0.0,
        "total_points": 45.0,
        "vegas_strength_diff": 0.0,
        "home_favored": False,
        "is_divisional": False,
        # Context
        "is_home": is_home,
        "is_dome": False,
    }


def generate_week_features(
    season: int,
    target_week: int,
    completed_weeks: list[int],
    positions: list[str] | None = None,
) -> pl.DataFrame:
    """Generate features for all players for a specific week.

    Uses completed weeks' actual data to compute rolling stats and other
    features for predicting the target week.

    Args:
        season: NFL season year.
        target_week: Week to generate predictions for.
        completed_weeks: List of weeks with actual data available.
        positions: Positions to include (default: QB, RB, WR, TE, K, DEF).

    Returns:
        DataFrame with one row per player, containing all features needed
        for prediction.
    """
    if positions is None:
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

    logger.info(
        f"Generating features for week {target_week} of {season} "
        f"(using completed weeks: {completed_weeks})"
    )

    # Get active roster
    roster = get_active_players(season, positions)

    # Get schedule for target week
    schedule = get_schedule_for_week(season, target_week)

    # Get player stats for completed weeks
    all_seasons = list(range(season - 3, season + 1))  # Include prior seasons for rolling
    player_stats = fetch_player_stats(all_seasons, summary_level="week")
    player_stats = player_stats.filter(pl.col("position").is_in(positions))

    # Load defense data if DEF is in positions
    defense_stats = None
    if "DEF" in positions:
        defense_stats = process_defense_data(all_seasons)

    # Build features for each player
    feature_rows = []

    for player in roster.to_dicts():
        player_id = player["gsis_id"]
        position = player["position"]
        team = player["team"]

        # Find this player's game in the schedule
        game = schedule.filter(
            (pl.col("home_team") == team) | (pl.col("away_team") == team)
        )

        if game.is_empty():
            # Player not scheduled (bye week)
            continue

        game_row = game.row(0, named=True)
        is_home = game_row["home_team"] == team
        opponent = game_row["away_team"] if is_home else game_row["home_team"]

        # Check if dome
        roof = game_row.get("roof", "")
        is_dome = roof in ("dome", "closed") if roof else False

        # Handle DEF position separately
        if position == "DEF" and defense_stats is not None:
            # Get this team's defense history
            team_defense = defense_stats.filter(pl.col("team") == team)

            # Filter to completed weeks + prior seasons
            prior_def = team_defense.filter(pl.col("season") < season)
            current_def = team_defense.filter(
                (pl.col("season") == season) & (pl.col("week").is_in(completed_weeks))
            )
            combined_def = pl.concat([prior_def, current_def])

            # Compute DEF rolling features
            def_rolling = _compute_def_rolling_features(combined_def, window=5)

            features: dict[str, Any] = {
                "player_id": player_id,
                "player_name": player["full_name"],
                "position": position,
                "team": team,
                "opponent": opponent,
                "season": season,
                "week": target_week,
                **def_rolling,
            }
            feature_rows.append(features)
            continue

        # Get this player's historical stats (skill positions and K)
        player_history = player_stats.filter(pl.col("player_id") == player_id)

        # Filter to target season's completed weeks + prior seasons
        prior_season_stats = player_history.filter(pl.col("season") < season)
        current_season_stats = player_history.filter(
            (pl.col("season") == season) & (pl.col("week").is_in(completed_weeks))
        )

        # Combine for rolling calculation (prior seasons + completed weeks)
        combined_stats = pl.concat([prior_season_stats, current_season_stats])

        # Compute features
        rolling_features = compute_rolling_features_for_player(
            combined_stats,
            completed_weeks=list(range(1, 100)),  # All available
            window=5,
        )

        volatility_features = compute_volatility_for_player(
            combined_stats,
            completed_weeks=list(range(1, 100)),
            window=5,
        )

        context_features = get_default_context_features(is_home)
        context_features["is_home"] = is_home
        context_features["is_dome"] = is_dome

        # Combine all features
        features = {
            "player_id": player_id,
            "player_name": player["full_name"],
            "position": position,
            "team": team,
            "opponent": opponent,
            "season": season,
            "week": target_week,
            **rolling_features,
            **volatility_features,
            **context_features,
        }

        feature_rows.append(features)

    if not feature_rows:
        logger.warning(f"No features generated for week {target_week}")
        return pl.DataFrame()

    df = pl.DataFrame(feature_rows)
    logger.info(f"Generated features for {len(df)} players")

    return df
