"""Next Gen Stats feature engineering."""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_nextgen_stats

logger = logging.getLogger(__name__)


NEXTGEN_FEATURES = [
    "ngs_cpoe",
    "ngs_avg_time_to_throw",
    "ngs_avg_intended_air_yards",
    "ngs_aggressiveness",
    "ngs_avg_separation",
    "ngs_avg_cushion",
    "ngs_air_yards_share",
    "ngs_avg_yac_above_expectation",
    "ngs_ryoe",
    "ngs_efficiency",
    "ngs_avg_time_to_los",
    "ngs_dib_pct",
]


def add_nextgen_features(df: pl.DataFrame, seasons: list[int]) -> pl.DataFrame:
    """Join Next Gen Stats features for passing, receiving, and rushing."""
    try:
        passing = fetch_nextgen_stats(seasons, "passing")
        receiving = fetch_nextgen_stats(seasons, "receiving")
        rushing = fetch_nextgen_stats(seasons, "rushing")
    except Exception as exc:
        logger.warning("Failed to fetch nextgen stats: %s", exc)
        return _add_defaults(df)

    out = df
    out = _join_ngs(out, passing, _passing_map())
    out = _join_ngs(out, receiving, _receiving_map())
    out = _join_ngs(out, rushing, _rushing_map())
    for col in NEXTGEN_FEATURES:
        if col not in out.columns:
            out = out.with_columns(pl.lit(0.0).alias(col))
        else:
            out = out.with_columns(pl.col(col).fill_null(0.0))
    return out


def get_nextgen_columns() -> list[str]:
    return NEXTGEN_FEATURES


def _join_ngs(df: pl.DataFrame, ngs: pl.DataFrame, feature_map: dict[str, str]) -> pl.DataFrame:
    if ngs.is_empty():
        return df

    id_col = None
    for candidate in ["player_gsis_id", "player_id", "gsis_id"]:
        if candidate in ngs.columns:
            id_col = candidate
            break
    if id_col is None:
        return df

    cols = [id_col, "season", "week"] + [c for c in feature_map.keys() if c in ngs.columns]
    if len(cols) <= 3:
        return df

    join_df = ngs.select(cols).rename({id_col: "player_id", **{k: v for k, v in feature_map.items() if k in ngs.columns}})
    return df.join(join_df, on=["player_id", "season", "week"], how="left")


def _add_defaults(df: pl.DataFrame) -> pl.DataFrame:
    out = df
    for col in NEXTGEN_FEATURES:
        out = out.with_columns(pl.lit(0.0).alias(col))
    return out


def _passing_map() -> dict[str, str]:
    return {
        "completion_percentage_above_expectation": "ngs_cpoe",
        "avg_time_to_throw": "ngs_avg_time_to_throw",
        "avg_intended_air_yards": "ngs_avg_intended_air_yards",
        "aggressiveness": "ngs_aggressiveness",
    }


def _receiving_map() -> dict[str, str]:
    return {
        "avg_separation": "ngs_avg_separation",
        "avg_cushion": "ngs_avg_cushion",
        "percent_share_of_intended_air_yards": "ngs_air_yards_share",
        "avg_yac_above_expectation": "ngs_avg_yac_above_expectation",
    }


def _rushing_map() -> dict[str, str]:
    return {
        "rush_yards_over_expected": "ngs_ryoe",
        "efficiency": "ngs_efficiency",
        "avg_time_to_los": "ngs_avg_time_to_los",
        "percent_attempts_gte_eight_defenders": "ngs_dib_pct",
    }
