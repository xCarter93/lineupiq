"use client";

import { useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { getCurrentSeason, getCurrentNFLWeek } from "@/lib/season";
import { useActiveScoringConfig } from "./useScoringConfigs";
import {
  buildPlayerProjections,
  toPlayerProjection,
  type PlayerProjection,
} from "@/lib/prediction-points";

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

/**
 * Every target predicted for a named set of players in one week — for lineup
 * surfaces, which need a handful of players rather than the whole grid.
 */
export function usePlayersWeekPredictions(
  playerIds: readonly string[],
  season?: number,
  week?: number
) {
  const resolvedSeason = season ?? getCurrentSeason();
  const resolvedWeek = week ?? getCurrentNFLWeek(resolvedSeason);
  // Sorted and deduped so the subscription key is stable across slot reorders.
  const ids = useMemo(
    () => Array.from(new Set(playerIds)).sort(),
    [playerIds]
  );

  const predictions = useQuery(
    api.predictions.byPlayersWeek,
    ids.length > 0
      ? { playerIds: ids, season: resolvedSeason, week: resolvedWeek }
      : "skip"
  );

  return {
    predictions: ids.length === 0 ? [] : predictions,
    isLoading: ids.length > 0 && predictions === undefined,
  };
}

/** The whole week's predictions, rolled into fantasy points per player. */
export function useWeekProjections(season?: number, week?: number) {
  const { predictions, isLoading } = useWeekPredictions(season, week);
  const { scoring, name } = useActiveScoringConfig();

  return {
    projections: useMemo(
      () => buildPlayerProjections(predictions, scoring),
      [predictions, scoring]
    ),
    scoringName: name,
    isLoading,
  };
}

/** One player's predictions, rolled into fantasy points. */
export function usePlayerWeekProjection(
  playerId: string,
  season?: number,
  week?: number
): {
  projection: PlayerProjection | null;
  scoringName: string;
  isLoading: boolean;
} {
  const { predictions, isLoading } = usePlayerWeekPredictions(
    playerId,
    season,
    week
  );
  const { scoring, name } = useActiveScoringConfig();

  return {
    projection: useMemo(
      () => (predictions ? toPlayerProjection(predictions, scoring) : null),
      [predictions, scoring]
    ),
    scoringName: name,
    isLoading,
  };
}

/** A named set of players' predictions, rolled into fantasy points per player. */
export function usePlayersWeekProjections(
  playerIds: readonly string[],
  season?: number,
  week?: number
) {
  const { predictions, isLoading } = usePlayersWeekPredictions(
    playerIds,
    season,
    week
  );
  const { scoring, name } = useActiveScoringConfig();

  return {
    projections: useMemo(
      () => buildPlayerProjections(predictions ?? undefined, scoring),
      [predictions, scoring]
    ),
    scoringName: name,
    isLoading,
  };
}
