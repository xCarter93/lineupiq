"use client";

import { useState, useEffect, useMemo } from "react";
import { useSimulation } from "./useSimulation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SimulationPrediction {
  player_id: string;
  player_name: string;
  position: string;
  team: string;
  opponent: string;
  season: number;
  week: number;
  // QB stats
  passing_yards?: number;
  passing_tds?: number;
  interceptions?: number;
  rushing_yards?: number;
  rushing_tds?: number;
  fumbles_lost?: number;
  // RB/WR/TE stats
  carries?: number;
  receiving_yards?: number;
  receptions?: number;
  receiving_tds?: number;
  // Kicker stats
  fg_att?: number;
  fg_att_0_39?: number;
  fg_att_40_49?: number;
  fg_att_50_plus?: number;
  pat_att?: number;
  // Defense stats
  points_allowed?: number;
  def_sacks?: number;
  def_interceptions?: number;
  def_fumbles?: number;
  total_def_tds?: number;
}

interface ActualStats {
  player_id: string;
  player_name: string;
  position: string;
  team: string;
  week: number;
  season: number;
  fantasy_points: number;
  passing_yards?: number;
  passing_tds?: number;
  interceptions?: number;
  rushing_yards?: number;
  rushing_tds?: number;
  receiving_yards?: number;
  receiving_tds?: number;
  receptions?: number;
  // Kicker stats
  fg_made?: number;
  fg_att?: number;
  fg_att_0_39?: number;
  fg_att_40_49?: number;
  fg_att_50_plus?: number;
  pat_made?: number;
  pat_att?: number;
  // Defense stats
  points_allowed?: number;
  def_sacks?: number;
  def_interceptions?: number;
  def_fumbles?: number;
  total_def_tds?: number;
}

interface SimulationPredictionsResponse {
  week: number;
  season: number;
  count: number;
  predictions: SimulationPrediction[];
}

interface ActualsResponse {
  week: number;
  season: number;
  count: number;
  actuals: ActualStats[];
}

interface UseSimulationPredictionsResult {
  /** All predictions for this player across all weeks */
  predictions: SimulationPrediction[];
  /** Prediction for the current simulation week */
  currentWeekPrediction: SimulationPrediction | null;
  /** Predictions grouped by stat for chart display (includes actuals for completed weeks) */
  groupedByTarget: Record<string, Array<{ week: number; predicted: number; actual?: number }>> | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook to fetch simulation predictions for a player.
 * Only active when simulation mode is enabled.
 * Also fetches actuals for completed weeks.
 */
export function useSimulationPredictions(
  playerId: string | null,
  position: string
): UseSimulationPredictionsResult {
  const simulation = useSimulation();
  const [allPredictions, setAllPredictions] = useState<SimulationPrediction[]>([]);
  const [actuals, setActuals] = useState<Map<number, ActualStats>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch predictions for all weeks and actuals for completed weeks (in parallel)
  useEffect(() => {
    if (!playerId || !simulation.isActive) {
      setAllPredictions([]);
      setActuals(new Map());
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch predictions for all weeks in parallel
        const weeks = Array.from({ length: 18 }, (_, i) => i + 1);
        const predictionPromises = weeks.map(async (week) => {
          try {
            const response = await fetch(
              `${API_BASE_URL}/api/simulation/predictions/${week}?position=${position}`
            );

            if (!response.ok) {
              return null; // No predictions for this week
            }

            const data: SimulationPredictionsResponse = await response.json();
            return data.predictions.find(p => p.player_id === playerId) || null;
          } catch {
            return null;
          }
        });

        // Fetch actuals for completed weeks in parallel
        const completedWeeks = Array.from({ length: simulation.completedWeeks }, (_, i) => i + 1);
        const actualsPromises = completedWeeks.map(async (week) => {
          try {
            const response = await fetch(
              `${API_BASE_URL}/api/simulation/actuals/${week}`
            );

            if (!response.ok) {
              return null;
            }

            const data: ActualsResponse = await response.json();
            const playerActual = data.actuals.find(a => a.player_id === playerId);
            return playerActual ? { week, actual: playerActual } : null;
          } catch {
            return null;
          }
        });

        // Wait for all requests in parallel
        const [predictionResults, actualsResults] = await Promise.all([
          Promise.all(predictionPromises),
          Promise.all(actualsPromises),
        ]);

        // Filter out nulls and collect results
        const predictions = predictionResults.filter((p): p is SimulationPrediction => p !== null);

        const actualsMap = new Map<number, ActualStats>();
        for (const result of actualsResults) {
          if (result) {
            actualsMap.set(result.week, result.actual);
          }
        }

        setAllPredictions(predictions);
        setActuals(actualsMap);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch predictions");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [playerId, position, simulation.isActive, simulation.completedWeeks]);

  // Get current week prediction
  const currentWeekPrediction = useMemo(() => {
    const targetWeek = simulation.currentWeek;
    return allPredictions.find(p => p.week === targetWeek) || null;
  }, [allPredictions, simulation.currentWeek]);

  // Group predictions by stat target for charts (include actuals for completed weeks)
  const groupedByTarget = useMemo(() => {
    if (allPredictions.length === 0) return null;

    const groups: Record<string, Array<{ week: number; predicted: number; actual?: number }>> = {};

    // Determine which stats to include based on position
    const statKeys = position === "QB"
      ? ["passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds", "fumbles_lost"]
      : position === "RB"
      ? ["rushing_yards", "rushing_tds", "carries", "receiving_yards", "receptions", "receiving_tds", "fumbles_lost"]
      : position === "K"
      ? ["fg_att", "fg_att_0_39", "fg_att_40_49", "fg_att_50_plus", "pat_att"]
      : position === "DEF"
      ? ["points_allowed", "def_sacks", "def_interceptions", "def_fumbles", "total_def_tds"]
      : ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"];

    for (const stat of statKeys) {
      groups[stat] = allPredictions
        .filter(p => p[stat as keyof SimulationPrediction] !== null && p[stat as keyof SimulationPrediction] !== undefined)
        .map(p => {
          const weekActual = actuals.get(p.week);
          const actualValue = weekActual?.[stat as keyof ActualStats] as number | undefined;
          return {
            week: p.week,
            predicted: p[stat as keyof SimulationPrediction] as number,
            actual: actualValue,
          };
        })
        .sort((a, b) => a.week - b.week);
    }

    return groups;
  }, [allPredictions, actuals, position]);

  return {
    predictions: allPredictions,
    currentWeekPrediction,
    groupedByTarget,
    isLoading,
    error,
  };
}
