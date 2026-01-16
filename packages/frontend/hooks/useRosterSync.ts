"use client";

import { useState, useCallback } from "react";
import { useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { fetchRoster, fetchPlayerHistory } from "@/lib/roster-api";

interface SyncStatus {
  isLoading: boolean;
  progress: number; // 0-100
  message: string;
  error: string | null;
}

interface SyncResult {
  playersImported: number;
  historyImported: number;
  errors: string[];
}

export function useRosterSync() {
  const [status, setStatus] = useState<SyncStatus>({
    isLoading: false,
    progress: 0,
    message: "",
    error: null,
  });

  const bulkUpsertPlayers = useMutation(api.players.bulkUpsert);
  const bulkUpsertHistory = useMutation(api.playerHistory.bulkUpsert);

  /**
   * Sync full roster from API to Convex.
   * Processes in batches of 100 to avoid Convex limits.
   */
  const syncRoster = useCallback(async (season?: number): Promise<SyncResult> => {
    setStatus({ isLoading: true, progress: 0, message: "Fetching roster...", error: null });

    try {
      const { players } = await fetchRoster(season);
      setStatus(s => ({ ...s, progress: 10, message: `Fetched ${players.length} players` }));

      const errors: string[] = [];
      const batchSize = 100;
      let imported = 0;

      for (let i = 0; i < players.length; i += batchSize) {
        const batch = players.slice(i, i + batchSize);
        const convexPlayers = batch.map(p => ({
          playerId: p.player_id,
          name: p.name,
          position: p.position,
          team: p.team,
          jerseyNumber: p.jersey_number ?? undefined,
          height: p.height?.toString() ?? undefined,
          weight: p.weight ?? undefined,
          college: p.college ?? undefined,
          yearsExp: p.years_exp ?? undefined,
          headshotUrl: p.headshot_url ?? undefined,
        }));

        try {
          await bulkUpsertPlayers({ players: convexPlayers });
          imported += batch.length;
        } catch (e) {
          errors.push(`Batch ${i / batchSize}: ${e}`);
        }

        const progress = 10 + Math.round((i / players.length) * 90);
        setStatus(s => ({
          ...s,
          progress,
          message: `Imported ${imported}/${players.length} players...`,
        }));
      }

      setStatus({ isLoading: false, progress: 100, message: "Roster sync complete", error: null });
      return { playersImported: imported, historyImported: 0, errors };
    } catch (e) {
      const error = e instanceof Error ? e.message : "Unknown error";
      setStatus({ isLoading: false, progress: 0, message: "", error });
      throw e;
    }
  }, [bulkUpsertPlayers]);

  /**
   * Sync history for a single player.
   */
  const syncPlayerHistory = useCallback(async (
    playerId: string,
    seasons: number = 3
  ): Promise<number> => {
    setStatus({ isLoading: true, progress: 0, message: "Fetching history...", error: null });

    try {
      const { games } = await fetchPlayerHistory(playerId, seasons);
      setStatus(s => ({ ...s, progress: 50, message: `Fetched ${games.length} games` }));

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

      setStatus({ isLoading: false, progress: 100, message: "History sync complete", error: null });
      return games.length;
    } catch (e) {
      const error = e instanceof Error ? e.message : "Unknown error";
      setStatus({ isLoading: false, progress: 0, message: "", error });
      throw e;
    }
  }, [bulkUpsertHistory]);

  return { status, syncRoster, syncPlayerHistory };
}
