"use client";

import { useState, useEffect } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface GameInfo {
  season: number;
  week: number;
  team: string;
  opponent: string;
  is_home: boolean;
  gameday: string;
  weekday: string;
  gametime: string;
  stadium: string;
  roof: string;
  surface: string;
  temp: number | null;
  wind: number | null;
  spread_line: number | null;
  total_line: number | null;
  team_implied_total: number | null;
}

interface UseGameInfoResult {
  gameInfo: GameInfo | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook to fetch game information for a team in a specific week.
 */
export function useGameInfo(
  team: string | null,
  week: number,
  season: number
): UseGameInfoResult {
  const [gameInfo, setGameInfo] = useState<GameInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!team) {
      setGameInfo(null);
      return;
    }

    const fetchGameInfo = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/schedule/game/${season}/${week}/${team}`
        );

        if (!response.ok) {
          if (response.status === 404) {
            setError(`No game found for ${team} in week ${week}`);
            setGameInfo(null);
            return;
          }
          throw new Error("Failed to fetch game info");
        }

        const data: GameInfo = await response.json();
        setGameInfo(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch game info");
        setGameInfo(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchGameInfo();
  }, [team, week, season]);

  return { gameInfo, isLoading, error };
}
