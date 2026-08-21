"""Player ID crosswalk for nflverse datasets keyed on Pro-Football-Reference IDs.

Snap counts and PFR advanced stats carry only `pfr_player_id`, while player stats
are keyed on GSIS `player_id`, so those datasets cannot be joined without a bridge.
"""

from __future__ import annotations

import logging

import polars as pl

logger = logging.getLogger(__name__)


def load_pfr_gsis_map() -> pl.DataFrame:
    """Fetch the pfr_id -> gsis player_id crosswalk from nflreadpy."""
    import nflreadpy as nfl  # noqa: PLC0415

    ids: pl.DataFrame = nfl.load_ff_playerids()
    crosswalk = (
        ids.select(pl.col("pfr_id"), pl.col("gsis_id").alias("player_id"))
        .drop_nulls()
        # A handful of pfr_ids map to several gsis_ids; pick one deterministically.
        .sort(["pfr_id", "player_id"])
        .unique(subset=["pfr_id"], keep="first", maintain_order=True)
    )
    logger.info(f"Loaded pfr->gsis crosswalk with {len(crosswalk)} players")
    return crosswalk


def add_gsis_player_id(df: pl.DataFrame, pfr_col: str = "pfr_player_id") -> pl.DataFrame:
    """Attach GSIS `player_id` to a PFR-keyed frame, dropping unmatched rows."""
    crosswalk = load_pfr_gsis_map()
    matched = df.join(crosswalk, left_on=pfr_col, right_on="pfr_id", how="inner")
    if len(df) and len(matched) < len(df) * 0.5:
        logger.warning(
            f"pfr->gsis crosswalk matched only {len(matched)}/{len(df)} rows"
        )
    return matched
