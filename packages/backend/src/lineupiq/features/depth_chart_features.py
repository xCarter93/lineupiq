"""Depth chart and hierarchy features."""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_depth_charts

logger = logging.getLogger(__name__)


DEPTH_COLUMNS = ["depth_rank", "is_starter"]


def add_depth_chart_features(df: pl.DataFrame, seasons: list[int]) -> pl.DataFrame:
    """Join depth chart rank features (starter/backup encoding)."""
    try:
        depth = fetch_depth_charts(seasons)
    except Exception as exc:
        logger.warning("Failed to fetch depth chart data: %s", exc)
        return _defaults(df)

    if depth.is_empty():
        return _defaults(df)

    id_col = None
    for candidate in ["player_gsis_id", "player_id", "gsis_id"]:
        if candidate in depth.columns:
            id_col = candidate
            break
    if id_col is None:
        return _defaults(df)

    rank_col = "depth_team_order"
    if rank_col not in depth.columns:
        for candidate in ["depth_order", "depth_rank", "position_rank"]:
            if candidate in depth.columns:
                rank_col = candidate
                break

    join_cols = [id_col, "season", "week"]
    select_cols = [c for c in [rank_col] if c in depth.columns]
    if not select_cols:
        return _defaults(df)

    join_df = depth.select(join_cols + select_cols).rename({id_col: "player_id", rank_col: "depth_rank"})
    out = df.join(join_df, on=["player_id", "season", "week"], how="left")
    out = out.with_columns(
        pl.col("depth_rank").cast(pl.Float64).fill_null(3.0),
        (pl.col("depth_rank").fill_null(3) <= 1).cast(pl.Int8).alias("is_starter"),
    )
    return out


def get_depth_chart_columns() -> list[str]:
    return DEPTH_COLUMNS


def _defaults(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(3.0).alias("depth_rank"),
        pl.lit(0).alias("is_starter"),
    )
