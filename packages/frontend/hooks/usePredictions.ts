"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { getCurrentSeason, getCurrentNFLWeek } from "@/lib/season";

/**
 * Every prediction for a season/week — one query for the whole weekly grid.
 * Defaults to the current season/week.
 *
 * @example
 * const { predictions, isLoading } = useWeekPredictions();
 * const { predictions, isLoading } = useWeekPredictions(2026, 3);
 */
export function useWeekPredictions(season?: number, week?: number) {
  const resolvedSeason = season ?? getCurrentSeason();
  const predictions = useQuery(api.predictions.byWeek, {
    season: resolvedSeason,
    week: week ?? getCurrentNFLWeek(resolvedSeason),
  });

  return {
    predictions,
    isLoading: predictions === undefined,
  };
}

/**
 * Every target predicted for one player in one week.
 * Defaults to the current season/week.
 *
 * @example
 * const { predictions, isLoading } = usePlayerWeekPredictions("00-0034796");
 */
export function usePlayerWeekPredictions(
  playerId: string,
  season?: number,
  week?: number
) {
  const resolvedSeason = season ?? getCurrentSeason();
  const predictions = useQuery(api.predictions.byPlayerWeek, {
    playerId,
    season: resolvedSeason,
    week: week ?? getCurrentNFLWeek(resolvedSeason),
  });

  return {
    predictions,
    isLoading: predictions === undefined,
  };
}
