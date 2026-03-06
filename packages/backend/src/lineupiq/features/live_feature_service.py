"""
Shared feature service utilities used by both training and serving paths.

This module centralizes feature logic that was previously duplicated in:
- features/pipeline.py (training feature generation)
- api/routes/roster.py (live per-player feature generation)
"""

from __future__ import annotations

import os
from functools import lru_cache

import nflreadpy as nfl
import polars as pl

from lineupiq.data.fetchers import fetch_schedules, fetch_snap_counts
from lineupiq.data.odds_cache import OddsClient
from lineupiq.features.epa_features import get_epa_columns
from lineupiq.features.matchup import engineer_matchup_features
from lineupiq.features.weather import engineer_weather_features


def compute_multiwindow_features(
    df: pl.DataFrame,
    rolling_window: int = 5,
    short_window: int = 3,
) -> tuple[pl.DataFrame, list[str]]:
    """Compute 3-game rolling and momentum features."""
    stat_cols = ["passing_yards", "rushing_yards", "receiving_yards", "receptions"]
    result = df

    for stat_col in stat_cols:
        if stat_col not in result.columns:
            continue

        roll3_col = f"{stat_col}_roll{short_window}"
        roll5_col = f"{stat_col}_roll{rolling_window}"
        momentum_col = f"{stat_col}_momentum"

        result = result.sort(["player_id", "season", "week"]).with_columns(
            pl.col(stat_col)
            .shift(1)
            .rolling_mean(window_size=short_window, min_samples=1)
            .over("player_id")
            .fill_null(0.0)
            .alias(roll3_col)
        )

        if roll5_col in result.columns:
            result = result.with_columns(
                (pl.col(roll3_col) - pl.col(roll5_col)).fill_null(0.0).alias(momentum_col)
            )
        else:
            result = result.with_columns(pl.lit(0.0).alias(momentum_col))

    features = [f"{s}_roll{short_window}" for s in stat_cols] + [f"{s}_momentum" for s in stat_cols]
    return result, features


def compute_interaction_features(
    df: pl.DataFrame,
    rolling_window: int = 5,
) -> tuple[pl.DataFrame, list[str]]:
    """Compute interaction features used by both train and serve."""
    result = df
    interaction_cols: list[str] = []

    if f"rushing_yards_roll{rolling_window}" in result.columns and "opp_rush_defense_strength" in result.columns:
        result = result.with_columns(
            (pl.col(f"rushing_yards_roll{rolling_window}") * pl.col("opp_rush_defense_strength"))
            .fill_null(0.0)
            .alias("rush_yards_x_opp_rush_def")
        )
        interaction_cols.append("rush_yards_x_opp_rush_def")

    if f"passing_yards_roll{rolling_window}" in result.columns and "opp_pass_defense_strength" in result.columns:
        result = result.with_columns(
            (pl.col(f"passing_yards_roll{rolling_window}") * pl.col("opp_pass_defense_strength"))
            .fill_null(0.0)
            .alias("pass_yards_x_opp_pass_def")
        )
        interaction_cols.append("pass_yards_x_opp_pass_def")

    if f"receiving_yards_roll{rolling_window}" in result.columns and "opp_pass_defense_strength" in result.columns:
        result = result.with_columns(
            (pl.col(f"receiving_yards_roll{rolling_window}") * pl.col("opp_pass_defense_strength"))
            .fill_null(0.0)
            .alias("recv_yards_x_opp_pass_def")
        )
        interaction_cols.append("recv_yards_x_opp_pass_def")

    if f"carries_roll{rolling_window}" in result.columns and f"team_plays_roll{rolling_window}" in result.columns:
        result = result.with_columns(
            (pl.col(f"carries_roll{rolling_window}") * pl.col(f"team_plays_roll{rolling_window}"))
            .fill_null(0.0)
            .alias("player_volume_x_team_pace")
        )
        interaction_cols.append("player_volume_x_team_pace")

    return result, interaction_cols


def compute_live_context_features(
    history_df: pl.DataFrame,
    player_id: str,
    team: str,
    season: int,
    opponent_team: str | None,
    is_home: bool,
    rolling_window: int = 5,
) -> dict[str, float | bool]:
    """Compute non-rolling live features using real data where possible."""
    features: dict[str, float | bool] = {
        "temp_normalized": 0.5,
        "wind_normalized": 0.2,
        "extreme_cold": False,
        "freezing": False,
        "extreme_heat": False,
        "high_wind": False,
        "very_high_wind": False,
        "has_precip": False,
        "precip_amount": 0.0,
        "home_spread": 0.0,
        "total_points": 45.0,
        "vegas_strength_diff": 0.0,
        "home_favored": False,
        "is_divisional": False,
        "days_since_last_game": 7.0,
        "is_post_bye": False,
        "implied_team_total": 22.5,
        "game_script_lean": 0.0,
        "snap_pct_roll5": 0.5,
        "snap_pct_trend": 0.0,
        "target_share_roll5": 0.0,
        "carry_share_roll5": 0.0,
        "team_epa_roll5": 0.0,
        "opp_def_epa_roll5": 0.0,
        "player_epa_roll5": 0.0,
        "team_pass_epa_vs_rush_epa": 0.0,
    }

    # Usage from snap counts + recent shares
    features.update(_compute_usage_features(player_id, history_df, season, rolling_window))
    # Weather/matchup/rest/game script from schedules (+ odds if configured)
    features.update(_compute_schedule_features(team, season, opponent_team, is_home))
    # EPA from cached PBP aggregates
    features.update(_compute_latest_epa_features(player_id, team, opponent_team, season))
    return features


def _compute_usage_features(
    player_id: str,
    history_df: pl.DataFrame,
    season: int,
    rolling_window: int,
) -> dict[str, float]:
    usage = {
        "snap_pct_roll5": 0.5,
        "snap_pct_trend": 0.0,
        "target_share_roll5": 0.0,
        "carry_share_roll5": 0.0,
    }

    try:
        snaps = fetch_snap_counts([season - 1, season])
        id_col = "player_id" if "player_id" in snaps.columns else "gsis_id"
        if id_col in snaps.columns and "offense_pct" in snaps.columns:
            player_snaps = (
                snaps.filter(pl.col(id_col) == player_id)
                .sort(["season", "week"])
                .tail(rolling_window)
            )
            if not player_snaps.is_empty():
                usage["snap_pct_roll5"] = float(player_snaps["offense_pct"].mean())
                recent_3 = player_snaps.tail(3)
                usage["snap_pct_trend"] = float(recent_3["offense_pct"].mean() - player_snaps["offense_pct"].mean())
    except Exception:
        pass

    try:
        recent = history_df.sort(["season", "week"], descending=True).head(rolling_window)
        if not recent.is_empty() and "team" in recent.columns:
            team_week = recent.select(["team", "season", "week"]).unique()
            season_stats = nfl.load_player_stats(seasons=[season - 1, season], summary_level="week")
            team_stats = season_stats.join(team_week, on=["team", "season", "week"], how="inner")
            if "targets" in recent.columns and "targets" in team_stats.columns:
                player_targets = float(recent["targets"].fill_null(0).sum())
                team_targets = float(team_stats["targets"].fill_null(0).sum())
                usage["target_share_roll5"] = player_targets / team_targets if team_targets > 0 else 0.0
            if "carries" in recent.columns and "carries" in team_stats.columns:
                player_carries = float(recent["carries"].fill_null(0).sum())
                team_carries = float(team_stats["carries"].fill_null(0).sum())
                usage["carry_share_roll5"] = player_carries / team_carries if team_carries > 0 else 0.0
    except Exception:
        pass

    return usage


def _compute_schedule_features(
    team: str,
    season: int,
    opponent_team: str | None,
    is_home: bool,
) -> dict[str, float | bool]:
    out: dict[str, float | bool] = {}
    try:
        schedules = fetch_schedules([season])
        with_weather = engineer_weather_features(schedules)

        odds_df = None
        odds_key = os.getenv("ODDS_API_KEY")
        if odds_key and "gameday" in schedules.columns:
            odds_client = OddsClient(api_key=odds_key)
            odds_rows = []
            unique_days = schedules.select("gameday").drop_nulls().unique().sort("gameday")
            for row in unique_days.iter_rows(named=True):
                gameday = row["gameday"]
                date_str = gameday if isinstance(gameday, str) else gameday.strftime("%Y-%m-%d")
                try:
                    odds_rows.extend(odds_client.get_historical_odds(date_str))
                except Exception:
                    continue
            if odds_rows:
                odds_df = odds_client.parse_odds(odds_rows)

        with_matchup = engineer_matchup_features(with_weather, odds_df=odds_df)

        team_games = with_matchup.filter(
            (pl.col("home_team") == team) | (pl.col("away_team") == team)
        ).sort(["season", "week"])

        if team_games.is_empty():
            return out

        selected = None
        if opponent_team:
            selected_games = team_games.filter(
                ((pl.col("home_team") == team) & (pl.col("away_team") == opponent_team))
                | ((pl.col("away_team") == team) & (pl.col("home_team") == opponent_team))
            )
            if not selected_games.is_empty():
                selected = selected_games.sort(["season", "week"], descending=True).row(0, named=True)

        if selected is None:
            selected = team_games.sort(["season", "week"], descending=True).row(0, named=True)

        for col in [
            "temp_normalized",
            "wind_normalized",
            "extreme_cold",
            "freezing",
            "extreme_heat",
            "high_wind",
            "very_high_wind",
            "has_precip",
            "precip_amount",
            "home_spread",
            "total_points",
            "vegas_strength_diff",
            "home_favored",
            "is_divisional",
        ]:
            if col in selected:
                out[col] = selected[col]

        # days_since_last_game / post-bye from last two played games
        if "gameday" in team_games.columns and len(team_games) >= 2:
            latest = team_games.sort(["season", "week"], descending=True).head(2)
            g1 = latest.row(0, named=True).get("gameday")
            g2 = latest.row(1, named=True).get("gameday")
            if g1 is not None and g2 is not None and hasattr(g1, "__sub__"):
                days = float((g1 - g2).days)
                out["days_since_last_game"] = days
                out["is_post_bye"] = days >= 12

        # implied team total / game script
        total = float(out.get("total_points", 45.0))
        spread = float(out.get("home_spread", 0.0))
        implied = (total - spread) / 2 if is_home else (total + spread) / 2
        game_script = spread if is_home else -spread
        out["implied_team_total"] = implied
        out["game_script_lean"] = game_script
    except Exception:
        return out

    return out


@lru_cache(maxsize=8)
def _build_epa_tables(season: int) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    pbp = nfl.load_pbp([season - 1, season])
    if not isinstance(pbp, pl.DataFrame):
        pbp = pl.from_pandas(pbp)
    pbp = pbp.filter(pl.col("play_type").is_in(["pass", "run"]))

    team_col = "posteam" if "posteam" in pbp.columns else "offense_team"
    def_col = "defteam" if "defteam" in pbp.columns else None

    team_weekly = (
        pbp.group_by([team_col, "season", "week"])
        .agg(pl.col("epa").mean().alias("team_epa_per_play"))
        .rename({team_col: "team"})
        .sort(["team", "season", "week"])
        .with_columns(
            pl.col("team_epa_per_play")
            .shift(1)
            .rolling_mean(window_size=5, min_samples=1)
            .over("team")
            .fill_null(0.0)
            .alias("team_epa_roll5")
        )
    )

    if def_col:
        def_weekly = (
            pbp.group_by([def_col, "season", "week"])
            .agg(pl.col("epa").mean().alias("def_epa_per_play"))
            .rename({def_col: "team"})
            .sort(["team", "season", "week"])
            .with_columns(
                pl.col("def_epa_per_play")
                .shift(1)
                .rolling_mean(window_size=5, min_samples=1)
                .over("team")
                .fill_null(0.0)
                .alias("opp_def_epa_roll5")
            )
        )
    else:
        def_weekly = pl.DataFrame({"team": [], "season": [], "week": [], "opp_def_epa_roll5": []})

    pieces = []
    for pid_col in ["passer_player_id", "receiver_player_id", "rusher_player_id"]:
        if pid_col in pbp.columns:
            pieces.append(
                pbp.filter(pl.col(pid_col).is_not_null())
                .group_by([pid_col, "season", "week"])
                .agg(pl.col("epa").mean().alias("player_epa_per_play"))
                .rename({pid_col: "player_id"})
            )
    if pieces:
        player_weekly = (
            pl.concat(pieces)
            .group_by(["player_id", "season", "week"])
            .agg(pl.col("player_epa_per_play").mean())
            .sort(["player_id", "season", "week"])
            .with_columns(
                pl.col("player_epa_per_play")
                .shift(1)
                .rolling_mean(window_size=5, min_samples=1)
                .over("player_id")
                .fill_null(0.0)
                .alias("player_epa_roll5")
            )
        )
    else:
        player_weekly = pl.DataFrame({"player_id": [], "season": [], "week": [], "player_epa_roll5": []})

    return team_weekly, def_weekly, player_weekly


def _compute_latest_epa_features(
    player_id: str,
    team: str,
    opponent_team: str | None,
    season: int,
) -> dict[str, float]:
    features = {col: 0.0 for col in get_epa_columns()}
    try:
        team_weekly, def_weekly, player_weekly = _build_epa_tables(season)
        team_latest = team_weekly.filter(pl.col("team") == team).sort(["season", "week"], descending=True)
        if not team_latest.is_empty():
            row = team_latest.row(0, named=True)
            features["team_epa_roll5"] = float(row.get("team_epa_roll5", 0.0))
        if opponent_team:
            opp_latest = def_weekly.filter(pl.col("team") == opponent_team).sort(["season", "week"], descending=True)
            if not opp_latest.is_empty():
                row = opp_latest.row(0, named=True)
                features["opp_def_epa_roll5"] = float(row.get("opp_def_epa_roll5", 0.0))
        player_latest = player_weekly.filter(pl.col("player_id") == player_id).sort(["season", "week"], descending=True)
        if not player_latest.is_empty():
            row = player_latest.row(0, named=True)
            features["player_epa_roll5"] = float(row.get("player_epa_roll5", 0.0))
    except Exception:
        pass
    return features
