"""Pre-game Vegas context per team-week, shared by the K and DEF pipelines.

These are betting lines, not outcomes, so they are knowable before kickoff and
need no lagging - unlike every other feature in those two pipelines.
"""

import logging

import polars as pl

from lineupiq.data.normalization import normalize_team_columns

logger = logging.getLogger(__name__)

# Feature columns produced by attach_team_vegas_context()
TEAM_CONTEXT_COLUMNS = [
    "is_home",
    "total_line",
    "team_spread",
    "implied_team_total",
    "opp_implied_total",
]


def build_team_vegas_context(schedules: pl.DataFrame) -> pl.DataFrame:
    """One row per (season, week, team) with the game's lines from that team's side.

    nflverse `spread_line` is positive when the HOME team is favored, so a team's
    own spread flips sign on the road and its implied total adds that own spread:
    home = (total + spread) / 2, away = (total - spread) / 2.
    """
    # Pre-2020 schedules use OAK/SD/STL while the stat frames use LV/LAC/LA.
    schedules = normalize_team_columns(schedules)

    def side(team_col: str, is_home: bool) -> pl.DataFrame:
        spread = pl.col("spread_line") if is_home else -pl.col("spread_line")
        total = pl.col("total_line").cast(pl.Float64)
        return schedules.select(
            pl.col("season"),
            pl.col("week"),
            pl.col(team_col).alias("team"),
            pl.lit(int(is_home), dtype=pl.Int8).alias("is_home"),
            total.alias("total_line"),
            spread.cast(pl.Float64).alias("team_spread"),
            ((total + spread) / 2).alias("implied_team_total"),
            ((total - spread) / 2).alias("opp_implied_total"),
        )

    return pl.concat([side("home_team", True), side("away_team", False)])


def attach_team_vegas_context(
    df: pl.DataFrame, schedules: pl.DataFrame, team_col: str
) -> pl.DataFrame:
    """Left-join the Vegas context onto a frame keyed by (season, week, team_col)."""
    ctx = build_team_vegas_context(schedules).with_columns(
        pl.col("season").cast(df.schema["season"]),
        pl.col("week").cast(df.schema["week"]),
    )
    joined = df.join(
        ctx,
        left_on=["season", "week", team_col],
        right_on=["season", "week", "team"],
        how="left",
    )
    missing = joined.select(pl.col("implied_team_total").null_count()).item()
    if missing:
        logger.warning(f"{missing}/{len(joined)} rows have no Vegas line after join")
    return joined
