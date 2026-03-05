"""
EPA (Expected Points Added) features for ML models.

EPA is the gold standard advanced metric in NFL analytics. It measures
per-play value and is highly correlated with sustained fantasy production.

Features:
- team_epa_roll5: Rolling team offensive EPA per play
- opp_def_epa_roll5: Rolling opponent defensive EPA per play
- player_epa_roll5: Rolling individual EPA per play (QBs, pass catchers)
- team_pass_epa_vs_rush_epa: Ratio showing team's pass/rush lean
"""

import logging

import nflreadpy as nfl
import polars as pl

logger = logging.getLogger(__name__)


def compute_epa_features(
    df: pl.DataFrame,
    seasons: list[int],
    window: int = 5,
) -> pl.DataFrame:
    """Add EPA-based features to player data.

    Loads play-by-play data to compute EPA metrics, then joins to player data.

    Args:
        df: Player stats DataFrame with player_id, season, week, team, opponent.
        seasons: Seasons to load play-by-play data for.
        window: Rolling window size (default: 5).

    Returns:
        DataFrame with added EPA columns.
    """
    logger.info(f"Computing EPA features for seasons {seasons}")

    try:
        pbp = nfl.load_pbp(seasons)
    except Exception:
        logger.warning("Failed to load play-by-play data, adding default EPA features")
        return _add_default_epa_features(df, window)

    # Convert pandas to polars if needed
    if not isinstance(pbp, pl.DataFrame):
        if hasattr(pbp, "empty") and pbp.empty:
            logger.warning("Empty PBP data, adding defaults")
            return _add_default_epa_features(df, window)
        pbp = pl.from_pandas(pbp)

    if len(pbp) == 0:
        logger.warning("Empty PBP data, adding defaults")
        return _add_default_epa_features(df, window)

    # Filter to actual plays (exclude penalties, timeouts, etc.)
    if "play_type" in pbp.columns:
        pbp = pbp.filter(pl.col("play_type").is_in(["pass", "run"]))

    # Ensure EPA column exists
    if "epa" not in pbp.columns:
        logger.warning("No 'epa' column in PBP data, adding defaults")
        return _add_default_epa_features(df, window)

    # --- Team Offensive EPA ---
    team_epa = _compute_team_epa(pbp, window)
    if team_epa is not None:
        df = df.join(team_epa, on=["season", "week", "team"], how="left")
    else:
        df = df.with_columns([
            pl.lit(0.0).alias(f"team_epa_roll{window}"),
            pl.lit(0.0).alias("team_pass_epa_vs_rush_epa"),
        ])

    # --- Opponent Defensive EPA ---
    opp_epa = _compute_opp_def_epa(pbp, window)
    if opp_epa is not None and "opponent" in df.columns:
        df = df.join(
            opp_epa,
            left_on=["season", "week", "opponent"],
            right_on=["season", "week", "team"],
            how="left",
        )
    else:
        df = df.with_columns(pl.lit(0.0).alias(f"opp_def_epa_roll{window}"))

    # --- Player EPA ---
    player_epa = _compute_player_epa(pbp, window)
    if player_epa is not None:
        # Need to match on player ID - check available columns
        if "passer_player_id" in pbp.columns or "receiver_player_id" in pbp.columns:
            df = df.join(player_epa, on=["player_id", "season", "week"], how="left")
        else:
            df = df.with_columns(pl.lit(0.0).alias(f"player_epa_roll{window}"))
    else:
        df = df.with_columns(pl.lit(0.0).alias(f"player_epa_roll{window}"))

    # Fill remaining nulls with 0
    epa_cols = get_epa_columns(window)
    for col in epa_cols:
        if col in df.columns:
            df = df.with_columns(pl.col(col).fill_null(0.0))

    logger.info(f"Added {len(epa_cols)} EPA features")
    return df


def _compute_team_epa(pbp: pl.DataFrame, window: int) -> pl.DataFrame | None:
    """Compute team-level offensive EPA per play."""
    try:
        # Identify offensive team column
        team_col = "posteam" if "posteam" in pbp.columns else "offense_team"
        if team_col not in pbp.columns:
            return None

        # Group by team, season, week
        team_weekly = pbp.group_by([team_col, "season", "week"]).agg([
            pl.col("epa").mean().alias("team_epa_per_play"),
        ])

        # Also compute pass vs rush EPA split
        if "play_type" in pbp.columns:
            pass_epa = (
                pbp.filter(pl.col("play_type") == "pass")
                .group_by([team_col, "season", "week"])
                .agg(pl.col("epa").mean().alias("pass_epa"))
            )
            rush_epa = (
                pbp.filter(pl.col("play_type") == "run")
                .group_by([team_col, "season", "week"])
                .agg(pl.col("epa").mean().alias("rush_epa"))
            )
            team_weekly = team_weekly.join(pass_epa, on=[team_col, "season", "week"], how="left")
            team_weekly = team_weekly.join(rush_epa, on=[team_col, "season", "week"], how="left")

        team_weekly = team_weekly.rename({team_col: "team"})
        team_weekly = team_weekly.sort(["team", "season", "week"])

        # Compute rolling EPA with shift
        result = team_weekly.with_columns([
            pl.col("team_epa_per_play")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("team")
            .fill_null(0.0)
            .alias(f"team_epa_roll{window}"),
        ])

        # Pass vs rush EPA ratio
        if "pass_epa" in result.columns and "rush_epa" in result.columns:
            result = result.with_columns(
                (
                    pl.col("pass_epa").shift(1).rolling_mean(window_size=window, min_samples=1).over("team")
                    - pl.col("rush_epa").shift(1).rolling_mean(window_size=window, min_samples=1).over("team")
                )
                .fill_null(0.0)
                .alias("team_pass_epa_vs_rush_epa")
            )
        else:
            result = result.with_columns(pl.lit(0.0).alias("team_pass_epa_vs_rush_epa"))

        return result.select([
            "season", "week", "team",
            f"team_epa_roll{window}",
            "team_pass_epa_vs_rush_epa",
        ])

    except Exception:
        logger.warning("Failed to compute team EPA", exc_info=True)
        return None


def _compute_opp_def_epa(pbp: pl.DataFrame, window: int) -> pl.DataFrame | None:
    """Compute opponent defensive EPA (EPA allowed per play)."""
    try:
        # Defense team is the non-possessing team
        def_col = "defteam" if "defteam" in pbp.columns else None
        if def_col is None:
            return None

        # Group by defensive team, season, week
        def_weekly = pbp.group_by([def_col, "season", "week"]).agg([
            pl.col("epa").mean().alias("def_epa_per_play"),
        ])

        def_weekly = def_weekly.rename({def_col: "team"})
        def_weekly = def_weekly.sort(["team", "season", "week"])

        # Compute rolling defensive EPA (positive = bad defense, negative = good)
        result = def_weekly.with_columns(
            pl.col("def_epa_per_play")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("team")
            .fill_null(0.0)
            .alias(f"opp_def_epa_roll{window}")
        )

        return result.select(["season", "week", "team", f"opp_def_epa_roll{window}"])

    except Exception:
        logger.warning("Failed to compute opponent defensive EPA", exc_info=True)
        return None


def _compute_player_epa(pbp: pl.DataFrame, window: int) -> pl.DataFrame | None:
    """Compute per-player EPA (for QBs and pass catchers)."""
    try:
        # Collect EPA by player: passers and receivers
        player_epa_rows = []

        if "passer_player_id" in pbp.columns:
            passer_epa = pbp.filter(pl.col("passer_player_id").is_not_null()).group_by(
                ["passer_player_id", "season", "week"]
            ).agg(pl.col("epa").mean().alias("player_epa_per_play"))
            passer_epa = passer_epa.rename({"passer_player_id": "player_id"})
            player_epa_rows.append(passer_epa)

        if "receiver_player_id" in pbp.columns:
            recv_epa = pbp.filter(pl.col("receiver_player_id").is_not_null()).group_by(
                ["receiver_player_id", "season", "week"]
            ).agg(pl.col("epa").mean().alias("player_epa_per_play"))
            recv_epa = recv_epa.rename({"receiver_player_id": "player_id"})
            player_epa_rows.append(recv_epa)

        if "rusher_player_id" in pbp.columns:
            rusher_epa = pbp.filter(pl.col("rusher_player_id").is_not_null()).group_by(
                ["rusher_player_id", "season", "week"]
            ).agg(pl.col("epa").mean().alias("player_epa_per_play"))
            rusher_epa = rusher_epa.rename({"rusher_player_id": "player_id"})
            player_epa_rows.append(rusher_epa)

        if not player_epa_rows:
            return None

        # Combine and average if a player appears in multiple roles
        player_epa = pl.concat(player_epa_rows)
        player_epa = player_epa.group_by(["player_id", "season", "week"]).agg(
            pl.col("player_epa_per_play").mean()
        )

        player_epa = player_epa.sort(["player_id", "season", "week"])

        # Compute rolling EPA with shift
        result = player_epa.with_columns(
            pl.col("player_epa_per_play")
            .shift(1)
            .rolling_mean(window_size=window, min_samples=1)
            .over("player_id")
            .fill_null(0.0)
            .alias(f"player_epa_roll{window}")
        )

        return result.select(["player_id", "season", "week", f"player_epa_roll{window}"])

    except Exception:
        logger.warning("Failed to compute player EPA", exc_info=True)
        return None


def _add_default_epa_features(df: pl.DataFrame, window: int) -> pl.DataFrame:
    """Add default EPA features when PBP data is unavailable."""
    return df.with_columns([
        pl.lit(0.0).alias(f"team_epa_roll{window}"),
        pl.lit(0.0).alias(f"opp_def_epa_roll{window}"),
        pl.lit(0.0).alias(f"player_epa_roll{window}"),
        pl.lit(0.0).alias("team_pass_epa_vs_rush_epa"),
    ])


def get_epa_columns(window: int = 5) -> list[str]:
    """Return list of EPA feature column names."""
    return [
        f"team_epa_roll{window}",
        f"opp_def_epa_roll{window}",
        f"player_epa_roll{window}",
        "team_pass_epa_vs_rush_epa",
    ]
