/**
 * API client for roster and player history data from Python backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PlayerRoster {
  player_id: string;
  name: string;
  position: string;
  team: string;
  jersey_number: number | null;
  height: number | null;
  weight: number | null;
  college: string | null;
  years_exp: number | null;
  headshot_url: string | null;
}

export interface RosterResponse {
  season: number;
  players: PlayerRoster[];
  count: number;
}

export interface WeeklyStats {
  season: number;
  week: number;
  opponent_team: string | null;
  passing_yards: number | null;
  passing_tds: number | null;
  interceptions: number | null;
  rushing_yards: number | null;
  rushing_tds: number | null;
  carries: number | null;
  receiving_yards: number | null;
  receiving_tds: number | null;
  receptions: number | null;
  fantasy_points: number | null;
}

export interface PlayerHistoryResponse {
  player_id: string;
  player_name: string;
  position: string;
  seasons: number[];
  games: WeeklyStats[];
  total_games: number;
}

/**
 * Fetch current NFL roster for fantasy positions.
 */
export async function fetchRoster(season?: number): Promise<RosterResponse> {
  const url = new URL(`${API_BASE}/api/roster`);
  if (season) {
    url.searchParams.set("season", season.toString());
  }

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Failed to fetch roster: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch player's historical weekly stats.
 */
export async function fetchPlayerHistory(
  playerId: string,
  seasons: number = 3
): Promise<PlayerHistoryResponse> {
  const url = new URL(`${API_BASE}/api/player/${playerId}/history`);
  url.searchParams.set("seasons", seasons.toString());

  const response = await fetch(url.toString());
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Player not found: ${playerId}`);
    }
    throw new Error(`Failed to fetch player history: ${response.statusText}`);
  }

  return response.json();
}
