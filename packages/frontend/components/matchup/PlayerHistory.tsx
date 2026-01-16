"use client";

import { useState } from "react";
import { SectionLabel } from "@/components/ui/section-label";
import { usePlayerHistory, calculateSeasonAverages } from "@/hooks/usePlayerHistory";
import { cn } from "@/lib/utils";

interface PlayerHistoryProps {
  playerId: string | null;
  playerName: string;
  position: "QB" | "RB" | "WR" | "TE";
}

function StatCell({ value, label, isNegative = false }: { value: number | undefined; label: string; isNegative?: boolean }) {
  if (value === undefined || value === null) return null;
  return (
    <div className="text-center">
      <div className={cn(
        "text-lg font-semibold tabular-nums",
        isNegative ? "text-red-600" : ""
      )}>
        {value.toFixed(1)}
      </div>
      <div className="text-xs text-muted-foreground uppercase">{label}</div>
    </div>
  );
}

interface GameRowProps {
  game: {
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
  };
  position: string;
}

function GameRow({ game, position }: GameRowProps) {
  return (
    <div className="grid grid-cols-[80px_1fr] gap-4 py-2 border-b border-border/50 last:border-0">
      <div className="text-sm text-muted-foreground">
        Wk {game.week}
        <span className="block text-xs">{game.opponentTeam ? `vs ${game.opponentTeam}` : ""}</span>
      </div>
      <div className="grid grid-cols-4 md:grid-cols-6 gap-2">
        {position === "QB" && (
          <>
            <StatCell value={game.passingYards} label="Pass Yds" />
            <StatCell value={game.passingTds} label="Pass TD" />
            <StatCell value={game.interceptions} label="INT" isNegative />
            <StatCell value={game.rushingYards} label="Rush Yds" />
          </>
        )}
        {position === "RB" && (
          <>
            <StatCell value={game.rushingYards} label="Rush Yds" />
            <StatCell value={game.rushingTds} label="Rush TD" />
            <StatCell value={game.carries} label="Carries" />
            <StatCell value={game.receivingYards} label="Rec Yds" />
            <StatCell value={game.receptions} label="Rec" />
          </>
        )}
        {(position === "WR" || position === "TE") && (
          <>
            <StatCell value={game.receivingYards} label="Rec Yds" />
            <StatCell value={game.receivingTds} label="Rec TD" />
            <StatCell value={game.receptions} label="Rec" />
          </>
        )}
        <StatCell value={game.fantasyPoints} label="Pts" />
      </div>
    </div>
  );
}

interface SeasonSummaryProps {
  games: {
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
  }[];
  season: number;
  position: string;
}

function SeasonSummary({ games, season, position }: SeasonSummaryProps) {
  const avg = calculateSeasonAverages(games, season);
  if (!avg) return <div className="text-muted-foreground text-sm">No data for {season}</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold">{season} Season</h4>
        <span className="text-sm text-muted-foreground">{avg.games} games</span>
      </div>

      <div className="bg-muted/30 rounded-lg p-4">
        <div className="grid grid-cols-4 md:grid-cols-6 gap-4 text-center">
          {position === "QB" && (
            <>
              <StatCell value={avg.passingYards} label="Avg Pass Yds" />
              <StatCell value={avg.passingTds} label="Avg Pass TD" />
              <StatCell value={avg.interceptions} label="Avg INT" isNegative />
              <StatCell value={avg.rushingYards} label="Avg Rush Yds" />
            </>
          )}
          {position === "RB" && (
            <>
              <StatCell value={avg.rushingYards} label="Avg Rush Yds" />
              <StatCell value={avg.rushingTds} label="Avg Rush TD" />
              <StatCell value={avg.carries} label="Avg Carries" />
              <StatCell value={avg.receivingYards} label="Avg Rec Yds" />
            </>
          )}
          {(position === "WR" || position === "TE") && (
            <>
              <StatCell value={avg.receivingYards} label="Avg Rec Yds" />
              <StatCell value={avg.receivingTds} label="Avg Rec TD" />
              <StatCell value={avg.receptions} label="Avg Rec" />
            </>
          )}
          <StatCell value={avg.fantasyPoints} label="Avg Pts" />
        </div>
      </div>

      <div className="max-h-64 overflow-y-auto">
        {games
          .filter(g => g.season === season)
          .sort((a, b) => b.week - a.week)
          .slice(0, 10)
          .map((game, i) => (
            <GameRow key={i} game={game} position={position} />
          ))}
      </div>
    </div>
  );
}

export function PlayerHistory({ playerId, playerName, position }: PlayerHistoryProps) {
  const { games, isLoading, error } = usePlayerHistory(playerId);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);

  if (!playerId) {
    return null;
  }

  // Get unique seasons from games, sorted descending
  const seasons = [...new Set(games.map(g => g.season))].sort((a, b) => b - a);

  // Set default season when data loads
  const activeSeason = selectedSeason ?? seasons[0] ?? null;

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8">
        <SectionLabel className="mb-4">RECENT PERFORMANCE</SectionLabel>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted/50 rounded w-1/4" />
          <div className="h-24 bg-muted/30 rounded" />
          <div className="h-32 bg-muted/30 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8">
        <SectionLabel className="mb-4">RECENT PERFORMANCE</SectionLabel>
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (games.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8">
        <SectionLabel className="mb-4">RECENT PERFORMANCE</SectionLabel>
        <p className="text-muted-foreground text-sm">No historical data available for {playerName}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-8">
      <SectionLabel className="mb-6">RECENT PERFORMANCE</SectionLabel>

      {/* Custom Tabs using Tailwind */}
      <div className="mb-6">
        <div className="inline-flex bg-muted/30 rounded-lg p-1 gap-1">
          {seasons.map(season => (
            <button
              key={season}
              onClick={() => setSelectedSeason(season)}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-md transition-colors",
                activeSeason === season
                  ? "bg-white text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {season}
            </button>
          ))}
        </div>
      </div>

      {/* Season Content */}
      {activeSeason && (
        <SeasonSummary games={games} season={activeSeason} position={position} />
      )}
    </div>
  );
}
