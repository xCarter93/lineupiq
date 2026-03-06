"""PFR advanced feature engineering."""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_pfr_advstats

logger = logging.getLogger(__name__)

PFR_COLUMNS = [
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


def add_pfr_features(df: pl.DataFrame, seasons: list[int]) -> pl.DataFrame:
    """Join PFR advanced features for pass/rush/rec contexts."""
    out = df
    out = _join(out, seasons, "pass", _pass_map())
    out = _join(out, seasons, "rec", _rec_map())
    out = _join(out, seasons, "rush", _rush_map())
    for col in PFR_COLUMNS:
        if col not in out.columns:
            out = out.with_columns(pl.lit(0.0).alias(col))
        else:
            out = out.with_columns(pl.col(col).fill_null(0.0))
    return out


def get_pfr_columns() -> list[str]:
    return PFR_COLUMNS


def _join(df: pl.DataFrame, seasons: list[int], stat_type: str, mapping: dict[str, str]) -> pl.DataFrame:
    try:
        pfr = fetch_pfr_advstats(seasons, stat_type=stat_type)  # type: ignore[arg-type]
    except Exception:
        return df
    if pfr.is_empty():
        return df

    id_col = None
    for candidate in ["player_gsis_id", "player_id", "gsis_id"]:
        if candidate in pfr.columns:
            id_col = candidate
            break
    if id_col is None:
        return df

    cols = [id_col, "season", "week"] + [c for c in mapping if c in pfr.columns]
    if len(cols) <= 3:
        return df
    sub = pfr.select(cols).rename({id_col: "player_id", **{k: v for k, v in mapping.items() if k in pfr.columns}})
    return df.join(sub, on=["player_id", "season", "week"], how="left")


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
