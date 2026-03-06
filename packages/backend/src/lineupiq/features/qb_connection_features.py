"""QB-receiver connection and TD opportunity features."""

from __future__ import annotations

import logging

import polars as pl

logger = logging.getLogger(__name__)

QB_CONNECTION_COLUMNS = ["qb_cpoe_roll5", "qb_target_share_to_player_roll5", "red_zone_target_share_roll5"]


def add_qb_connection_features(df: pl.DataFrame, window: int = 5) -> pl.DataFrame:
    """Add receiver-facing QB quality and connection features.

    Uses already-joined nextgen CPOE (`ngs_cpoe`) where available.
    """
    out = df

    # Team-level proxy for current QB quality (rolling CPOE).
    if "ngs_cpoe" in out.columns:
        out = out.sort(["team", "season", "week"]).with_columns(
            pl.col("ngs_cpoe")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("team")
            .fill_null(0.0)
            .alias("qb_cpoe_roll5")
        )
    else:
        out = out.with_columns(pl.lit(0.0).alias("qb_cpoe_roll5"))

    # Share of team targets directed to this player.
    if "targets" in out.columns:
        team_targets = out.group_by(["team", "season", "week"]).agg(pl.col("targets").sum().alias("_team_targets"))
        out = out.join(team_targets, on=["team", "season", "week"], how="left").with_columns(
            pl.when(pl.col("_team_targets") > 0)
            .then(pl.col("targets") / pl.col("_team_targets"))
            .otherwise(0.0)
            .alias("_target_share_raw")
        ).with_columns(
            pl.col("_target_share_raw")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("player_id")
            .fill_null(0.0)
            .alias("qb_target_share_to_player_roll5")
        ).drop(["_team_targets", "_target_share_raw"])
    else:
        out = out.with_columns(pl.lit(0.0).alias("qb_target_share_to_player_roll5"))

    # Red-zone target share proxy (if explicit redzone targets unavailable).
    # Use receiving TD opportunity proxy from receiving_tds / team receiving_tds.
    if "receiving_tds" in out.columns:
        team_rec_tds = out.group_by(["team", "season", "week"]).agg(
            pl.col("receiving_tds").sum().alias("_team_receiving_tds")
        )
        out = out.join(team_rec_tds, on=["team", "season", "week"], how="left").with_columns(
            pl.when(pl.col("_team_receiving_tds") > 0)
            .then(pl.col("receiving_tds") / pl.col("_team_receiving_tds"))
            .otherwise(0.0)
            .alias("_red_zone_share_proxy")
        ).with_columns(
            pl.col("_red_zone_share_proxy")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("player_id")
            .fill_null(0.0)
            .alias("red_zone_target_share_roll5")
        ).drop(["_team_receiving_tds", "_red_zone_share_proxy"])
    else:
        out = out.with_columns(pl.lit(0.0).alias("red_zone_target_share_roll5"))

    for col in QB_CONNECTION_COLUMNS:
        out = out.with_columns(pl.col(col).fill_null(0.0))
    return out


def get_qb_connection_columns() -> list[str]:
    return QB_CONNECTION_COLUMNS
