"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import {
  getCurrentNFLWeek,
  getCurrentSeason,
  getDefaultTrainingSeasons,
} from "@/lib/season";

interface SimulationInfo {
  /** Whether simulation mode is active */
  isActive: boolean;
  /** The season being simulated (e.g., 2026) */
  targetSeason: number;
  /** Weeks that have been "played" (have actual data in training) */
  completedWeeks: number;
  /** The week the app should display as "current" (next to be played) */
  currentWeek: number;
  /** Training seasons (e.g., [2022, 2023, 2024]) */
  trainingSeasons: number[];
  /** Current simulation status */
  status: string;
  /** Whether simulation is busy (training, predicting, etc.) */
  isBusy: boolean;
}

/**
 * Hook to access simulation state throughout the app.
 *
 * Use this to make the app behave as if it's a specific week of the season.
 *
 * @example
 * ```tsx
 * const { currentWeek, isActive } = useSimulation();
 *
 * // Use currentWeek to fetch predictions for the "current" week
 * const predictions = usePredictions(playerId, currentWeek);
 * ```
 */
export function useSimulation(): SimulationInfo {
  const currentSeason = getCurrentSeason();
  const state = useQuery(api.simulation.getSimulationState, {
    targetSeason: currentSeason,
  });

  if (!state) {
    // No simulation active - use real current week
    return {
      isActive: false,
      targetSeason: currentSeason,
      completedWeeks: 0,
      currentWeek: getCurrentNFLWeek(currentSeason),
      trainingSeasons: getDefaultTrainingSeasons(currentSeason),
      status: "ready",
      isBusy: false,
    };
  }

  // Simulation is active
  // currentWeek in state = the week we're ON (predicting)
  // completedWeeks = weeks with actual data = currentWeek - 1
  const appWeek = state.currentWeek;
  const completedWeeks = Math.max(0, state.currentWeek - 1);

  return {
    isActive: true,
    targetSeason: state.targetSeason,
    completedWeeks,
    currentWeek: appWeek,
    trainingSeasons: state.trainingSeasons,
    status: state.status,
    isBusy: state.status !== "ready",
  };
}
