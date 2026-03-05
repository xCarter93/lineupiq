"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";

interface SimulationInfo {
  /** Whether simulation mode is active */
  isActive: boolean;
  /** The season being simulated (e.g., 2025) */
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
  const state = useQuery(api.simulation.getSimulationState, {
    targetSeason: 2025,
  });

  if (!state) {
    // No simulation active - use real current week
    return {
      isActive: false,
      targetSeason: 2025,
      completedWeeks: 0,
      currentWeek: getCurrentNFLWeek(),
      trainingSeasons: [2022, 2023, 2024, 2025],
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

/**
 * Get the current NFL week based on the calendar.
 * This is used when simulation mode is not active.
 */
function getCurrentNFLWeek(): number {
  const now = new Date();
  const year = now.getFullYear();

  // NFL 2025 season starts ~Sep 4, 2025
  // Each week is roughly 7 days
  // This is a rough estimate - real implementation would use NFL schedule data
  const seasonStart = new Date(year, 8, 4); // September 4

  if (now < seasonStart) {
    return 1; // Preseason, show week 1
  }

  const daysSinceStart = Math.floor(
    (now.getTime() - seasonStart.getTime()) / (1000 * 60 * 60 * 24)
  );
  const week = Math.floor(daysSinceStart / 7) + 1;

  return Math.min(Math.max(week, 1), 18);
}
