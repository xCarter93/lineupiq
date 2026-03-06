"""Expected fantasy point opportunity features (xFP)."""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_ff_opportunity

logger = logging.getLogger(__name__)

OPPORTUNITY_COLUMNS = [
    "xfp_rush",
    "xfp_rec",
    "xfp_total",
    "xfp_efficiency_delta",
]


def add_opportunity_features(df: pl.DataFrame, seasons: list[int]) -> pl.DataFrame:
    """Join weekly xFP features from nflreadpy opportunity dataset."""
    try:
        opp = fetch_ff_opportunity(seasons, stat_type="weekly")
    except Exception as exc:
        logger.warning("Failed to fetch xFP data: %s", exc)
        return _with_defaults(df)

    if opp.is_empty():
        return _with_defaults(df)

    id_col = None
    for candidate in ["player_gsis_id", "player_id", "gsis_id"]:
        if candidate in opp.columns:
            id_col = candidate
            break
    if id_col is None:
        return _with_defaults(df)

    base = opp.select(
        [
            id_col,
            "season",
            "week",
            *[c for c in ["rec_fantasy_points_exp", "rush_fantasy_points_exp"] if c in opp.columns],
        ]
    ).rename({id_col: "player_id", "rec_fantasy_points_exp": "xfp_rec", "rush_fantasy_points_exp": "xfp_rush"})

    out = df.join(base, on=["player_id", "season", "week"], how="left")
    out = out.with_columns(
        (pl.col("xfp_rush").fill_null(0.0) + pl.col("xfp_rec").fill_null(0.0)).alias("xfp_total")
    )

    # Compare expected production to realized fantasy points where available.
    if "fantasy_points_ppr" in out.columns:
        out = out.with_columns(
            (pl.col("fantasy_points_ppr").fill_null(0.0) - pl.col("xfp_total")).alias("xfp_efficiency_delta")
        )
    else:
        out = out.with_columns(pl.lit(0.0).alias("xfp_efficiency_delta"))

    for col in OPPORTUNITY_COLUMNS:
        out = out.with_columns(pl.col(col).fill_null(0.0))
    return out


def get_opportunity_columns() -> list[str]:
    return OPPORTUNITY_COLUMNS


def _with_defaults(df: pl.DataFrame) -> pl.DataFrame:
    out = df
    for col in OPPORTUNITY_COLUMNS:
        out = out.with_columns(pl.lit(0.0).alias(col))
    return out
