"use client";

import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";

/**
 * Hook to get a prediction for a player
 * If week/season provided, gets specific prediction
 * Otherwise gets most recent by createdAt
 *
 * @example
 * const { prediction, isLoading } = usePrediction("player-123");
 * const { prediction, isLoading } = usePrediction("player-123", 10, 2024);
 */
export function usePrediction(
  playerId: string,
  week?: number,
  season?: number
) {
  const prediction = useQuery(api.predictions.getByPlayer, {
    playerId,
    week,
    season,
  });
  return {
    prediction,
    isLoading: prediction === undefined,
  };
}

/**
 * Hook to get recent predictions
 *
 * @example
 * const { predictions, isLoading } = useRecentPredictions();
 * const { predictions, isLoading } = useRecentPredictions(20);
 */
export function useRecentPredictions(limit = 10) {
  const predictions = useQuery(api.predictions.listRecent, { limit });
  return {
    predictions,
    isLoading: predictions === undefined,
  };
}

/**
 * Hook returning mutation functions for prediction operations
 *
 * @example
 * const { store, remove, clearOld } = usePredictionMutations();
 *
 * // Store a prediction
 * await store({
 *   playerId: "player-123",
 *   position: "QB",
 *   week: 10,
 *   season: 2024,
 *   predictions: { passing_yards: 280.5, passing_tds: 2.1 },
 * });
 *
 * // Remove a prediction
 * await remove({ id: predictionId });
 *
 * // Clear old predictions (default 7 days)
 * const count = await clearOld({ daysOld: 14 });
 */
export function usePredictionMutations() {
  const store = useMutation(api.predictions.store);
  const remove = useMutation(api.predictions.remove);
  const clearOld = useMutation(api.predictions.clearOld);

  return {
    store,
    remove,
    clearOld,
  };
}
