"""Diagnostic script to demonstrate the window parameter mismatch bug.

This script fetches features for 3 different QBs and compares their rolling stats
to demonstrate that they all receive identical position-default values instead of
player-specific values.

Root Cause:
- Models expect window=5 features (passing_yards_roll5, etc.)
- API computes window=3 features by default (passing_yards_roll3, etc.)
- Feature merge doesn't overwrite defaults → all players get same predictions
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import nflreadpy as nfl  # noqa: E402
import polars as pl  # noqa: E402

from lineupiq.data.fetchers import fetch_player_history, fetch_rosters  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def get_qb_player_ids() -> list[tuple[str, str]]:
    """Get player IDs for 3 well-known QBs with different performance profiles."""
    current = nfl.get_current_season()
    roster = fetch_rosters([current])

    qbs = roster.filter(pl.col("position") == "QB")

    # Look for Jalen Hurts, Patrick Mahomes, Joe Burrow
    target_names = ["Jalen Hurts", "Patrick Mahomes", "Joe Burrow"]
    players = []

    for name in target_names:
        player = qbs.filter(pl.col("full_name") == name)
        if not player.is_empty():
            row = player.row(0, named=True)
            players.append((row["gsis_id"], row["full_name"]))

    if len(players) < 3:
        # Fallback: just take first 3 QBs
        logger.warning("Could not find all target QBs, using first 3 from roster")
        players = [(row["gsis_id"], row["full_name"]) for row in qbs.head(3).to_dicts()]

    return players


def compute_rolling_stats_window3(history_df: pl.DataFrame) -> dict[str, float]:
    """Compute rolling stats with window=3 (current API default - BUG)."""
    df = history_df.sort(["season", "week"], descending=True)
    recent = df.head(3)

    if recent.is_empty():
        return {}

    stats = {}
    stat_mappings = {
        "passing_yards_roll3": "passing_yards",
        "passing_tds_roll3": "passing_tds",
        "rushing_yards_roll3": "rushing_yards",
        "rushing_tds_roll3": "rushing_tds",
        "carries_roll3": "carries",
    }

    for roll_name, stat_col in stat_mappings.items():
        if stat_col in recent.columns:
            values = recent[stat_col].drop_nulls()
            if len(values) > 0:
                stats[roll_name] = round(float(values.mean()), 2)
            else:
                stats[roll_name] = 0.0
        else:
            stats[roll_name] = 0.0

    return stats


def compute_rolling_stats_window5(history_df: pl.DataFrame) -> dict[str, float]:
    """Compute rolling stats with window=5 (what models expect)."""
    df = history_df.sort(["season", "week"], descending=True)
    recent = df.head(5)

    if recent.is_empty():
        return {}

    stats = {}
    stat_mappings = {
        "passing_yards_roll5": "passing_yards",
        "passing_tds_roll5": "passing_tds",
        "rushing_yards_roll5": "rushing_yards",
        "rushing_tds_roll5": "rushing_tds",
        "carries_roll5": "carries",
    }

    for roll_name, stat_col in stat_mappings.items():
        if stat_col in recent.columns:
            values = recent[stat_col].drop_nulls()
            if len(values) > 0:
                stats[roll_name] = round(float(values.mean()), 2)
            else:
                stats[roll_name] = 0.0
        else:
            stats[roll_name] = 0.0

    return stats


def get_qb_defaults() -> dict[str, float]:
    """Get position-default features for QB (from roster.py _get_default_features)."""
    return {
        "passing_yards_roll5": 250.0,
        "passing_tds_roll5": 1.8,
        "rushing_yards_roll5": 15.0,
        "rushing_tds_roll5": 0.1,
        "carries_roll5": 3.0,
    }


def main():
    """Run diagnostic to demonstrate window mismatch bug."""
    logger.info("=" * 80)
    logger.info("DIAGNOSTIC: Window Parameter Mismatch Bug")
    logger.info("=" * 80)
    logger.info("")

    # Get 3 QB player IDs
    qbs = get_qb_player_ids()
    logger.info(f"Testing with QBs: {', '.join(name for _, name in qbs)}")
    logger.info("")

    # Fetch history for each QB
    current = nfl.get_current_season()
    season_list = [current - 1, current]

    results = {}
    for player_id, name in qbs:
        history = fetch_player_history(player_id, season_list)
        if not history.is_empty():
            results[name] = {
                "player_id": player_id,
                "history": history,
                "games": len(history),
            }

    logger.info("-" * 80)
    logger.info("1. WHAT MODELS EXPECT (window=5 features)")
    logger.info("-" * 80)
    defaults = get_qb_defaults()
    logger.info(f"Position defaults (from _get_default_features in roster.py):")
    for key, val in defaults.items():
        logger.info(f"  {key}: {val}")
    logger.info("")

    logger.info("Player-specific values (window=5):")
    for name, data in results.items():
        stats = compute_rolling_stats_window5(data["history"])
        logger.info(f"\n  {name} ({data['games']} games):")
        for key, val in stats.items():
            logger.info(f"    {key}: {val}")
    logger.info("")

    logger.info("-" * 80)
    logger.info("2. WHAT API ACTUALLY COMPUTES (window=3 features - BUG)")
    logger.info("-" * 80)
    logger.info("Features from _compute_rolling_stats_for_player (default window=3):")
    for name, data in results.items():
        stats = compute_rolling_stats_window3(data["history"])
        logger.info(f"\n  {name} ({data['games']} games):")
        for key, val in stats.items():
            logger.info(f"    {key}: {val}")
    logger.info("")

    logger.info("-" * 80)
    logger.info("3. THE BUG: Feature Key Mismatch")
    logger.info("-" * 80)
    logger.info("When features.update(rolling_stats) happens at roster.py:450:")
    logger.info("")
    logger.info("  Default features dict has keys:    passing_yards_roll5, passing_tds_roll5, ...")
    logger.info("  Computed rolling_stats dict has:   passing_yards_roll3, passing_tds_roll3, ...")
    logger.info("")
    logger.info("  Result: roll3 keys DON'T overwrite roll5 defaults!")
    logger.info("  All players get the same roll5 default values (250.0, 1.8, 15.0, ...)")
    logger.info("  Player-specific roll3 values are ignored by the model")
    logger.info("")

    logger.info("-" * 80)
    logger.info("4. DEMONSTRATION: All Players Get Same Predictions")
    logger.info("-" * 80)
    logger.info("When prediction models receive features:")
    logger.info("")
    for name in results.keys():
        logger.info(f"  {name}:")
        logger.info(
            f"    passing_yards_roll5 = {defaults['passing_yards_roll5']} (default, not player-specific!)"
        )
        logger.info(
            f"    passing_tds_roll5 = {defaults['passing_tds_roll5']} (default, not player-specific!)"
        )
    logger.info("")
    logger.info("  ^ All identical! This is why predictions are the same.")
    logger.info("")

    logger.info("-" * 80)
    logger.info("5. ROOT CAUSE SUMMARY")
    logger.info("-" * 80)
    logger.info("")
    logger.info("EXPECTED:")
    logger.info("  - Models trained with window=5 (Phase 19.1)")
    logger.info("  - API should compute window=5 features")
    logger.info("  - Player-specific roll5 values replace defaults")
    logger.info("")
    logger.info("ACTUAL:")
    logger.info("  - API computes window=3 features (roster.py lines 124, 172)")
    logger.info("  - Creates roll3 keys that don't match model expectations")
    logger.info("  - features.update() doesn't overwrite roll5 defaults")
    logger.info("  - All players get identical roll5 defaults → same predictions")
    logger.info("")
    logger.info("FIX:")
    logger.info("  - Change window parameter from 3 to 5 in:")
    logger.info("    * _compute_rolling_stats_for_player(history_df, window=5)")
    logger.info("    * _compute_volatility_for_player(history_df, window=5)")
    logger.info("    * Update calls at lines 424, 425, 448, 449")
    logger.info("")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
