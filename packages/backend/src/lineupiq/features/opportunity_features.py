"""Expected fantasy point opportunity features (xFP).

xFP is computed from the plays of the game being predicted, so the weekly values
are joined and then lagged into prior-game rolling averages.
"""

from __future__ import annotations

import logging

import polars as pl

from lineupiq.data.fetchers import fetch_ff_opportunity
from lineupiq.data.normalization import prepare_weekly_join
from lineupiq.features.rolling_stats import add_lagged_rolling

logger = logging.getLogger(__name__)

OPPORTUNITY_STATS = ["xfp_rush", "xfp_rec", "xfp_total"]


def add_opportunity_features(df: pl.DataFrame, seasons: list[int], window: int = 5) -> pl.DataFrame:
    """Join weekly xFP from nflreadpy opportunity data as lagged rolling means."""
    try:
        opp = fetch_ff_opportunity(seasons, stat_type="weekly")
    except Exception as exc:
        logger.warning("Failed to fetch xFP data: %s", exc)
        return _with_defaults(df, window)

    id_col = None
    for candidate in ["player_gsis_id", "player_id", "gsis_id"]:
        if candidate in opp.columns:
            id_col = candidate
            break
    if opp.is_empty() or id_col is None:
        return _with_defaults(df, window)

    source_cols = ["rec_fantasy_points_exp", "rush_fantasy_points_exp"]
    stat_cols = [c for c in source_cols if c in opp.columns]
    if not stat_cols:
        return _with_defaults(df, window)

    base = opp.select([id_col, "season", "week", *stat_cols]).rename(
        {
            id_col: "player_id",
            "rec_fantasy_points_exp": "xfp_rec",
            "rush_fantasy_points_exp": "xfp_rush",
        }
    )

    out = df.join(prepare_weekly_join(base, df), on=["player_id", "season", "week"], how="left")
    # Null (no opportunity row) must stay null so the rolling mean skips the week.
    out = out.with_columns(
        pl.when(pl.col("xfp_rush").is_null() & pl.col("xfp_rec").is_null())
        .then(None)
        .otherwise(pl.col("xfp_rush").fill_null(0.0) + pl.col("xfp_rec").fill_null(0.0))
        .alias("xfp_total")
    )
    return add_lagged_rolling(out, OPPORTUNITY_STATS, window)


def get_opportunity_columns(window: int = 5) -> list[str]:
    return [f"{col}_roll{window}" for col in OPPORTUNITY_STATS]


def _with_defaults(df: pl.DataFrame, window: int) -> pl.DataFrame:
    return df.with_columns([pl.lit(0.0).alias(col) for col in get_opportunity_columns(window)])
