"""Depth chart and hierarchy features.

Depth charts are published before kickoff, so they are used at their own week
(no lag). nflverse changed the schema in 2025: seasons through 2024 carry
season/week rows with a `depth_team` rank, 2025+ carries dated snapshots with a
`pos_rank`, so both layouts are handled and the snapshot rows are resolved to the
last snapshot taken before the week's first game.
"""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_depth_charts
from lineupiq.data.normalization import prepare_weekly_join

logger = logging.getLogger(__name__)


DEPTH_COLUMNS = ["depth_rank", "is_starter"]

RANK_SCHEMA = {
    "player_id": pl.String,
    "season": pl.Int32,
    "week": pl.Int32,
    "depth_rank": pl.Float64,
}


def add_depth_chart_features(
    df: pl.DataFrame,
    seasons: list[int],
    schedules: pl.DataFrame,
) -> pl.DataFrame:
    """Join depth chart rank features (starter/backup encoding)."""
    try:
        depth = fetch_depth_charts(seasons)
        ranks = pl.concat([_weekly_ranks(depth), _snapshot_ranks(depth, schedules)])
    except Exception as exc:
        logger.warning("Failed to fetch depth chart data: %s", exc)
        return _defaults(df)

    if ranks.is_empty():
        logger.warning("No usable depth chart ranks found, using defaults")
        return _defaults(df)

    out = df.join(prepare_weekly_join(ranks, df), on=["player_id", "season", "week"], how="left")
    out = out.with_columns(pl.col("depth_rank").fill_null(3.0))
    return out.with_columns((pl.col("depth_rank") <= 1).cast(pl.Int8).alias("is_starter"))


def get_depth_chart_columns() -> list[str]:
    return DEPTH_COLUMNS


def _weekly_ranks(depth: pl.DataFrame) -> pl.DataFrame:
    """Rank per player-week from the pre-2025 season/week schema."""
    if "depth_team" not in depth.columns:
        return pl.DataFrame(schema=RANK_SCHEMA)

    return (
        depth.filter(
            pl.col("formation") == "Offense",
            pl.col("depth_team").is_not_null(),
            pl.col("week").is_not_null(),
        )
        .group_by(["gsis_id", "season", "week"])
        .agg(pl.col("depth_team").cast(pl.Float64).min().alias("depth_rank"))
        .rename({"gsis_id": "player_id"})
        .select(list(RANK_SCHEMA))
        .cast(RANK_SCHEMA)  # type: ignore[arg-type]
    )


def _snapshot_ranks(depth: pl.DataFrame, schedules: pl.DataFrame) -> pl.DataFrame:
    """Rank per player-week from the 2025+ dated-snapshot schema."""
    if "pos_rank" not in depth.columns:
        return pl.DataFrame(schema=RANK_SCHEMA)

    # Snapshot rows carry null season/week, which the schedule join supplies instead.
    snapshots = (
        depth.filter(
            pl.col("pos_grp") == "3WR 1TE",
            pl.col("pos_rank").is_not_null(),
            pl.col("gsis_id").is_not_null(),
        )
        .with_columns(pl.col("dt").str.to_datetime("%Y-%m-%dT%H:%M:%SZ").alias("snapshot_at"))
        .select(["gsis_id", "pos_rank", "snapshot_at"])
    )

    if snapshots.is_empty():
        return pl.DataFrame(schema=RANK_SCHEMA)

    week_starts = (
        schedules.group_by(["season", "week"])
        .agg(pl.col("gameday").min().str.to_datetime("%Y-%m-%d").alias("week_start"))
        .sort("week_start")
    )

    # Last snapshot published before the week's first kickoff.
    weeks = week_starts.join_asof(
        snapshots.select("snapshot_at").unique().sort("snapshot_at"),
        left_on="week_start",
        right_on="snapshot_at",
        strategy="backward",
    ).drop_nulls("snapshot_at")

    return (
        snapshots.join(weeks.select(["season", "week", "snapshot_at"]), on="snapshot_at")
        .group_by(["gsis_id", "season", "week"])
        .agg(pl.col("pos_rank").cast(pl.Float64).min().alias("depth_rank"))
        .rename({"gsis_id": "player_id"})
        .select(list(RANK_SCHEMA))
        .cast(RANK_SCHEMA)  # type: ignore[arg-type]
    )


def _defaults(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(3.0).alias("depth_rank"),
        pl.lit(0, dtype=pl.Int8).alias("is_starter"),
    )
