/**
 * Turns `cachedPredictions` rows (one row per stat target) into the single
 * fantasy-point number the list surfaces display, using the active scoring
 * config. No projection is invented: a player with no rows gets no projection.
 */

import { calculateFantasyPoints, type AnyPrediction } from "./fantasy-points";
import type { FullScoringConfig } from "./scoring-config";

export type PredictionSource = "model" | "baseline";

/** Whether every scored stat came from a model, from recent-form baselines, or both. */
export type SourceMix = PredictionSource | "mixed";

/** The subset of a cachedPredictions document these helpers read. */
export interface PredictionRow {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  opponent?: string;
  isHome?: boolean;
  target: string;
  predictedValue: number;
  source: PredictionSource;
}

export interface PlayerProjection {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  opponent?: string;
  isHome?: boolean;
  points: number;
  /** Zero-filled stat object in the shape this position's calculators expect. */
  stats: AnyPrediction;
  sourceMix: SourceMix;
  modelCount: number;
  baselineCount: number;
  /** Only the targets that feed the scoring formula, in scoring order. */
  scoredRows: PredictionRow[];
}

/**
 * Targets each position's calculator reads. Anything predicted but unscored
 * (K `fg_att`, which is the total the bracketed attempts already cover) is
 * excluded so it neither zero-fills a calculator nor skews the source mix.
 */
export const SCORED_TARGETS: Record<string, readonly string[]> = {
  QB: [
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_tds",
    "fumbles_lost",
  ],
  RB: [
    "rushing_yards",
    "rushing_tds",
    "carries",
    "receiving_yards",
    "receptions",
    "receiving_tds",
    "fumbles_lost",
  ],
  WR: ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"],
  TE: ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"],
  K: ["fg_att_0_39", "fg_att_40_49", "fg_att_50_plus", "pat_att"],
  DEF: [
    "points_allowed",
    "def_sacks",
    "def_interceptions",
    "def_fumbles",
    "total_def_tds",
  ],
};

function resolveSourceMix(
  modelCount: number,
  baselineCount: number
): SourceMix {
  if (modelCount > 0 && baselineCount > 0) return "mixed";
  return baselineCount > 0 ? "baseline" : "model";
}

/**
 * Collapse one player's stat rows into a projection.
 * Returns null when the position has no scoring rules or nothing was predicted.
 */
export function toPlayerProjection(
  rows: PredictionRow[],
  config: FullScoringConfig
): PlayerProjection | null {
  const first = rows[0];
  if (!first) return null;

  const scoredTargets = SCORED_TARGETS[first.position.toUpperCase()];
  if (!scoredTargets) return null;

  const byTarget = new Map(rows.map((row) => [row.target, row]));
  const scoredRows = scoredTargets
    .map((target) => byTarget.get(target))
    .filter((row): row is PredictionRow => row !== undefined);

  if (scoredRows.length === 0) return null;

  // The calculators read every field of their position's shape, so zero-fill
  // targets this run did not predict rather than letting them read undefined.
  const stats = Object.fromEntries(
    scoredTargets.map((target) => [target, byTarget.get(target)?.predictedValue ?? 0])
  ) as unknown as AnyPrediction;

  const modelCount = scoredRows.filter((row) => row.source === "model").length;
  const baselineCount = scoredRows.length - modelCount;

  return {
    playerId: first.playerId,
    playerName: first.playerName,
    position: first.position,
    team: first.team,
    opponent: first.opponent,
    isHome: first.isHome,
    points: calculateFantasyPoints(first.position, stats, config),
    stats,
    sourceMix: resolveSourceMix(modelCount, baselineCount),
    modelCount,
    baselineCount,
    scoredRows,
  };
}

/** Group a week's rows by player and project each one. */
export function buildPlayerProjections(
  rows: readonly PredictionRow[] | undefined,
  config: FullScoringConfig
): Map<string, PlayerProjection> {
  const projections = new Map<string, PlayerProjection>();
  if (!rows) return projections;

  const byPlayer = new Map<string, PredictionRow[]>();
  for (const row of rows) {
    const existing = byPlayer.get(row.playerId);
    if (existing) {
      existing.push(row);
    } else {
      byPlayer.set(row.playerId, [row]);
    }
  }

  for (const [playerId, playerRows] of byPlayer) {
    const projection = toPlayerProjection(playerRows, config);
    if (projection) {
      projections.set(playerId, projection);
    }
  }

  return projections;
}

/** "vs. TB" / "@ WAS" — the matchup the prediction was generated against. */
export function formatMatchup(projection: {
  opponent?: string;
  isHome?: boolean;
}): string | null {
  if (!projection.opponent) return null;
  return `${projection.isHome ? "vs." : "@"} ${projection.opponent}`;
}
