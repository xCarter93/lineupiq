/**
 * Fantasy points calculator for predicted stats.
 * Calculates points using configurable scoring rules.
 * Supports all positions: QB, RB, WR, TE, K, DEF.
 */

import {
  FullScoringConfig,
  getPointsAllowedScore,
  DEFAULT_SCORING,
} from "./scoring-config";

// Legacy scoring config structure (matches Convex schema)
// Kept for backward compatibility with existing code
export interface ScoringConfig {
  passing: { yardsPerPoint: number; tdPoints: number; intPoints: number };
  rushing: { yardsPerPoint: number; tdPoints: number };
  receiving: { yardsPerPoint: number; tdPoints: number; receptionPoints: number };
}

// Prediction types (re-export compatible with prediction-api.ts)
export interface QBPrediction {
  passing_yards: number;
  passing_tds: number;
  interceptions: number;
  rushing_yards: number;
  rushing_tds: number;
  fumbles_lost: number;
}

export interface RBPrediction {
  rushing_yards: number;
  rushing_tds: number;
  carries: number;
  receiving_yards: number;
  receptions: number;
  receiving_tds: number;
  fumbles_lost: number;
}

export interface ReceiverPrediction {
  receiving_yards: number;
  receiving_tds: number;
  receptions: number;
  fumbles_lost: number;
}

// Kicker prediction type
export interface KickerPrediction {
  fg_att_0_39: number;
  fg_att_40_49: number;
  fg_att_50_plus: number;
  pat_att: number;
  // Optional: success rates for more accurate scoring
  fg_pct?: number;
  pat_pct?: number;
}

// Defense prediction type
export interface DefensePrediction {
  points_allowed: number;
  def_sacks: number;
  def_interceptions: number;
  def_fumbles: number; // Fumble recoveries
  total_def_tds: number; // Defensive + ST touchdowns
  // Optional stats
  def_safeties?: number;
  blocked_kicks?: number;
}

// Points breakdown for detailed display
export interface PointsBreakdown {
  total: number;
  categories: { label: string; points: number; detail: string }[];
}

// Union type for all predictions
export type AnyPrediction =
  | QBPrediction
  | RBPrediction
  | ReceiverPrediction
  | KickerPrediction
  | DefensePrediction;

/**
 * Calculate fantasy points for a QB prediction.
 * Includes passing, rushing, interceptions, and fumbles.
 */
export function calculateQBPoints(
  prediction: QBPrediction,
  config: ScoringConfig
): number {
  const passYardPoints = prediction.passing_yards / config.passing.yardsPerPoint;
  const passTdPoints = prediction.passing_tds * config.passing.tdPoints;
  const intPoints = prediction.interceptions * config.passing.intPoints; // intPoints is negative
  const rushYardPoints = prediction.rushing_yards / config.rushing.yardsPerPoint;
  const rushTdPoints = prediction.rushing_tds * config.rushing.tdPoints;
  const fumblePoints = prediction.fumbles_lost * -2; // -2 pts per fumble

  const total = passYardPoints + passTdPoints + intPoints + rushYardPoints + rushTdPoints + fumblePoints;
  return Math.round(total * 10) / 10;
}

/**
 * Calculate fantasy points for an RB prediction.
 * Combines rushing and receiving contributions, including fumbles.
 */
export function calculateRBPoints(
  prediction: RBPrediction,
  config: ScoringConfig
): number {
  const rushYardPoints = prediction.rushing_yards / config.rushing.yardsPerPoint;
  const rushTdPoints = prediction.rushing_tds * config.rushing.tdPoints;
  const recYardPoints = prediction.receiving_yards / config.receiving.yardsPerPoint;
  const recTdPoints = prediction.receiving_tds * config.receiving.tdPoints;
  const receptionPoints = prediction.receptions * config.receiving.receptionPoints;
  const fumblePoints = prediction.fumbles_lost * -2; // -2 pts per fumble

  const total = rushYardPoints + rushTdPoints + recYardPoints + recTdPoints + receptionPoints + fumblePoints;
  return Math.round(total * 10) / 10;
}

/**
 * Calculate fantasy points for a WR/TE prediction.
 * Includes receiving stats and fumbles.
 */
export function calculateReceiverPoints(
  prediction: ReceiverPrediction,
  config: ScoringConfig
): number {
  const yardPoints = prediction.receiving_yards / config.receiving.yardsPerPoint;
  const tdPoints = prediction.receiving_tds * config.receiving.tdPoints;
  const receptionPoints = prediction.receptions * config.receiving.receptionPoints;
  const fumblePoints = prediction.fumbles_lost * -2; // -2 pts per fumble

  const total = yardPoints + tdPoints + receptionPoints + fumblePoints;
  return Math.round(total * 10) / 10;
}

/**
 * Calculate fantasy points for a kicker prediction.
 * Uses expected value based on attempts and historical success rates.
 */
export function calculateKickerPoints(
  prediction: KickerPrediction,
  config: FullScoringConfig
): number {
  const k = config.kicking;

  // Use provided success rates or defaults (NFL averages)
  const fgPct = prediction.fg_pct ?? 0.85;
  const patPct = prediction.pat_pct ?? 0.94;

  // Expected FG points by distance
  const fg0_39 =
    prediction.fg_att_0_39 * (fgPct * k.fgMade0_39 + (1 - fgPct) * k.fgMissed0_39);
  const fg40_49 =
    prediction.fg_att_40_49 * (fgPct * k.fgMade40_49 + (1 - fgPct) * k.fgMissed40_49);
  const fg50Plus =
    prediction.fg_att_50_plus * (0.75 * k.fgMade50Plus + 0.25 * k.fgMissed50Plus); // Lower rate for long FGs

  // Expected PAT points
  const pat = prediction.pat_att * (patPct * k.xpMade + (1 - patPct) * k.xpMissed);

  const total = fg0_39 + fg40_49 + fg50Plus + pat;
  return Math.round(total * 10) / 10;
}

/**
 * Calculate fantasy points for a team defense prediction.
 */
export function calculateDefensePoints(
  prediction: DefensePrediction,
  config: FullScoringConfig
): number {
  const d = config.defense;

  // Points allowed tier
  const paPoints = getPointsAllowedScore(prediction.points_allowed, d);

  // Individual stat contributions
  const sackPoints = prediction.def_sacks * d.sack;
  const intPoints = prediction.def_interceptions * d.interception;
  const fumblePoints = prediction.def_fumbles * d.fumbleRecovery;
  const tdPoints = prediction.total_def_tds * d.defensiveTd;

  // Optional stats
  const safetyPoints = (prediction.def_safeties ?? 0) * d.safety;
  const blockedPoints = (prediction.blocked_kicks ?? 0) * d.blockedKick;

  const total =
    paPoints + sackPoints + intPoints + fumblePoints + tdPoints + safetyPoints + blockedPoints;
  return Math.round(total * 10) / 10;
}

/**
 * Route to the correct calculator based on position.
 * Supports: QB, RB, WR, TE, K, DEF
 *
 * For skill positions (QB, RB, WR, TE), accepts ScoringConfig for backward compatibility.
 * For K/DEF, requires FullScoringConfig.
 */
export function calculateFantasyPoints(
  position: string,
  prediction: AnyPrediction,
  config: ScoringConfig | FullScoringConfig = DEFAULT_SCORING
): number {
  const pos = position.toUpperCase();

  switch (pos) {
    case "QB":
      return calculateQBPoints(prediction as QBPrediction, config as ScoringConfig);
    case "RB":
      return calculateRBPoints(prediction as RBPrediction, config as ScoringConfig);
    case "WR":
    case "TE":
      return calculateReceiverPoints(prediction as ReceiverPrediction, config as ScoringConfig);
    case "K":
      return calculateKickerPoints(prediction as KickerPrediction, config as FullScoringConfig);
    case "DEF":
    case "DST":
      return calculateDefensePoints(prediction as DefensePrediction, config as FullScoringConfig);
    default:
      throw new Error(`Unsupported position: ${position}`);
  }
}

/**
 * Get detailed points breakdown showing contribution from each stat category.
 * Supports all positions: QB, RB, WR, TE, K, DEF
 */
export function getPointsBreakdown(
  position: string,
  prediction: AnyPrediction,
  config: ScoringConfig | FullScoringConfig = DEFAULT_SCORING
): PointsBreakdown {
  const pos = position.toUpperCase();
  const categories: { label: string; points: number; detail: string }[] = [];

  if (pos === "QB") {
    const qb = prediction as QBPrediction;
    const c = config as ScoringConfig;
    const passYardPoints = Math.round((qb.passing_yards / c.passing.yardsPerPoint) * 10) / 10;
    const passTdPoints = Math.round(qb.passing_tds * c.passing.tdPoints * 10) / 10;
    const intPoints = Math.round(qb.interceptions * c.passing.intPoints * 10) / 10;
    const rushYardPoints = Math.round((qb.rushing_yards / c.rushing.yardsPerPoint) * 10) / 10;
    const rushTdPoints = Math.round(qb.rushing_tds * c.rushing.tdPoints * 10) / 10;
    const fumblePoints = Math.round(qb.fumbles_lost * -2 * 10) / 10;

    categories.push({
      label: "Passing Yards",
      points: passYardPoints,
      detail: `${qb.passing_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Passing TDs",
      points: passTdPoints,
      detail: `${qb.passing_tds.toFixed(1)} TDs x ${c.passing.tdPoints} pts`,
    });
    categories.push({
      label: "Interceptions",
      points: intPoints,
      detail: `${qb.interceptions.toFixed(1)} INTs x ${c.passing.intPoints} pts`,
    });
    categories.push({
      label: "Rushing Yards",
      points: rushYardPoints,
      detail: `${qb.rushing_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Rushing TDs",
      points: rushTdPoints,
      detail: `${qb.rushing_tds.toFixed(1)} TDs x ${c.rushing.tdPoints} pts`,
    });
    categories.push({
      label: "Fumbles Lost",
      points: fumblePoints,
      detail: `${qb.fumbles_lost.toFixed(1)} fumbles x -2 pts`,
    });
  } else if (pos === "RB") {
    const rb = prediction as RBPrediction;
    const c = config as ScoringConfig;
    const rushYardPoints = Math.round((rb.rushing_yards / c.rushing.yardsPerPoint) * 10) / 10;
    const rushTdPoints = Math.round(rb.rushing_tds * c.rushing.tdPoints * 10) / 10;
    const recYardPoints = Math.round((rb.receiving_yards / c.receiving.yardsPerPoint) * 10) / 10;
    const recTdPoints = Math.round(rb.receiving_tds * c.receiving.tdPoints * 10) / 10;
    const receptionPoints = Math.round(rb.receptions * c.receiving.receptionPoints * 10) / 10;
    const fumblePoints = Math.round(rb.fumbles_lost * -2 * 10) / 10;

    categories.push({
      label: "Rushing Yards",
      points: rushYardPoints,
      detail: `${rb.rushing_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Rushing TDs",
      points: rushTdPoints,
      detail: `${rb.rushing_tds.toFixed(1)} TDs x ${c.rushing.tdPoints} pts`,
    });
    categories.push({
      label: "Receiving Yards",
      points: recYardPoints,
      detail: `${rb.receiving_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Receiving TDs",
      points: recTdPoints,
      detail: `${rb.receiving_tds.toFixed(1)} TDs x ${c.receiving.tdPoints} pts`,
    });
    if (c.receiving.receptionPoints > 0) {
      categories.push({
        label: "Receptions",
        points: receptionPoints,
        detail: `${rb.receptions.toFixed(1)} rec x ${c.receiving.receptionPoints} pts`,
      });
    }
    categories.push({
      label: "Fumbles Lost",
      points: fumblePoints,
      detail: `${rb.fumbles_lost.toFixed(1)} fumbles x -2 pts`,
    });
  } else if (pos === "WR" || pos === "TE") {
    const rec = prediction as ReceiverPrediction;
    const c = config as ScoringConfig;
    const yardPoints = Math.round((rec.receiving_yards / c.receiving.yardsPerPoint) * 10) / 10;
    const tdPoints = Math.round(rec.receiving_tds * c.receiving.tdPoints * 10) / 10;
    const receptionPoints = Math.round(rec.receptions * c.receiving.receptionPoints * 10) / 10;
    const fumblePoints = Math.round(rec.fumbles_lost * -2 * 10) / 10;

    categories.push({
      label: "Receiving Yards",
      points: yardPoints,
      detail: `${rec.receiving_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Receiving TDs",
      points: tdPoints,
      detail: `${rec.receiving_tds.toFixed(1)} TDs x ${c.receiving.tdPoints} pts`,
    });
    if (c.receiving.receptionPoints > 0) {
      categories.push({
        label: "Receptions",
        points: receptionPoints,
        detail: `${rec.receptions.toFixed(1)} rec x ${c.receiving.receptionPoints} pts`,
      });
    }
    categories.push({
      label: "Fumbles Lost",
      points: fumblePoints,
      detail: `${rec.fumbles_lost.toFixed(1)} fumbles x -2 pts`,
    });
  } else if (pos === "K") {
    const k = prediction as KickerPrediction;
    const kc = (config as FullScoringConfig).kicking;
    const fgPct = k.fg_pct ?? 0.85;

    if (k.fg_att_0_39 > 0) {
      const pts = Math.round(k.fg_att_0_39 * fgPct * kc.fgMade0_39 * 10) / 10;
      categories.push({
        label: "FG 0-39",
        points: pts,
        detail: `${k.fg_att_0_39.toFixed(1)} att x ${kc.fgMade0_39} pts`,
      });
    }

    if (k.fg_att_40_49 > 0) {
      const pts = Math.round(k.fg_att_40_49 * fgPct * kc.fgMade40_49 * 10) / 10;
      categories.push({
        label: "FG 40-49",
        points: pts,
        detail: `${k.fg_att_40_49.toFixed(1)} att x ${kc.fgMade40_49} pts`,
      });
    }

    if (k.fg_att_50_plus > 0) {
      const pts = Math.round(k.fg_att_50_plus * 0.75 * kc.fgMade50Plus * 10) / 10;
      categories.push({
        label: "FG 50+",
        points: pts,
        detail: `${k.fg_att_50_plus.toFixed(1)} att x ${kc.fgMade50Plus} pts`,
      });
    }

    if (k.pat_att > 0) {
      const pts = Math.round(k.pat_att * (k.pat_pct ?? 0.94) * kc.xpMade * 10) / 10;
      categories.push({
        label: "Extra Points",
        points: pts,
        detail: `${k.pat_att.toFixed(1)} att x ${kc.xpMade} pts`,
      });
    }
  } else if (pos === "DEF" || pos === "DST") {
    const d = prediction as DefensePrediction;
    const dc = (config as FullScoringConfig).defense;

    const paPoints = getPointsAllowedScore(d.points_allowed, dc);
    categories.push({
      label: "Points Allowed",
      points: paPoints,
      detail: `${d.points_allowed.toFixed(0)} pts allowed`,
    });

    if (d.def_sacks > 0) {
      categories.push({
        label: "Sacks",
        points: Math.round(d.def_sacks * dc.sack * 10) / 10,
        detail: `${d.def_sacks.toFixed(1)} sacks`,
      });
    }

    if (d.def_interceptions > 0) {
      categories.push({
        label: "Interceptions",
        points: Math.round(d.def_interceptions * dc.interception * 10) / 10,
        detail: `${d.def_interceptions.toFixed(1)} INTs`,
      });
    }

    if (d.def_fumbles > 0) {
      categories.push({
        label: "Fumble Rec",
        points: Math.round(d.def_fumbles * dc.fumbleRecovery * 10) / 10,
        detail: `${d.def_fumbles.toFixed(1)} fumbles`,
      });
    }

    if (d.total_def_tds > 0) {
      categories.push({
        label: "Def/ST TDs",
        points: Math.round(d.total_def_tds * dc.defensiveTd * 10) / 10,
        detail: `${d.total_def_tds.toFixed(1)} TDs`,
      });
    }
  }

  const total = categories.reduce((sum, cat) => sum + cat.points, 0);

  return {
    total: Math.round(total * 10) / 10,
    categories,
  };
}
