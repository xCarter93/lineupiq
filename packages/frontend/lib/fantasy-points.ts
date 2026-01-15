/**
 * Fantasy points calculator for predicted stats.
 * Calculates points using configurable scoring rules.
 */

// Scoring config structure (matches Convex schema)
export interface ScoringConfig {
  passing: { yardsPerPoint: number; tdPoints: number; intPoints: number };
  rushing: { yardsPerPoint: number; tdPoints: number };
  receiving: { yardsPerPoint: number; tdPoints: number; receptionPoints: number };
}

// Prediction types (re-export compatible with prediction-api.ts)
export interface QBPrediction {
  passing_yards: number;
  passing_tds: number;
}

export interface RBPrediction {
  rushing_yards: number;
  rushing_tds: number;
  carries: number;
  receiving_yards: number;
  receptions: number;
  // Note: API doesn't include receiving_tds for RBs
}

export interface ReceiverPrediction {
  receiving_yards: number;
  receiving_tds: number;
  receptions: number;
}

// Points breakdown for detailed display
export interface PointsBreakdown {
  total: number;
  categories: { label: string; points: number; detail: string }[];
}

/**
 * Calculate fantasy points for a QB prediction.
 * Formula: (passing_yards / yardsPerPoint) + (passing_tds * tdPoints)
 */
export function calculateQBPoints(
  prediction: QBPrediction,
  config: ScoringConfig
): number {
  const yardPoints = prediction.passing_yards / config.passing.yardsPerPoint;
  const tdPoints = prediction.passing_tds * config.passing.tdPoints;
  return Math.round((yardPoints + tdPoints) * 10) / 10;
}

/**
 * Calculate fantasy points for an RB prediction.
 * Combines rushing and receiving contributions.
 * Note: API doesn't predict receiving TDs for RBs.
 */
export function calculateRBPoints(
  prediction: RBPrediction,
  config: ScoringConfig
): number {
  const rushYardPoints = prediction.rushing_yards / config.rushing.yardsPerPoint;
  const rushTdPoints = prediction.rushing_tds * config.rushing.tdPoints;
  const recYardPoints = prediction.receiving_yards / config.receiving.yardsPerPoint;
  const receptionPoints = prediction.receptions * config.receiving.receptionPoints;

  const total = rushYardPoints + rushTdPoints + recYardPoints + receptionPoints;
  return Math.round(total * 10) / 10;
}

/**
 * Calculate fantasy points for a WR/TE prediction.
 * Formula: (receiving_yards / yardsPerPoint) + (receiving_tds * tdPoints) + (receptions * receptionPoints)
 */
export function calculateReceiverPoints(
  prediction: ReceiverPrediction,
  config: ScoringConfig
): number {
  const yardPoints = prediction.receiving_yards / config.receiving.yardsPerPoint;
  const tdPoints = prediction.receiving_tds * config.receiving.tdPoints;
  const receptionPoints = prediction.receptions * config.receiving.receptionPoints;

  const total = yardPoints + tdPoints + receptionPoints;
  return Math.round(total * 10) / 10;
}

/**
 * Route to the correct calculator based on position.
 */
export function calculateFantasyPoints(
  position: string,
  prediction: QBPrediction | RBPrediction | ReceiverPrediction,
  config: ScoringConfig
): number {
  const pos = position.toUpperCase();

  switch (pos) {
    case "QB":
      return calculateQBPoints(prediction as QBPrediction, config);
    case "RB":
      return calculateRBPoints(prediction as RBPrediction, config);
    case "WR":
    case "TE":
      return calculateReceiverPoints(prediction as ReceiverPrediction, config);
    default:
      throw new Error(`Unsupported position: ${position}`);
  }
}

/**
 * Get detailed points breakdown showing contribution from each stat category.
 */
export function getPointsBreakdown(
  position: string,
  prediction: QBPrediction | RBPrediction | ReceiverPrediction,
  config: ScoringConfig
): PointsBreakdown {
  const pos = position.toUpperCase();
  const categories: { label: string; points: number; detail: string }[] = [];

  if (pos === "QB") {
    const qb = prediction as QBPrediction;
    const yardPoints = Math.round((qb.passing_yards / config.passing.yardsPerPoint) * 10) / 10;
    const tdPoints = Math.round(qb.passing_tds * config.passing.tdPoints * 10) / 10;

    categories.push({
      label: "Passing Yards",
      points: yardPoints,
      detail: `${qb.passing_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Passing TDs",
      points: tdPoints,
      detail: `${qb.passing_tds.toFixed(1)} TDs x ${config.passing.tdPoints} pts`,
    });
  } else if (pos === "RB") {
    const rb = prediction as RBPrediction;
    const rushYardPoints = Math.round((rb.rushing_yards / config.rushing.yardsPerPoint) * 10) / 10;
    const rushTdPoints = Math.round(rb.rushing_tds * config.rushing.tdPoints * 10) / 10;
    const recYardPoints = Math.round((rb.receiving_yards / config.receiving.yardsPerPoint) * 10) / 10;
    const receptionPoints = Math.round(rb.receptions * config.receiving.receptionPoints * 10) / 10;

    categories.push({
      label: "Rushing Yards",
      points: rushYardPoints,
      detail: `${rb.rushing_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Rushing TDs",
      points: rushTdPoints,
      detail: `${rb.rushing_tds.toFixed(1)} TDs x ${config.rushing.tdPoints} pts`,
    });
    categories.push({
      label: "Receiving Yards",
      points: recYardPoints,
      detail: `${rb.receiving_yards.toFixed(1)} yards`,
    });
    if (config.receiving.receptionPoints > 0) {
      categories.push({
        label: "Receptions",
        points: receptionPoints,
        detail: `${rb.receptions.toFixed(1)} rec x ${config.receiving.receptionPoints} pts`,
      });
    }
  } else if (pos === "WR" || pos === "TE") {
    const rec = prediction as ReceiverPrediction;
    const yardPoints = Math.round((rec.receiving_yards / config.receiving.yardsPerPoint) * 10) / 10;
    const tdPoints = Math.round(rec.receiving_tds * config.receiving.tdPoints * 10) / 10;
    const receptionPoints = Math.round(rec.receptions * config.receiving.receptionPoints * 10) / 10;

    categories.push({
      label: "Receiving Yards",
      points: yardPoints,
      detail: `${rec.receiving_yards.toFixed(1)} yards`,
    });
    categories.push({
      label: "Receiving TDs",
      points: tdPoints,
      detail: `${rec.receiving_tds.toFixed(1)} TDs x ${config.receiving.tdPoints} pts`,
    });
    if (config.receiving.receptionPoints > 0) {
      categories.push({
        label: "Receptions",
        points: receptionPoints,
        detail: `${rec.receptions.toFixed(1)} rec x ${config.receiving.receptionPoints} pts`,
      });
    }
  }

  const total = categories.reduce((sum, cat) => sum + cat.points, 0);

  return {
    total: Math.round(total * 10) / 10,
    categories,
  };
}
