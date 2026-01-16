"use client";

import { useQuery, useMutation } from "convex/react";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/convex/_generated/api";
import { fetchPlayerHistory } from "@/lib/roster-api";

interface HistoryGame {
  season: number;
  week: number;
  opponentTeam?: string;
  passingYards?: number;
  passingTds?: number;
  interceptions?: number;
  rushingYards?: number;
  rushingTds?: number;
  carries?: number;
  receivingYards?: number;
  receivingTds?: number;
  receptions?: number;
  fantasyPoints?: number;
}

interface UsePlayerHistoryResult {
  games: HistoryGame[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to get player's historical stats.
 * Checks Convex cache first, fetches from API if missing.
 */
export function usePlayerHistory(
  playerId: string | null,
  seasons: number = 3
): UsePlayerHistoryResult {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Query Convex for cached history
  const cachedGames = useQuery(
    api.playerHistory.getRecentGames,
    playerId ? { playerId, limit: seasons * 20 } : "skip"
  );

  const bulkUpsertHistory = useMutation(api.playerHistory.bulkUpsert);

  // Fetch from API and cache in Convex
  const fetchAndCache = useCallback(async () => {
    if (!playerId) return;

    setIsLoading(true);
    setError(null);

    try {
      const { games } = await fetchPlayerHistory(playerId, seasons);

      // Convert to Convex format and cache
      const convexGames = games.map(g => ({
        playerId,
        season: g.season,
        week: g.week,
        opponentTeam: g.opponent_team ?? undefined,
        passingYards: g.passing_yards ?? undefined,
        passingTds: g.passing_tds ?? undefined,
        interceptions: g.interceptions ?? undefined,
        rushingYards: g.rushing_yards ?? undefined,
        rushingTds: g.rushing_tds ?? undefined,
        carries: g.carries ?? undefined,
        receivingYards: g.receiving_yards ?? undefined,
        receivingTds: g.receiving_tds ?? undefined,
        receptions: g.receptions ?? undefined,
        fantasyPoints: g.fantasy_points ?? undefined,
      }));

      await bulkUpsertHistory({ games: convexGames });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch history");
    } finally {
      setIsLoading(false);
    }
  }, [playerId, seasons, bulkUpsertHistory]);

  // Auto-fetch if no cached data exists
  useEffect(() => {
    if (playerId && cachedGames !== undefined && cachedGames.length === 0) {
      fetchAndCache();
    }
  }, [playerId, cachedGames, fetchAndCache]);

  return {
    games: cachedGames ?? [],
    isLoading: isLoading || cachedGames === undefined,
    error,
    refetch: fetchAndCache,
  };
}

/**
 * Calculate season averages from game data.
 */
export function calculateSeasonAverages(games: HistoryGame[], season: number) {
  const seasonGames = games.filter(g => g.season === season);
  if (seasonGames.length === 0) return null;

  const sum = (key: keyof HistoryGame) =>
    seasonGames.reduce((acc, g) => acc + (Number(g[key]) || 0), 0);

  const count = seasonGames.length;

  return {
    season,
    games: count,
    passingYards: sum("passingYards") / count,
    passingTds: sum("passingTds") / count,
    interceptions: sum("interceptions") / count,
    rushingYards: sum("rushingYards") / count,
    rushingTds: sum("rushingTds") / count,
    carries: sum("carries") / count,
    receivingYards: sum("receivingYards") / count,
    receivingTds: sum("receivingTds") / count,
    receptions: sum("receptions") / count,
    fantasyPoints: sum("fantasyPoints") / count,
  };
}
