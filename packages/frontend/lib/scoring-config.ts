/**
 * Fantasy scoring configuration with ESPN standard defaults.
 * Supports all position types: QB, RB, WR, TE, K, DEF.
 */

// Full scoring configuration interface
export interface FullScoringConfig {
  passing: {
    yardsPerPoint: number; // e.g., 25 = 1 point per 25 yards
    tdPoints: number; // Points per passing TD
    intPoints: number; // Points per interception (negative)
    twoPtConversion: number; // Points per 2-pt conversion
  };
  rushing: {
    yardsPerPoint: number;
    tdPoints: number;
    twoPtConversion: number;
    fumblesLostPoints: number; // Points per fumble lost (negative)
  };
  receiving: {
    yardsPerPoint: number;
    tdPoints: number;
    receptionPoints: number; // PPR points
    twoPtConversion: number;
    fumblesLostPoints: number;
  };
  kicking: {
    fgMade0_39: number; // FG 0-39 yards
    fgMade40_49: number; // FG 40-49 yards
    fgMade50Plus: number; // FG 50+ yards
    fgMissed0_39: number; // Missed FG penalties
    fgMissed40_49: number;
    fgMissed50Plus: number;
    xpMade: number; // Extra point made
    xpMissed: number; // Extra point missed
  };
  defense: {
    sack: number;
    interception: number;
    fumbleRecovery: number;
    defensiveTd: number;
    safety: number;
    blockedKick: number;
    returnTd: number; // Kick/punt return TD
    // Points allowed tiers
    pointsAllowed0: number;
    pointsAllowed1_6: number;
    pointsAllowed7_13: number;
    pointsAllowed14_20: number;
    pointsAllowed21_27: number;
    pointsAllowed28_34: number;
    pointsAllowed35Plus: number;
  };
}

// ESPN Standard Scoring (non-PPR)
export const ESPN_STANDARD: FullScoringConfig = {
  passing: {
    yardsPerPoint: 25,
    tdPoints: 4,
    intPoints: -2,
    twoPtConversion: 2,
  },
  rushing: {
    yardsPerPoint: 10,
    tdPoints: 6,
    twoPtConversion: 2,
    fumblesLostPoints: -2,
  },
  receiving: {
    yardsPerPoint: 10,
    tdPoints: 6,
    receptionPoints: 0, // Standard = no PPR
    twoPtConversion: 2,
    fumblesLostPoints: -2,
  },
  kicking: {
    fgMade0_39: 3,
    fgMade40_49: 4,
    fgMade50Plus: 5,
    fgMissed0_39: 0,
    fgMissed40_49: -1,
    fgMissed50Plus: 0,
    xpMade: 1,
    xpMissed: -1,
  },
  defense: {
    sack: 1,
    interception: 2,
    fumbleRecovery: 2,
    defensiveTd: 6,
    safety: 2,
    blockedKick: 2,
    returnTd: 6,
    pointsAllowed0: 10,
    pointsAllowed1_6: 7,
    pointsAllowed7_13: 4,
    pointsAllowed14_20: 1,
    pointsAllowed21_27: 0,
    pointsAllowed28_34: -1,
    pointsAllowed35Plus: -4,
  },
};

// ESPN PPR Scoring
export const ESPN_PPR: FullScoringConfig = {
  ...ESPN_STANDARD,
  receiving: {
    ...ESPN_STANDARD.receiving,
    receptionPoints: 1, // 1 point per reception
  },
};

// Half-PPR Scoring
export const ESPN_HALF_PPR: FullScoringConfig = {
  ...ESPN_STANDARD,
  receiving: {
    ...ESPN_STANDARD.receiving,
    receptionPoints: 0.5,
  },
};

// Default config (can be changed based on user preference)
export const DEFAULT_SCORING = ESPN_STANDARD;

/**
 * The `scoringConfigs` Convex document shape, which names its kicking/defense
 * fields differently from FullScoringConfig and may omit them entirely.
 */
export interface StoredScoringConfig {
  name: string;
  passing: { yardsPerPoint: number; tdPoints: number; intPoints: number };
  rushing: { yardsPerPoint: number; tdPoints: number };
  receiving: {
    yardsPerPoint: number;
    tdPoints: number;
    receptionPoints: number;
  };
  kicking?: {
    fgPoints: number;
    fg40_49Points: number;
    fg50PlusPoints: number;
    patPoints: number;
    missPoints: number;
  };
  defense?: {
    sackPoints: number;
    intPoints: number;
    fumbleRecPoints: number;
    tdPoints: number;
    safetyPoints: number;
    ptsAllowed0?: number;
    ptsAllowed1_6?: number;
    ptsAllowed7_13?: number;
    ptsAllowed14_20?: number;
    ptsAllowed21_27?: number;
    ptsAllowed28_34?: number;
    ptsAllowed35Plus?: number;
  };
}

/**
 * Widen a stored config into the full one the calculators expect, keeping ESPN
 * standard values for anything the stored config does not carry.
 */
export function toFullScoringConfig(
  stored: StoredScoringConfig | null | undefined
): FullScoringConfig {
  if (!stored) return DEFAULT_SCORING;

  const k = stored.kicking;
  const d = stored.defense;

  return {
    passing: { ...ESPN_STANDARD.passing, ...stored.passing },
    rushing: { ...ESPN_STANDARD.rushing, ...stored.rushing },
    receiving: { ...ESPN_STANDARD.receiving, ...stored.receiving },
    kicking: k
      ? {
          fgMade0_39: k.fgPoints,
          fgMade40_49: k.fg40_49Points,
          fgMade50Plus: k.fg50PlusPoints,
          fgMissed0_39: k.missPoints,
          fgMissed40_49: k.missPoints,
          fgMissed50Plus: k.missPoints,
          xpMade: k.patPoints,
          xpMissed: k.missPoints,
        }
      : ESPN_STANDARD.kicking,
    defense: d
      ? {
          sack: d.sackPoints,
          interception: d.intPoints,
          fumbleRecovery: d.fumbleRecPoints,
          defensiveTd: d.tdPoints,
          safety: d.safetyPoints,
          blockedKick: ESPN_STANDARD.defense.blockedKick,
          returnTd: d.tdPoints,
          pointsAllowed0: d.ptsAllowed0 ?? ESPN_STANDARD.defense.pointsAllowed0,
          pointsAllowed1_6:
            d.ptsAllowed1_6 ?? ESPN_STANDARD.defense.pointsAllowed1_6,
          pointsAllowed7_13:
            d.ptsAllowed7_13 ?? ESPN_STANDARD.defense.pointsAllowed7_13,
          pointsAllowed14_20:
            d.ptsAllowed14_20 ?? ESPN_STANDARD.defense.pointsAllowed14_20,
          pointsAllowed21_27:
            d.ptsAllowed21_27 ?? ESPN_STANDARD.defense.pointsAllowed21_27,
          pointsAllowed28_34:
            d.ptsAllowed28_34 ?? ESPN_STANDARD.defense.pointsAllowed28_34,
          pointsAllowed35Plus:
            d.ptsAllowed35Plus ?? ESPN_STANDARD.defense.pointsAllowed35Plus,
        }
      : ESPN_STANDARD.defense,
  };
}

/**
 * Get points allowed fantasy points based on tier.
 */
export function getPointsAllowedScore(
  pointsAllowed: number,
  config: FullScoringConfig["defense"]
): number {
  if (pointsAllowed === 0) return config.pointsAllowed0;
  if (pointsAllowed <= 6) return config.pointsAllowed1_6;
  if (pointsAllowed <= 13) return config.pointsAllowed7_13;
  if (pointsAllowed <= 20) return config.pointsAllowed14_20;
  if (pointsAllowed <= 27) return config.pointsAllowed21_27;
  if (pointsAllowed <= 34) return config.pointsAllowed28_34;
  return config.pointsAllowed35Plus;
}
