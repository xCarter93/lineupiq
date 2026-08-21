"""Next Gen Stats feature engineering.

NGS values describe how a player performed *in* a game, so they are joined on the
current week and then lagged into prior-game rolling averages before use.
"""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_nextgen_stats
from lineupiq.data.normalization import prepare_weekly_join
from lineupiq.features.rolling_stats import add_lagged_rolling

logger = logging.getLogger(__name__)


NEXTGEN_STATS = [
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


def add_nextgen_features(df: pl.DataFrame, seasons: list[int], window: int = 5) -> pl.DataFrame:
    """Join Next Gen Stats for passing, receiving and rushing as lagged rolling means."""
    try:
        passing = fetch_nextgen_stats(seasons, "passing")
        receiving = fetch_nextgen_stats(seasons, "receiving")
        rushing = fetch_nextgen_stats(seasons, "rushing")
    except Exception as exc:
        logger.warning("Failed to fetch nextgen stats: %s", exc)
        return _add_defaults(df, window)

    out = df
    out = _join_ngs(out, passing, _passing_map())
    out = _join_ngs(out, receiving, _receiving_map())
    out = _join_ngs(out, rushing, _rushing_map())

    # Keep the schema stable when a source is missing a stat entirely.
    missing = [c for c in NEXTGEN_STATS if c not in out.columns]
    if missing:
        out = out.with_columns([pl.lit(None, dtype=pl.Float64).alias(c) for c in missing])

    return add_lagged_rolling(out, NEXTGEN_STATS, window)


def get_nextgen_columns(window: int = 5) -> list[str]:
    return [f"{col}_roll{window}" for col in NEXTGEN_STATS]


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

    present = {k: v for k, v in feature_map.items() if k in ngs.columns}
    if not present:
        return df

    join_df = (
        ngs.select([id_col, "season", "week", *present.keys()])
        .rename({id_col: "player_id", **present})
        # Week 0 rows are season aggregates, not games.
        .filter(pl.col("week") > 0)
    )
    return df.join(prepare_weekly_join(join_df, df), on=["player_id", "season", "week"], how="left")


def _add_defaults(df: pl.DataFrame, window: int) -> pl.DataFrame:
    return df.with_columns([pl.lit(0.0).alias(col) for col in get_nextgen_columns(window)])


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
