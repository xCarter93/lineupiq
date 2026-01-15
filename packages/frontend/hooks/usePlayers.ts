"use client";

import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";

/**
 * Hook to get all players sorted by name
 *
 * @example
 * const { players, isLoading } = usePlayers();
 */
export function usePlayers() {
  const players = useQuery(api.players.list);
  return {
    players,
    isLoading: players === undefined,
  };
}

/**
 * Hook to get players by position
 *
 * @example
 * const { players, isLoading } = usePlayersByPosition("QB");
 * const { players, isLoading } = usePlayersByPosition("WR");
 */
export function usePlayersByPosition(position: "QB" | "RB" | "WR" | "TE") {
  const players = useQuery(api.players.getByPosition, { position });
  return {
    players,
    isLoading: players === undefined,
  };
}

/**
 * Hook to get players by team
 *
 * @example
 * const { players, isLoading } = usePlayersByTeam("KC");
 * const { players, isLoading } = usePlayersByTeam("SF");
 */
export function usePlayersByTeam(team: string) {
  const players = useQuery(api.players.getByTeam, { team });
  return {
    players,
    isLoading: players === undefined,
  };
}

/**
 * Hook to search players by name
 *
 * @example
 * const { players, isLoading } = usePlayerSearch("Mahomes");
 */
export function usePlayerSearch(query: string) {
  const players = useQuery(api.players.search, { query });
  return {
    players,
    isLoading: players === undefined,
  };
}

/**
 * Hook returning mutation functions for player operations
 *
 * @example
 * const { upsert, bulkUpsert, remove } = usePlayerMutations();
 *
 * // Upsert a single player
 * await upsert({
 *   playerId: "player-123",
 *   name: "Patrick Mahomes",
 *   position: "QB",
 *   team: "KC",
 * });
 *
 * // Bulk upsert players
 * const count = await bulkUpsert({
 *   players: [
 *     { playerId: "p1", name: "Player One", position: "QB", team: "KC" },
 *     { playerId: "p2", name: "Player Two", position: "RB", team: "SF" },
 *   ],
 * });
 *
 * // Remove a player
 * await remove({ id: playerId });
 */
export function usePlayerMutations() {
  const upsert = useMutation(api.players.upsert);
  const bulkUpsert = useMutation(api.players.bulkUpsert);
  const remove = useMutation(api.players.remove);

  return {
    upsert,
    bulkUpsert,
    remove,
  };
}
