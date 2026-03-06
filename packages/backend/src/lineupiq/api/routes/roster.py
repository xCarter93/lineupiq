"""Roster and player history API routes."""

import logging

import nflreadpy as nfl
import polars as pl
from fastapi import APIRouter, HTTPException, Query

from lineupiq.api.schemas.prediction import PlayerFeaturesResponse
from lineupiq.api.schemas.roster import (
    PlayerHistoryResponse,
    PlayerRoster,
    RosterResponse,
    WeeklyStats,
)
from lineupiq.data.fetchers import fetch_player_history, fetch_rosters
from lineupiq.features.rankings_cache import (
    get_latest_opponent_strength,
    get_latest_team_strength,
)
from lineupiq.features.pipeline import get_feature_columns
from lineupiq.features.live_feature_service import (
    compute_interaction_features,
    compute_live_context_features,
    compute_multiwindow_features,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# All 32 NFL teams for DEF position
NFL_TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
    "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
    "LV", "LAC", "LAR", "MIA", "MIN", "NE", "NO", "NYG",
    "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WAS"
]

# Team full names for DEF display
TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders"
}


@router.get("/roster", response_model=RosterResponse)
async def get_roster(
    season: int | None = Query(default=None, description="NFL season year (default: current)")
) -> RosterResponse:
    """Get current NFL roster for fantasy-relevant positions.

    Returns all players in QB, RB, WR, TE, K positions for the specified season,
    plus all 32 team defenses as synthetic "DEF" players.
    Use this to populate player dropdowns and search interfaces.

    Args:
        season: NFL season year. Defaults to current season.

    Returns:
        RosterResponse with list of PlayerRoster entries.
    """
    if season is None:
        season = nfl.get_current_season()

    df = fetch_rosters([season])

    players = [
        PlayerRoster(
            player_id=row["gsis_id"],
            name=row["full_name"],
            position=row["position"],
            team=row["team"],
            jersey_number=row.get("jersey_number"),
            height=row.get("height"),
            weight=row.get("weight"),
            college=row.get("college"),
            years_exp=row.get("years_exp"),
            headshot_url=row.get("headshot_url"),
        )
        for row in df.to_dicts()
    ]

    # Add team defenses as synthetic "players"
    for team in NFL_TEAMS:
        team_name = TEAM_NAMES.get(team, f"{team} Defense")
        players.append(
            PlayerRoster(
                player_id=f"DEF_{team}",
                name=f"{team_name} D/ST",
                position="DEF",
                team=team,
                jersey_number=None,
                height=None,
                weight=None,
                college=None,
                years_exp=None,
                headshot_url=None,
            )
        )

    return RosterResponse(season=season, players=players, count=len(players))


@router.get("/player/{player_id}/history", response_model=PlayerHistoryResponse)
async def get_player_history(
    player_id: str,
    seasons: int = Query(default=3, ge=1, le=5, description="Number of seasons to fetch"),
) -> PlayerHistoryResponse:
    """Get player's historical weekly stats for the last N seasons.

    Returns game-by-game stats sorted by most recent first. Use this to
    display player performance history and recent trends.

    Args:
        player_id: Player's gsis_id (e.g., "00-0033873" for Mahomes).
        seasons: Number of seasons to fetch (1-5, default 3).

    Returns:
        PlayerHistoryResponse with list of WeeklyStats.

    Raises:
        HTTPException: 404 if player not found in any season.
    """
    current = nfl.get_current_season()
    season_list = list(range(current - seasons + 1, current + 1))

    df = fetch_player_history(player_id, season_list)

    if df.is_empty():
        raise HTTPException(status_code=404, detail=f"No stats found for player {player_id}")

    # Get player info from first row
    first = df.row(0, named=True)

    games = [
        WeeklyStats(
            season=row["season"],
            week=row["week"],
            opponent_team=row.get("opponent_team"),
            passing_yards=row.get("passing_yards"),
            passing_tds=row.get("passing_tds"),
            interceptions=row.get("passing_interceptions"),
            rushing_yards=row.get("rushing_yards"),
            rushing_tds=row.get("rushing_tds"),
            carries=row.get("carries"),
            receiving_yards=row.get("receiving_yards"),
            receiving_tds=row.get("receiving_tds"),
            receptions=row.get("receptions"),
            fantasy_points=row.get("fantasy_points"),
        )
        for row in df.to_dicts()
    ]

    return PlayerHistoryResponse(
        player_id=player_id,
        player_name=first.get("player_display_name") or first.get("player_name") or "Unknown",
        position=first.get("position") or "Unknown",
        seasons=season_list,
        games=games,
        total_games=len(games),
    )


def _compute_rolling_stats_for_player(
    history_df: pl.DataFrame,
    window: int = 5,
) -> dict[str, float]:
    """Compute rolling stats from player's recent games.

    Args:
        history_df: Player history DataFrame with stats columns.
        window: Rolling window size (default 5, matches model training).

    Returns:
        Dict with rolling stat values.
    """
    # Sort by season/week descending to get most recent games first
    df = history_df.sort(["season", "week"], descending=True)

    # Get the most recent `window` games
    recent = df.head(window)

    if recent.is_empty():
        return {}

    # Compute means for each stat
    stats = {}
    stat_mappings = {
        f"passing_yards_roll{window}": "passing_yards",
        f"passing_tds_roll{window}": "passing_tds",
        f"rushing_yards_roll{window}": "rushing_yards",
        f"rushing_tds_roll{window}": "rushing_tds",
        f"carries_roll{window}": "carries",
        f"receiving_yards_roll{window}": "receiving_yards",
        f"receiving_tds_roll{window}": "receiving_tds",
        f"receptions_roll{window}": "receptions",
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

    return stats


def _compute_volatility_for_player(
    history_df: pl.DataFrame,
    window: int = 5,
) -> dict[str, float]:
    """Compute volatility features (std, CV) from player's recent games.

    Args:
        history_df: Player history DataFrame with stats columns.
        window: Rolling window size (default 5, matches model training).

    Returns:
        Dict with volatility feature values.
    """
    # Sort by season/week descending to get most recent games first
    df = history_df.sort(["season", "week"], descending=True)

    # Get the most recent `window` games
    recent = df.head(window)

    if len(recent) < 2:
        # Need at least 2 games for std calculation
        return {
            f"passing_yards_std{window}": 0.0,
            f"passing_yards_cv{window}": 0.0,
            f"rushing_yards_std{window}": 0.0,
            f"rushing_yards_cv{window}": 0.0,
            f"receiving_yards_std{window}": 0.0,
            f"receiving_yards_cv{window}": 0.0,
            f"receptions_std{window}": 0.0,
            f"receptions_cv{window}": 0.0,
        }

    volatility = {}
    stat_cols = ["passing_yards", "rushing_yards", "receiving_yards", "receptions"]

    for col in stat_cols:
        if col in recent.columns:
            values = recent[col].drop_nulls()
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


def _get_default_features(position: str, is_home: bool) -> dict[str, float | bool]:
    """Get default position-typical features for players with no data.

    Args:
        position: Player position (QB, RB, WR, TE).
        is_home: Whether the player is playing at home.

    Returns:
        Dict with default feature values.
    """
    base = {
        # Opponent features (neutral/average values)
        "opp_pass_defense_strength": 0.5,
        "opp_rush_defense_strength": 0.5,
        "opp_pass_yards_allowed_rank": 16.0,
        "opp_rush_yards_allowed_rank": 16.0,
        "opp_total_yards_allowed_rank": 16.0,
        # Team strength (league average)
        "team_points_roll5": 22.0,
        "team_yards_roll5": 340.0,
        "team_plays_roll5": 65.0,
        # Weather features - neutral defaults
        "temp_normalized": 0.5,
        "wind_normalized": 0.2,
        "extreme_cold": False,
        "freezing": False,
        "extreme_heat": False,
        "high_wind": False,
        "very_high_wind": False,
        "has_precip": False,
        "precip_amount": 0.0,
        # Matchup features - neutral defaults
        "home_spread": 0.0,
        "total_points": 45.0,
        "vegas_strength_diff": 0.0,
        "home_favored": False,
        "is_divisional": False,
        # Context
        "is_home": is_home,
        "is_dome": False,
        "injury_severity": 0.0,
        "on_injury_report": 0,
        # Game context features - neutral defaults
        "days_since_last_game": 7.0,
        "is_post_bye": False,
        "implied_team_total": 22.5,
        "game_script_lean": 0.0,
        # Usage features - neutral defaults
        "snap_pct_roll5": 0.5,
        "snap_pct_trend": 0.0,
        "target_share_roll5": 0.0,
        "carry_share_roll5": 0.0,
        # EPA features - neutral defaults
        "team_epa_roll5": 0.0,
        "opp_def_epa_roll5": 0.0,
        "player_epa_roll5": 0.0,
        "team_pass_epa_vs_rush_epa": 0.0,
        # Multi-window rolling features - will be overridden per position
        "passing_yards_roll3": 0.0,
        "rushing_yards_roll3": 0.0,
        "receiving_yards_roll3": 0.0,
        "receptions_roll3": 0.0,
        "passing_yards_momentum": 0.0,
        "rushing_yards_momentum": 0.0,
        "receiving_yards_momentum": 0.0,
        "receptions_momentum": 0.0,
        # Interaction features - neutral defaults
        "rush_yards_x_opp_rush_def": 0.0,
        "pass_yards_x_opp_pass_def": 0.0,
        "recv_yards_x_opp_pass_def": 0.0,
        "player_volume_x_team_pace": 0.0,
    }

    # Position-typical rolling stats and volatility
    if position == "QB":
        return {
            **base,
            "passing_yards_roll5": 250.0,
            "passing_tds_roll5": 1.8,
            "rushing_yards_roll5": 15.0,
            "rushing_tds_roll5": 0.1,
            "carries_roll5": 3.0,
            "receiving_yards_roll5": 0.0,
            "receiving_tds_roll5": 0.0,
            "receptions_roll5": 0.0,
            # QB volatility
            "passing_yards_std5": 50.0,
            "passing_yards_cv5": 0.2,
            "rushing_yards_std5": 10.0,
            "rushing_yards_cv5": 0.5,
            "receiving_yards_std5": 0.0,
            "receiving_yards_cv5": 0.0,
            "receptions_std5": 0.0,
            "receptions_cv5": 0.0,
        }

    if position == "RB":
        return {
            **base,
            "passing_yards_roll5": 0.0,
            "passing_tds_roll5": 0.0,
            "rushing_yards_roll5": 65.0,
            "rushing_tds_roll5": 0.5,
            "carries_roll5": 15.0,
            "receiving_yards_roll5": 20.0,
            "receiving_tds_roll5": 0.1,
            "receptions_roll5": 2.5,
            # RB volatility
            "passing_yards_std5": 0.0,
            "passing_yards_cv5": 0.0,
            "rushing_yards_std5": 25.0,
            "rushing_yards_cv5": 0.4,
            "receiving_yards_std5": 15.0,
            "receiving_yards_cv5": 0.6,
            "receptions_std5": 1.5,
            "receptions_cv5": 0.5,
        }

    # WR/TE default
    return {
        **base,
        "passing_yards_roll5": 0.0,
        "passing_tds_roll5": 0.0,
        "rushing_yards_roll5": 2.0,
        "rushing_tds_roll5": 0.0,
        "carries_roll5": 0.3,
        "receiving_yards_roll5": 55.0,
        "receiving_tds_roll5": 0.4,
        "receptions_roll5": 4.0,
        # WR/TE volatility
        "passing_yards_std5": 0.0,
        "passing_yards_cv5": 0.0,
        "rushing_yards_std5": 5.0,
        "rushing_yards_cv5": 0.5,
        "receiving_yards_std5": 30.0,
        "receiving_yards_cv5": 0.5,
        "receptions_std5": 2.0,
        "receptions_cv5": 0.4,
    }


def _get_opponent_strength(opponent_team: str | None) -> dict[str, float]:
    """Get opponent defensive strength features from cached rankings.

    Looks up actual defensive rankings computed from historical data,
    using the same logic as the training pipeline (opponent_features.py).
    Falls back to neutral defaults only if no opponent is specified or
    ranking data is unavailable.

    Args:
        opponent_team: Opponent team abbreviation (or None).

    Returns:
        Dict with opponent strength features.
    """
    if opponent_team is None:
        return {
            "opp_pass_defense_strength": 0.5,
            "opp_rush_defense_strength": 0.5,
            "opp_pass_yards_allowed_rank": 16.0,
            "opp_rush_yards_allowed_rank": 16.0,
            "opp_total_yards_allowed_rank": 16.0,
        }

    return get_latest_opponent_strength(opponent_team)


def _get_team_strength(team: str) -> dict[str, float]:
    """Get team offensive strength features from cached data.

    Looks up actual team offensive metrics computed from historical data,
    using the same logic as the training pipeline (team_strength.py).
    Falls back to league average defaults only if data is unavailable.

    Args:
        team: Team abbreviation.

    Returns:
        Dict with team strength features.
    """
    return get_latest_team_strength(team)


@router.get("/player/{player_id}/features", response_model=PlayerFeaturesResponse)
async def get_player_features(
    player_id: str,
    opponent_team: str | None = Query(
        default=None, description="Opponent team abbreviation (e.g., DAL)"
    ),
    is_home: bool = Query(default=True, description="Whether player is at home"),
) -> PlayerFeaturesResponse:
    """Get player-specific features for prediction.

    Computes feature values based on the player's historical performance,
    ready to be used as input to the prediction models. This allows for
    differentiated predictions based on actual player stats rather than
    position-typical defaults.

    Args:
        player_id: Player's gsis_id (e.g., "00-0036389" for Jalen Hurts).
        opponent_team: Optional opponent team for opponent strength features.
        is_home: Whether the player is playing at home (default True).

    Returns:
        PlayerFeaturesResponse with computed feature values.

    Raises:
        HTTPException: 404 if player not found.
    """
    logger.info(f"Computing features for player {player_id}, opponent={opponent_team}")

    # Fetch player history (last 2 seasons for sufficient data)
    current = nfl.get_current_season()
    season_list = [current - 1, current]

    history_df = fetch_player_history(player_id, season_list)

    if history_df.is_empty():
        raise HTTPException(
            status_code=404,
            detail=f"No stats found for player {player_id}",
        )

    # Get player metadata
    first = history_df.row(0, named=True)
    player_name = first.get("player_display_name") or first.get("player_name") or "Unknown"
    position = first.get("position") or "Unknown"

    # Try to get team from most recent game
    team = "UNK"
    roster_df = fetch_rosters([current])
    player_roster = roster_df.filter(pl.col("gsis_id") == player_id)
    if not player_roster.is_empty():
        team = player_roster.row(0, named=True).get("team", "UNK")

    # Compute number of games available
    games_available = len(history_df)
    has_sufficient_data = games_available >= 3

    if has_sufficient_data:
        # Compute player-specific features from history
        rolling_stats = _compute_rolling_stats_for_player(history_df)
        volatility = _compute_volatility_for_player(history_df)

        # Get context features
        opponent_features = _get_opponent_strength(opponent_team)
        team_features = _get_team_strength(team)

        # Compute context features using shared live feature service.
        context_features = compute_live_context_features(
            history_df=history_df,
            player_id=player_id,
            team=team,
            season=current,
            opponent_team=opponent_team,
            is_home=is_home,
            rolling_window=5,
        )

        # Build one-row frame to reuse shared multi-window + interaction logic.
        one_row = pl.DataFrame([
            {
                "player_id": player_id,
                "season": current,
                "week": int(history_df.select("week").max().item() or 0),
                "passing_yards": float(rolling_stats.get("passing_yards_roll5", 0.0)),
                "rushing_yards": float(rolling_stats.get("rushing_yards_roll5", 0.0)),
                "receiving_yards": float(rolling_stats.get("receiving_yards_roll5", 0.0)),
                "receptions": float(rolling_stats.get("receptions_roll5", 0.0)),
                "passing_yards_roll5": float(rolling_stats.get("passing_yards_roll5", 0.0)),
                "rushing_yards_roll5": float(rolling_stats.get("rushing_yards_roll5", 0.0)),
                "receiving_yards_roll5": float(rolling_stats.get("receiving_yards_roll5", 0.0)),
                "receptions_roll5": float(rolling_stats.get("receptions_roll5", 0.0)),
                "carries_roll5": float(rolling_stats.get("carries_roll5", 0.0)),
                "opp_pass_defense_strength": float(opponent_features.get("opp_pass_defense_strength", 0.5)),
                "opp_rush_defense_strength": float(opponent_features.get("opp_rush_defense_strength", 0.5)),
                "team_plays_roll5": float(team_features.get("team_plays_roll5", 65.0)),
            }
        ])
        one_row, _ = compute_multiwindow_features(one_row, rolling_window=5, short_window=3)
        one_row, _ = compute_interaction_features(one_row, rolling_window=5)
        one_row_dict = one_row.row(0, named=True)

        # Combine all features (64 features total)
        features: dict[str, float | bool] = {
            **rolling_stats,
            **volatility,
            **opponent_features,
            **team_features,
            **context_features,
            # Context features
            "is_home": is_home,
            "is_dome": False,
            "injury_severity": 0.0,
            "on_injury_report": 0,
            # Multi-window rolling features
            "passing_yards_roll3": float(one_row_dict.get("passing_yards_roll3", 0.0)),
            "rushing_yards_roll3": float(one_row_dict.get("rushing_yards_roll3", 0.0)),
            "receiving_yards_roll3": float(one_row_dict.get("receiving_yards_roll3", 0.0)),
            "receptions_roll3": float(one_row_dict.get("receptions_roll3", 0.0)),
            "passing_yards_momentum": float(one_row_dict.get("passing_yards_momentum", 0.0)),
            "rushing_yards_momentum": float(one_row_dict.get("rushing_yards_momentum", 0.0)),
            "receiving_yards_momentum": float(one_row_dict.get("receiving_yards_momentum", 0.0)),
            "receptions_momentum": float(one_row_dict.get("receptions_momentum", 0.0)),
            # Interaction features
            "rush_yards_x_opp_rush_def": float(one_row_dict.get("rush_yards_x_opp_rush_def", 0.0)),
            "pass_yards_x_opp_pass_def": float(one_row_dict.get("pass_yards_x_opp_pass_def", 0.0)),
            "recv_yards_x_opp_pass_def": float(one_row_dict.get("recv_yards_x_opp_pass_def", 0.0)),
            "player_volume_x_team_pace": float(one_row_dict.get("player_volume_x_team_pace", 0.0)),
        }
    else:
        # Not enough data - use position defaults but merge any available stats
        features = _get_default_features(position, is_home)

        # Override with actual stats if we have any games
        if games_available > 0:
            rolling_stats = _compute_rolling_stats_for_player(history_df)
            volatility = _compute_volatility_for_player(history_df)
            features.update(rolling_stats)
            features.update(volatility)

    logger.info(
        f"Computed features for {player_name}: {games_available} games, "
        f"sufficient_data={has_sufficient_data}"
    )

    # Keep serving contract aligned with training feature schema.
    for feature_name in get_feature_columns():
        if feature_name not in features:
            # Most engineered features are numeric; booleans are represented
            # by explicit defaults in _get_default_features.
            features[feature_name] = 0.0

    return PlayerFeaturesResponse(
        player_id=player_id,
        player_name=player_name,
        position=position,
        team=team,
        games_available=games_available,
        features=features,
        has_sufficient_data=has_sufficient_data,
    )
