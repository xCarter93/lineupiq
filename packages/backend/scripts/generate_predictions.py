"""Generate the upcoming week's predictions and push them to Convex.

The frame is the normal training frame with synthetic rows appended for the games
that have not been played yet, so every feature is produced by the same code that
produced the training features. Per (position, target), eval/verdicts_final.json
decides whether the row comes from the trained artifact or from the naive lagged
5-game mean that the artifact was measured against.

Usage:
    uv run python scripts/generate_predictions.py [--season 2026] [--week 1] [--dry-run]
"""

import argparse
import json
import logging
import math
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import nflreadpy as nfl
import numpy as np
import polars as pl
import requests
from dotenv import load_dotenv
from evaluate_honest import lagged_mean, skill_target_exprs  # sibling script on sys.path[0]

from lineupiq.data.cleaning import clean_schedules
from lineupiq.data.defense_processing import get_defense_feature_columns, process_defense_data
from lineupiq.data.fetchers import fetch_rosters, latest_stats_season
from lineupiq.data.kicker_processing import get_kicker_feature_columns, process_kicker_data
from lineupiq.data.normalization import normalize_team_columns
from lineupiq.data.storage import load_schedules_cached
from lineupiq.features.pipeline import (
    build_features,
    build_future_player_rows,
    get_feature_columns,
)
from lineupiq.models.persistence import load_model

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
VERDICTS_PATH = BACKEND_DIR / "eval" / "verdicts_final.json"
PREVIEW_PATH = BACKEND_DIR / "eval" / "predictions_preview.json"

INGEST_PATH = "/ingest-predictions"
CHUNK_SIZE = 100

SKILL_POSITIONS = ("QB", "RB", "WR", "TE")
# Training history depth, matching the seasons the shipped models were fit on.
STATS_SEASON_SPAN = 4

# Opponent strength is ranked from prior weeks of the same season, so it is null for
# every week-1 row in every season. Excluded from the parity gate for that reason.
OPPONENT_FEATURES = frozenset(
    {
        "opp_pass_defense_strength",
        "opp_rush_defense_strength",
        "opp_pass_yards_allowed_rank",
        "opp_rush_yards_allowed_rank",
        "opp_total_yards_allowed_rank",
    }
)
NULL_RATE_TOLERANCE = 0.10


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def load_schedule(season: int) -> pl.DataFrame:
    """Cleaned, team-normalized schedule for one season."""
    schedule: pl.DataFrame = normalize_team_columns(
        clean_schedules(load_schedules_cached([season]))
    )
    return schedule


def derive_target_week(schedule: pl.DataFrame, today: date) -> int:
    """Earliest week whose games have not all been played.

    Derived from the schedule rather than from stats availability: only the schedule
    knows about games that have not happened yet.
    """
    last_game = pl.col("gameday")
    if schedule.schema["gameday"] == pl.String:
        last_game = last_game.str.to_date()

    weeks = (
        schedule.group_by("week")
        .agg(last_game.max().alias("last_game"))
        .filter(pl.col("last_game") >= pl.lit(today))
        .sort("week")
    )
    if weeks.is_empty():
        raise SystemExit(f"Every game in the {schedule['season'][0]} schedule has been played")
    return int(weeks["week"][0])


def load_verdicts() -> dict[tuple[str, str], str]:
    payload = json.loads(VERDICTS_PATH.read_text())
    return {(r["position"], r["target"]): r["final_verdict"] for r in payload["results"]}


def targets_for(verdicts: dict[tuple[str, str], str], position: str) -> list[str]:
    return [target for (pos, target) in verdicts if pos == position]


def team_names() -> dict[str, str]:
    """Team abbreviation -> full name, for the synthetic DEF entities."""
    teams = nfl.load_teams()
    return dict(zip(teams["team_abbr"].to_list(), teams["team_name"].to_list(), strict=True))


# ---------------------------------------------------------------------------
# Scoring frames
# ---------------------------------------------------------------------------


def _concat_future(base: pl.DataFrame, future: pl.DataFrame, group: str) -> pl.DataFrame:
    """Append stat-less future rows so the lagged rollups reach back into real games."""
    shared = pl.Schema({c: base.schema[c] for c in future.columns if c in base.columns})
    return pl.concat([base, future.cast(shared)], how="diagonal").sort([group, "season", "week"])


def _prior_games(group: str) -> pl.Expr:
    return pl.col(group).cum_count().over(group) - 1


def _upcoming(frame: pl.DataFrame, season: int, week: int, group: str) -> pl.DataFrame:
    """The future rows, dropped to entities with at least one prior game."""
    return frame.filter(
        (pl.col("season") == season) & (pl.col("week") == week) & (_prior_games(group) >= 1)
    )


def skill_scoring_frame(
    frame: pl.DataFrame, position: str, targets: list[str], season: int, week: int
) -> pl.DataFrame:
    pos = frame.filter(pl.col("position") == position).sort(["player_id", "season", "week"])
    pos = pos.with_columns(**skill_target_exprs(position))
    pos = pos.with_columns(
        **{f"naive_{t}": lagged_mean(pl.col(t), "player_id") for t in targets}
    )
    return _upcoming(pos, season, week, "player_id").with_columns(
        entity_id=pl.col("player_id"),
        entity_name=pl.col("player_name"),
    )


def kicker_scoring_frame(
    stats_seasons: list[int], future: pl.DataFrame, targets: list[str], season: int, week: int
) -> pl.DataFrame:
    base = process_kicker_data(stats_seasons)
    frame = _concat_future(base, future, "player_id").with_columns(
        **{f"naive_{t}": lagged_mean(pl.col(t), "player_id") for t in targets},
    )
    return _upcoming(frame, season, week, "player_id").with_columns(
        entity_id=pl.col("player_id"),
        entity_name=pl.col("player_name"),
    )


def defense_scoring_frame(
    stats_seasons: list[int], future: pl.DataFrame, targets: list[str], season: int, week: int
) -> pl.DataFrame:
    base = process_defense_data(stats_seasons)
    frame = _concat_future(base, future, "team").with_columns(
        **{f"naive_{t}": lagged_mean(pl.col(t), "team") for t in targets},
    )
    names = team_names()
    return _upcoming(frame, season, week, "team").with_columns(
        entity_id=pl.format("DEF_{}", pl.col("team")),
        entity_name=pl.col("team").replace_strict(names, default=pl.col("team") + " Defense")
        + " D/ST",
        position=pl.lit("DEF"),
    )


def build_defense_entities(schedule: pl.DataFrame, season: int, week: int) -> pl.DataFrame:
    """One row per team playing that week, with its opponent."""
    games = schedule.filter(pl.col("week") == week)
    sides = pl.concat(
        [
            games.select(
                pl.col("home_team").alias("team"),
                pl.col("away_team").alias("opponent"),
                pl.lit(True).alias("is_home"),
            ),
            games.select(
                pl.col("away_team").alias("team"),
                pl.col("home_team").alias("opponent"),
                pl.lit(False).alias("is_home"),
            ),
        ]
    )
    return sides.with_columns(
        pl.lit(season, dtype=pl.Int32).alias("season"),
        pl.lit(week, dtype=pl.Int32).alias("week"),
    )


# ---------------------------------------------------------------------------
# Null-parity gate
# ---------------------------------------------------------------------------


def check_null_parity(
    frame: pl.DataFrame, season: int, week: int, reference_season: int, feature_cols: list[str]
) -> None:
    """Fail if a feature is more null on the synthetic rows than on real ones.

    A column populated in the reference week but null in the synthetic week means the
    future rows are not reaching the same data the training rows reached.

    Both sides are restricted to the population that actually gets scored: a preseason
    roster carries rookies whose rolling features are legitimately null, and comparing
    them against a reference week of players who all had prior games measures roster
    depth rather than plumbing.
    """
    scored = frame.sort(["player_id", "season", "week"]).filter(_prior_games("player_id") >= 1)
    upcoming = scored.filter((pl.col("season") == season) & (pl.col("week") == week))
    reference = scored.filter((pl.col("season") == reference_season) & (pl.col("week") == week))
    if upcoming.is_empty() or reference.is_empty():
        raise SystemExit(
            f"Null-parity gate needs both {season} W{week} ({len(upcoming)} rows) and "
            f"{reference_season} W{week} ({len(reference)} rows)"
        )

    offenders = []
    for col in feature_cols:
        if col in OPPONENT_FEATURES:
            continue
        rate = upcoming[col].null_count() / len(upcoming)
        ref_rate = reference[col].null_count() / len(reference)
        if rate - ref_rate > NULL_RATE_TOLERANCE:
            offenders.append((col, rate, ref_rate))

    if offenders:
        diff = "\n".join(
            f"  {col:38s} {season}W{week}={rate:.2%}  {reference_season}W{week}={ref:.2%}"
            for col, rate, ref in offenders
        )
        raise SystemExit(f"Null-parity gate failed for {len(offenders)} feature(s):\n{diff}")

    logger.info(
        "Null-parity gate passed: %d features, %d upcoming vs %d reference rows",
        len(feature_cols),
        len(upcoming),
        len(reference),
    )


# ---------------------------------------------------------------------------
# Prediction rows
# ---------------------------------------------------------------------------


def load_scoring_model(
    position: str, target: str, n_features: int
) -> tuple[Any, str | None] | None:
    """Load an artifact, or None if it is missing, unreadable, or schema-drifted.

    The trainers fit on `df.select(get_feature_columns()).to_numpy()`, so the artifact's
    feature_names are positional placeholders ("Column_0", ...) rather than real names:
    the feature count is the only identity the artifact carries, and column order is what
    binds a value to a feature. A count mismatch means the artifact predates the current
    schema. Loading is also retried-as-baseline because save_model copies over the
    canonical path non-atomically, so a concurrent training run can yield a torn read.
    """
    try:
        model, metadata = load_model(position, target)
    except Exception as exc:
        logger.warning("%s_%s not loadable (%s) - falling back to baseline", position, target, exc)
        return None

    n_artifact = len(metadata.get("feature_names") or [])
    if n_artifact != n_features:
        logger.warning(
            "%s_%s feature schema drift (artifact %d, pipeline %d) - falling back to baseline",
            position,
            target,
            n_artifact,
            n_features,
        )
        return None
    return model, metadata.get("version")


def _row(entity: dict[str, Any], target: str, value: float, source: str, version: str | None,
         run_id: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "playerId": entity["entity_id"],
        "playerName": entity["entity_name"],
        "position": entity["position"],
        "team": entity["team"],
        "season": int(entity["season"]),
        "week": int(entity["week"]),
        "target": target,
        "predictedValue": round(max(value, 0.0), 2),
        "source": source,
        "runId": run_id,
    }
    # Optional fields are omitted rather than sent as null; the validator rejects null.
    if entity.get("opponent") is not None:
        row["opponent"] = entity["opponent"]
    if entity.get("is_home") is not None:
        row["isHome"] = bool(entity["is_home"])
    if version:
        row["modelVersion"] = version
    return row


def predict_rows(
    scoring: pl.DataFrame,
    position: str,
    targets: list[str],
    feature_cols: list[str],
    verdicts: dict[tuple[str, str], str],
    run_id: str,
) -> list[dict[str, Any]]:
    if scoring.is_empty():
        logger.warning("No %s entities for the target week", position)
        return []

    # Opponent strength is null for every week-1 row and LightGBM scores NaN fine; any
    # other feature the future rows cannot supply means no model can be trusted here.
    unusable = [
        c
        for c in feature_cols
        if c not in scoring.columns
        or (c not in OPPONENT_FEATURES and scoring[c].null_count() == len(scoring))
    ]
    if unusable:
        logger.warning(
            "%s: %d of %d features unavailable on the future rows (e.g. %s) - baseline only",
            position,
            len(unusable),
            len(feature_cols),
            ", ".join(unusable[:3]),
        )
    features = (
        None if unusable else scoring.select(feature_cols).to_numpy().astype(np.float64)
    )
    identity = scoring.select(
        "entity_id", "entity_name", "position", "team", "opponent", "is_home", "season", "week"
    ).to_dicts()

    rows: list[dict[str, Any]] = []
    for target in targets:
        artifact = None
        if features is not None and verdicts[(position, target)] == "SHIP_MODEL":
            artifact = load_scoring_model(position, target, len(feature_cols))

        if artifact is not None:
            model, version = artifact
            values = list(model.predict(features))
            source = "model"
        else:
            values = scoring[f"naive_{target}"].to_list()
            source, version = "baseline", None

        for entity, value in zip(identity, values, strict=True):
            if value is None or math.isnan(value):
                continue
            rows.append(_row(entity, target, float(value), source, version, run_id))
    return rows


# ---------------------------------------------------------------------------
# Convex
# ---------------------------------------------------------------------------


def post_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    load_dotenv(BACKEND_DIR / ".env")
    site_url = os.environ["CONVEX_SITE_URL"].rstrip("/")
    secret = os.environ["PREDICTIONS_INGEST_SECRET"]

    totals = {"inserted": 0, "updated": 0}
    for start in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[start : start + CHUNK_SIZE]
        response = requests.post(
            f"{site_url}{INGEST_PATH}",
            json={"rows": chunk},
            headers={"Authorization": f"Bearer {secret}"},
            timeout=60,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Ingest failed ({response.status_code}): {response.text}")
        counts = response.json()
        totals["inserted"] += counts["inserted"]
        totals["updated"] += counts["updated"]
        logger.info("Posted rows %d-%d: %s", start, start + len(chunk), counts)
    return totals


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def summarize(rows: list[dict[str, Any]]) -> None:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["position"], row["source"])
        counts[key] = counts.get(key, 0) + 1
    print(f"\n{'position':10s} {'source':10s} {'rows':>7s}")
    print("-" * 29)
    for (position, source), count in sorted(counts.items()):
        print(f"{position:10s} {source:10s} {count:7d}")
    print(f"{'TOTAL':21s} {len(rows):7d}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, help="Target season (default: current roster season)")
    parser.add_argument("--week", type=int, help="Target week (default: next unplayed week)")
    parser.add_argument("--run-id", help="Run identifier (default: {season}w{week}-{utc stamp})")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=f"Write rows to {PREVIEW_PATH.name} instead of posting to Convex",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("lineupiq").setLevel(logging.WARNING)

    season = args.season or int(nfl.get_current_season(roster=True))
    schedule = load_schedule(season)
    week = args.week or derive_target_week(schedule, datetime.now(timezone.utc).date())
    stats_seasons = list(range(season - STATS_SEASON_SPAN, latest_stats_season() + 1))
    run_id = args.run_id or f"{season}w{week}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    logger.info("Predicting %s week %s from stats seasons %s (run %s)",
                season, week, stats_seasons, run_id)

    verdicts = load_verdicts()
    rosters = fetch_rosters([season])

    future_players = build_future_player_rows(rosters, schedule, season, week, SKILL_POSITIONS)
    frame = build_features(
        seasons=stats_seasons,
        context_seasons=sorted({*stats_seasons, season}),
        future_rows=future_players,
    )

    feature_cols = get_feature_columns()
    reference_season = max(s for s in stats_seasons if s != season)
    check_null_parity(frame, season, week, reference_season, feature_cols)

    rows: list[dict[str, Any]] = []
    for position in SKILL_POSITIONS:
        targets = targets_for(verdicts, position)
        scoring = skill_scoring_frame(frame, position, targets, season, week)
        rows += predict_rows(scoring, position, targets, feature_cols, verdicts, run_id)

    kicker_targets = targets_for(verdicts, "K")
    future_kickers = build_future_player_rows(rosters, schedule, season, week, ("K",))
    kickers = kicker_scoring_frame(stats_seasons, future_kickers, kicker_targets, season, week)
    rows += predict_rows(
        kickers, "K", kicker_targets, get_kicker_feature_columns(), verdicts, run_id
    )

    defense_targets = targets_for(verdicts, "DEF")
    future_defenses = build_defense_entities(schedule, season, week)
    defenses = defense_scoring_frame(stats_seasons, future_defenses, defense_targets, season, week)
    rows += predict_rows(
        defenses, "DEF", defense_targets, get_defense_feature_columns(), verdicts, run_id
    )

    summarize(rows)

    if args.dry_run:
        PREVIEW_PATH.write_text(json.dumps({"runId": run_id, "rows": rows}, indent=2))
        print(f"\nWrote {len(rows)} rows to {PREVIEW_PATH}")
        return

    totals = post_rows(rows)
    print(f"\nIngested {totals} as run {run_id}")


if __name__ == "__main__":
    main()
