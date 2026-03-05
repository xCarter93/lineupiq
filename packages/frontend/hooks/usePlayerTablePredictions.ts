"use client";

import { useState, useEffect, useMemo } from "react";
import { useSimulation } from "./useSimulation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Standard PPR scoring values
const SCORING_VALUES: Record<string, number> = {
  passing_yards: 0.04, // 1 point per 25 yards
  passing_tds: 4,
  interceptions: -2,
  rushing_yards: 0.1,
  rushing_tds: 6,
  receiving_yards: 0.1,
  receiving_tds: 6,
  receptions: 1,
  fumbles_lost: -2,
  // Kicker scoring
  fg_att_0_39: 3,
  fg_att_40_49: 4,
  fg_att_50_plus: 5,
  pat_att: 1,
  // Defense scoring (individual stats, points_allowed handled separately)
  def_sacks: 1,
  def_interceptions: 2,
  def_fumbles: 2,
  total_def_tds: 6,
};

// Defense points allowed scoring (bracket-based)
function getDefensePointsAllowedScore(pointsAllowed: number): number {
  if (pointsAllowed <= 0) return 10;
  if (pointsAllowed <= 6) return 7;
  if (pointsAllowed <= 13) return 4;
  if (pointsAllowed <= 20) return 1;
  if (pointsAllowed <= 27) return 0;
  if (pointsAllowed <= 34) return -1;
  return -4;
}

// API returns predictions with stats as columns
interface PlayerPredictionRow {
  player_id: string;
  player_name: string;
  position: string;
  team: string;
  opponent: string;
  season: number;
  week: number;
  // Skill position stats
  passing_yards?: number | null;
  passing_tds?: number | null;
  interceptions?: number | null;
  rushing_yards?: number | null;
  rushing_tds?: number | null;
  receiving_yards?: number | null;
  receiving_tds?: number | null;
  receptions?: number | null;
  fumbles_lost?: number | null;
  carries?: number | null;
  // Kicker stats
  fg_att?: number | null;
  fg_att_0_39?: number | null;
  fg_att_40_49?: number | null;
  fg_att_50_plus?: number | null;
  pat_att?: number | null;
  // Defense stats
  points_allowed?: number | null;
  def_sacks?: number | null;
  def_interceptions?: number | null;
  def_fumbles?: number | null;
  total_def_tds?: number | null;
}

export interface PlayerProjectedStats {
  playerId: string;
  playerName: string;
  thisWeekProj: number | null;
  lastWeekActual: number | null;
  lastWeekPred: number | null;
  seasonAvg: number | null;
  trend: "up" | "down" | "flat";
}

interface UsePlayerTablePredictionsResult {
  /** Stats by player ID (GSIS ID like "00-0033873") */
  playerStats: Map<string, PlayerProjectedStats>;
  /** Stats by player name (for fallback matching) */
  playerStatsByName: Map<string, PlayerProjectedStats>;
  isLoading: boolean;
  error: string | null;
  currentWeek: number;
}

/**
 * Calculate fantasy points from a player prediction row
 */
function calculateFantasyPointsFromRow(row: PlayerPredictionRow): number {
  let points = 0;
  const position = row.position;

  // Kicker scoring
  if (position === "K") {
    if (row.fg_att_0_39 != null) {
      points += row.fg_att_0_39 * SCORING_VALUES.fg_att_0_39;
    }
    if (row.fg_att_40_49 != null) {
      points += row.fg_att_40_49 * SCORING_VALUES.fg_att_40_49;
    }
    if (row.fg_att_50_plus != null) {
      points += row.fg_att_50_plus * SCORING_VALUES.fg_att_50_plus;
    }
    if (row.pat_att != null) {
      points += row.pat_att * SCORING_VALUES.pat_att;
    }
    return points;
  }

  // Defense scoring
  if (position === "DEF") {
    if (row.points_allowed != null) {
      points += getDefensePointsAllowedScore(row.points_allowed);
    }
    if (row.def_sacks != null) {
      points += row.def_sacks * SCORING_VALUES.def_sacks;
    }
    if (row.def_interceptions != null) {
      points += row.def_interceptions * SCORING_VALUES.def_interceptions;
    }
    if (row.def_fumbles != null) {
      points += row.def_fumbles * SCORING_VALUES.def_fumbles;
    }
    if (row.total_def_tds != null) {
      points += row.total_def_tds * SCORING_VALUES.total_def_tds;
    }
    return points;
  }

  // Skill position scoring (QB, RB, WR, TE)
  if (row.passing_yards != null) {
    points += row.passing_yards * SCORING_VALUES.passing_yards;
  }
  if (row.passing_tds != null) {
    points += row.passing_tds * SCORING_VALUES.passing_tds;
  }
  if (row.interceptions != null) {
    points += row.interceptions * SCORING_VALUES.interceptions;
  }
  if (row.rushing_yards != null) {
    points += row.rushing_yards * SCORING_VALUES.rushing_yards;
  }
  if (row.rushing_tds != null) {
    points += row.rushing_tds * SCORING_VALUES.rushing_tds;
  }
  if (row.receiving_yards != null) {
    points += row.receiving_yards * SCORING_VALUES.receiving_yards;
  }
  if (row.receiving_tds != null) {
    points += row.receiving_tds * SCORING_VALUES.receiving_tds;
  }
  if (row.receptions != null) {
    points += row.receptions * SCORING_VALUES.receptions;
  }
  if (row.fumbles_lost != null) {
    points += row.fumbles_lost * SCORING_VALUES.fumbles_lost;
  }

  return points;
}

/**
 * Hook to fetch player predictions for the table display.
 * Returns projected points for current week and last week (if available).
 */
export function usePlayerTablePredictions(): UsePlayerTablePredictionsResult {
  const simulation = useSimulation();
  const [predictions, setPredictions] = useState<PlayerPredictionRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Determine which weeks to fetch
  const currentWeek = simulation.isActive ? simulation.currentWeek : 1;
  const lastWeek = simulation.completedWeeks > 0 ? simulation.completedWeeks : null;

  // Store actuals fetched from backend
  const [actuals, setActuals] = useState<Map<string, number>>(new Map());

  // Fetch predictions and actuals
  useEffect(() => {
    if (!simulation.isActive) {
      setPredictions([]);
      setActuals(new Map());
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch predictions for current week and last week
        const weeksToFetch = [currentWeek];
        if (lastWeek) {
          weeksToFetch.push(lastWeek);
        }

        const allPredictions: PlayerPredictionRow[] = [];

        for (const week of weeksToFetch) {
          const response = await fetch(
            `${API_BASE_URL}/api/simulation/predictions/${week}`
          );

          if (response.ok) {
            const data = await response.json();
            if (data.predictions) {
              allPredictions.push(...data.predictions);
            }
          }
        }

        setPredictions(allPredictions);

        // Fetch actuals for last completed week from backend API
        if (lastWeek) {
          const actualsResponse = await fetch(
            `${API_BASE_URL}/api/simulation/actuals/${lastWeek}`
          );

          if (actualsResponse.ok) {
            const actualsData = await actualsResponse.json();
            const actualsMap = new Map<string, number>();
            for (const actual of actualsData.actuals || []) {
              if (actual.player_id && actual.fantasy_points != null) {
                actualsMap.set(actual.player_id, actual.fantasy_points);
              }
            }
            setActuals(actualsMap);
          }
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch data"
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [simulation.isActive, currentWeek, lastWeek]);

  // actualsMap is already built in the useEffect above, just use it directly

  // Build maps of player stats by ID and by name
  const { playerStats, playerStatsByName } = useMemo(() => {
    const statsById = new Map<string, PlayerProjectedStats>();
    const statsByName = new Map<string, PlayerProjectedStats>();

    if (!simulation.isActive || predictions.length === 0) {
      return { playerStats: statsById, playerStatsByName: statsByName };
    }

    // Group predictions by player ID
    const playerPredictions = new Map<string, PlayerPredictionRow[]>();
    for (const pred of predictions) {
      const existing = playerPredictions.get(pred.player_id) || [];
      existing.push(pred);
      playerPredictions.set(pred.player_id, existing);
    }

    for (const [playerId, preds] of playerPredictions) {
      // Find this week's prediction
      const thisWeekPred = preds.find((p) => p.week === currentWeek);
      const thisWeekProj = thisWeekPred
        ? calculateFantasyPointsFromRow(thisWeekPred)
        : null;

      // Get player name from any prediction
      const playerName = preds[0]?.player_name || "";

      // Find last week's prediction and actual if we have completed weeks
      let lastWeekActual: number | null = null;
      let lastWeekPred: number | null = null;

      if (lastWeek) {
        const lastWeekPredRow = preds.find((p) => p.week === lastWeek);
        lastWeekPred = lastWeekPredRow
          ? calculateFantasyPointsFromRow(lastWeekPredRow)
          : null;
        // Get actual from backend API
        lastWeekActual = actuals.get(playerId) ?? null;
      }

      // Calculate trend based on actual vs predicted
      let trend: "up" | "down" | "flat" = "flat";
      if (lastWeekActual != null && lastWeekPred != null) {
        const diff = lastWeekActual - lastWeekPred;
        if (diff > 2) trend = "up";
        else if (diff < -2) trend = "down";
      }

      const seasonAvg = thisWeekProj;

      const stats: PlayerProjectedStats = {
        playerId,
        playerName,
        thisWeekProj,
        lastWeekActual,
        lastWeekPred,
        seasonAvg,
        trend,
      };

      statsById.set(playerId, stats);

      // Also store by normalized name for fallback matching
      if (playerName) {
        const normalizedName = playerName.toLowerCase().trim();
        statsByName.set(normalizedName, stats);
      }
    }

    return { playerStats: statsById, playerStatsByName: statsByName };
  }, [predictions, simulation.isActive, currentWeek, lastWeek, actuals]);

  return {
    playerStats,
    playerStatsByName,
    isLoading,
    error,
    currentWeek,
  };
}
