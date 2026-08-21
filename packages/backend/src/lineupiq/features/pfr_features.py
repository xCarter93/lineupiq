"""PFR advanced feature engineering.

PFR weekly stats are keyed on `pfr_player_id` and describe in-game outcomes, so
they are mapped to GSIS ids via the player crosswalk and then lagged.
"""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_pfr_advstats
from lineupiq.data.ids import add_gsis_player_id
from lineupiq.data.normalization import prepare_weekly_join
from lineupiq.features.rolling_stats import add_lagged_rolling

logger = logging.getLogger(__name__)

PFR_STATS = [
    "pfr_times_pressured",
    "pfr_times_hit",
    "pfr_times_blitzed",
    "pfr_passing_bad_throws",
    "pfr_passing_drop_pct",
    "pfr_receiving_drop",
    "pfr_receiving_broken_tackles",
    "pfr_rushing_broken_tackles",
    "pfr_rushing_yards_before_contact",
]


def add_pfr_features(df: pl.DataFrame, seasons: list[int], window: int = 5) -> pl.DataFrame:
    """Join PFR advanced stats for pass/rush/rec contexts as lagged rolling means."""
    out = df
    out = _join(out, seasons, "pass", _pass_map())
    out = _join(out, seasons, "rec", _rec_map())
    out = _join(out, seasons, "rush", _rush_map())

    missing = [c for c in PFR_STATS if c not in out.columns]
    if missing:
        out = out.with_columns([pl.lit(None, dtype=pl.Float64).alias(c) for c in missing])

    return add_lagged_rolling(out, PFR_STATS, window)


def get_pfr_columns(window: int = 5) -> list[str]:
    return [f"{col}_roll{window}" for col in PFR_STATS]


def _join(
    df: pl.DataFrame,
    seasons: list[int],
    stat_type: str,
    mapping: dict[str, str],
) -> pl.DataFrame:
    try:
        pfr = fetch_pfr_advstats(seasons, stat_type=stat_type)  # type: ignore[arg-type]
        if pfr.is_empty():
            return df
        present = {k: v for k, v in mapping.items() if k in pfr.columns}
        if not present:
            logger.warning("PFR %s stats missing expected columns", stat_type)
            return df
        sub = add_gsis_player_id(pfr.select(["pfr_player_id", "season", "week", *present.keys()]))
    except Exception as exc:
        logger.warning("Failed to add PFR %s features: %s", stat_type, exc)
        return df

    sub = sub.drop("pfr_player_id").rename(present)
    return df.join(prepare_weekly_join(sub, df), on=["player_id", "season", "week"], how="left")


def _pass_map() -> dict[str, str]:
    return {
        "times_pressured": "pfr_times_pressured",
        "times_hit": "pfr_times_hit",
        "times_blitzed": "pfr_times_blitzed",
        "passing_bad_throws": "pfr_passing_bad_throws",
        "passing_drop_pct": "pfr_passing_drop_pct",
    }


def _rec_map() -> dict[str, str]:
    return {
        "receiving_drop": "pfr_receiving_drop",
        "receiving_broken_tackles": "pfr_receiving_broken_tackles",
    }


def _rush_map() -> dict[str, str]:
    return {
        "rushing_broken_tackles": "pfr_rushing_broken_tackles",
        "rushing_yards_before_contact": "pfr_rushing_yards_before_contact",
    }
