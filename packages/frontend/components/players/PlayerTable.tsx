"use client";

import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import type { SortDescriptor } from "react-aria-components";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { PositionTabs } from "./PositionTabs";
import { PlayerTableFilters } from "./PlayerTableFilters";
import {
  Plus,
  TrendingUp,
  TrendingDown,
  Minus,
  Loader2,
} from "lucide-react";
import { useSimulation } from "@/hooks/useSimulation";
import { usePlayerTablePredictions } from "@/hooks/usePlayerTablePredictions";

const INITIAL_LOAD_COUNT = 50;
const LOAD_MORE_COUNT = 30;

interface PlayerTableProps {
  onPlayerClick: (player: {
    playerId: string;
    playerName: string;
    position: string;
    team: string;
    headshotUrl?: string;
  }) => void;
  onAddToLineup?: (playerId: string) => void;
}

interface PlayerWithStats {
  playerId: string;
  name: string;
  position: string;
  team: string;
  headshotUrl?: string;
  seasonAvg: number;
  thisWeekProj: number;
  lastWeekActual: number;
  lastWeekPred: number;
  trend: "up" | "down" | "flat";
}

// Trend icon component (defined outside to avoid recreating during render)
function TrendIcon({ trend }: { trend: "up" | "down" | "flat" }) {
  if (trend === "up") {
    return <TrendingUp className="h-4 w-4 text-green-600" />;
  }
  if (trend === "down") {
    return <TrendingDown className="h-4 w-4 text-red-500" />;
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

export function PlayerTable({ onPlayerClick, onAddToLineup }: PlayerTableProps) {
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>({
    column: "thisWeekProj",
    direction: "descending",
  });
  const [visibleCount, setVisibleCount] = useState(INITIAL_LOAD_COUNT);

  // Refs for infinite scroll
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Fetch players
  const allPlayersQuery = useQuery(api.players.list);
  const allPlayers = useMemo(() => allPlayersQuery ?? [], [allPlayersQuery]);

  // Track recent players
  const addRecentPlayer = useMutation(api.recentPlayers.add);

  // Simulation context
  const simulation = useSimulation();
  const { playerStats, playerStatsByName, isLoading: predictionsLoading, currentWeek } = usePlayerTablePredictions();

  // Get unique teams for filter
  const teams = useMemo(() => {
    const teamSet = new Set(allPlayers.map((p) => p.team).filter(Boolean));
    return Array.from(teamSet).sort() as string[];
  }, [allPlayers]);

  // Count players per position
  const playerCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    allPlayers.forEach((p) => {
      counts[p.position] = (counts[p.position] || 0) + 1;
    });
    return counts;
  }, [allPlayers]);

  // Enhance players with simulation data when available, otherwise mock stats
  const playersWithStats: PlayerWithStats[] = useMemo(() => {
    // In simulation mode with predictions, use real data
    if (simulation.isActive && (playerStats.size > 0 || playerStatsByName.size > 0)) {
      return allPlayers.map((player) => {
        // Try to match by player ID first, then by name
        let stats = playerStats.get(player.playerId);
        if (!stats) {
          const normalizedName = player.name.toLowerCase().trim();
          stats = playerStatsByName.get(normalizedName);
        }

        if (stats) {
          return {
            playerId: player.playerId,
            name: player.name,
            position: player.position,
            team: player.team || "N/A",
            headshotUrl: player.headshotUrl,
            seasonAvg: stats.seasonAvg ?? 0,
            thisWeekProj: stats.thisWeekProj ?? 0,
            lastWeekActual: stats.lastWeekActual ?? 0,
            lastWeekPred: stats.lastWeekPred ?? 0,
            trend: stats.trend,
          };
        }

        // Player not in predictions (maybe K or DEF without predictions)
        return {
          playerId: player.playerId,
          name: player.name,
          position: player.position,
          team: player.team || "N/A",
          headshotUrl: player.headshotUrl,
          seasonAvg: 0,
          thisWeekProj: 0,
          lastWeekActual: 0,
          lastWeekPred: 0,
          trend: "flat" as const,
        };
      });
    }

    // Fallback: mock position-based stats for non-simulation mode
    const positionStats: Record<string, { avg: number; proj: number; actual: number }> = {
      QB: { avg: 22.5, proj: 24.0, actual: 23.5 },
      RB: { avg: 14.0, proj: 15.0, actual: 13.5 },
      WR: { avg: 13.5, proj: 14.5, actual: 15.0 },
      TE: { avg: 10.5, proj: 11.0, actual: 9.5 },
      K: { avg: 8.0, proj: 8.5, actual: 7.5 },
      DEF: { avg: 7.5, proj: 8.0, actual: 6.5 },
    };

    return allPlayers.map((player, index) => {
      const stats = positionStats[player.position] ?? { avg: 12.0, proj: 12.5, actual: 11.5 };
      const variation = (index % 10) * 0.5;
      const seasonAvg = stats.avg + variation;
      const thisWeekProj = stats.proj + variation;
      const lastWeekActual = stats.actual + variation;
      const lastWeekPred = lastWeekActual * 0.95;
      const trendValue = thisWeekProj - seasonAvg;

      return {
        playerId: player.playerId,
        name: player.name,
        position: player.position,
        team: player.team || "N/A",
        headshotUrl: player.headshotUrl,
        seasonAvg,
        thisWeekProj,
        lastWeekActual,
        lastWeekPred,
        trend: trendValue > 2 ? "up" : trendValue < -2 ? "down" : "flat",
      };
    });
  }, [allPlayers, simulation.isActive, playerStats, playerStatsByName]);

  // Filter and sort players
  const filteredPlayers = useMemo(() => {
    let filtered = playersWithStats;

    // Position filter
    if (selectedPosition) {
      filtered = filtered.filter((p) => p.position === selectedPosition);
    }

    // Team filter
    if (selectedTeam) {
      filtered = filtered.filter((p) => p.team === selectedTeam);
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.team.toLowerCase().includes(query)
      );
    }

    // Sort based on sortDescriptor
    if (sortDescriptor.column) {
      filtered = [...filtered].sort((a, b) => {
        const column = sortDescriptor.column as keyof PlayerWithStats;
        const aVal = a[column];
        const bVal = b[column];

        if (typeof aVal === "string" && typeof bVal === "string") {
          return sortDescriptor.direction === "ascending"
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        }

        if (typeof aVal === "number" && typeof bVal === "number") {
          return sortDescriptor.direction === "ascending"
            ? aVal - bVal
            : bVal - aVal;
        }

        return 0;
      });
    }

    return filtered;
  }, [playersWithStats, selectedPosition, selectedTeam, searchQuery, sortDescriptor]);

  // Paginate filtered players for display
  const visiblePlayers = useMemo(() => {
    return filteredPlayers.slice(0, visibleCount);
  }, [filteredPlayers, visibleCount]);

  const hasMore = visibleCount < filteredPlayers.length;

  // Load more callback
  const loadMore = useCallback(() => {
    if (hasMore) {
      setVisibleCount((prev) => Math.min(prev + LOAD_MORE_COUNT, filteredPlayers.length));
    }
  }, [hasMore, filteredPlayers.length]);

  // Intersection observer for infinite scroll
  useEffect(() => {
    const loadMoreElement = loadMoreRef.current;
    const scrollContainer = scrollContainerRef.current;
    if (!loadMoreElement || !scrollContainer) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore) {
          loadMore();
        }
      },
      {
        root: scrollContainer,
        threshold: 0.1,
        rootMargin: "100px"
      }
    );

    observer.observe(loadMoreElement);

    return () => {
      observer.disconnect();
    };
  }, [hasMore, loadMore]);

  // Handle filter changes - reset visible count
  const handlePositionSelect = useCallback((position: string | null) => {
    setSelectedPosition(position);
    setVisibleCount(INITIAL_LOAD_COUNT);
  }, []);

  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query);
    setVisibleCount(INITIAL_LOAD_COUNT);
  }, []);

  const handleTeamChange = useCallback((team: string | null) => {
    setSelectedTeam(team);
    setVisibleCount(INITIAL_LOAD_COUNT);
  }, []);

  const handleSortChange = useCallback((descriptor: SortDescriptor) => {
    setSortDescriptor(descriptor);
    setVisibleCount(INITIAL_LOAD_COUNT);
  }, []);

  const handlePlayerClick = async (player: PlayerWithStats) => {
    // Track in recent players
    await addRecentPlayer({ playerId: player.playerId });

    onPlayerClick({
      playerId: player.playerId,
      playerName: player.name,
      position: player.position,
      team: player.team,
      headshotUrl: player.headshotUrl,
    });
  };

  return (
    <div className="space-y-4">
      {/* Position Tabs */}
      <PositionTabs
        selectedPosition={selectedPosition}
        onPositionSelect={handlePositionSelect}
        playerCounts={playerCounts}
      />

      {/* Filters */}
      <PlayerTableFilters
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        selectedTeam={selectedTeam}
        onTeamChange={handleTeamChange}
        teams={teams}
      />

      {/* Results Count */}
      <div className="text-sm text-muted-foreground flex items-center gap-2">
        <span>
          {visiblePlayers.length} of {filteredPlayers.length} players
        </span>
        {simulation.isActive && predictionsLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">
            Loading predictions...
          </span>
        )}
        {simulation.isActive && !predictionsLoading && playerStats.size > 0 && (
          <span className="text-xs text-blue-600">
            Week {currentWeek} projections loaded
          </span>
        )}
      </div>

      {/* Table with sticky header and infinite scroll */}
      <div
        ref={scrollContainerRef}
        className="rounded-lg border bg-card overflow-auto"
        style={{ maxHeight: "calc(100vh - 420px)", minHeight: "300px" }}
      >
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-card border-b">
            <tr>
              <th
                className="text-left font-medium text-muted-foreground px-4 py-2 cursor-pointer hover:bg-muted/50 w-[250px]"
                onClick={() =>
                  handleSortChange({
                    column: "name",
                    direction:
                      sortDescriptor.column === "name" &&
                      sortDescriptor.direction === "ascending"
                        ? "descending"
                        : "ascending",
                  })
                }
              >
                <span className="inline-flex items-center gap-1">
                  Player
                  {sortDescriptor.column === "name" && (
                    <span className="text-xs">
                      {sortDescriptor.direction === "ascending" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
              <th
                className="text-left font-medium text-muted-foreground px-4 py-2 cursor-pointer hover:bg-muted/50 w-[80px]"
                onClick={() =>
                  handleSortChange({
                    column: "team",
                    direction:
                      sortDescriptor.column === "team" &&
                      sortDescriptor.direction === "ascending"
                        ? "descending"
                        : "ascending",
                  })
                }
              >
                <span className="inline-flex items-center gap-1">
                  Team
                  {sortDescriptor.column === "team" && (
                    <span className="text-xs">
                      {sortDescriptor.direction === "ascending" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
              <th
                className="text-right font-medium text-muted-foreground px-4 py-2 cursor-pointer hover:bg-muted/50 w-[100px]"
                onClick={() =>
                  handleSortChange({
                    column: "lastWeekActual",
                    direction:
                      sortDescriptor.column === "lastWeekActual" &&
                      sortDescriptor.direction === "descending"
                        ? "ascending"
                        : "descending",
                  })
                }
              >
                <span className="inline-flex items-center justify-end gap-1 w-full">
                  {simulation.isActive && simulation.completedWeeks > 0
                    ? `Wk ${simulation.completedWeeks}`
                    : "Last Wk"}
                  {sortDescriptor.column === "lastWeekActual" && (
                    <span className="text-xs">
                      {sortDescriptor.direction === "ascending" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
              <th
                className="text-right font-medium text-muted-foreground px-4 py-2 cursor-pointer hover:bg-muted/50 w-[100px]"
                onClick={() =>
                  handleSortChange({
                    column: "thisWeekProj",
                    direction:
                      sortDescriptor.column === "thisWeekProj" &&
                      sortDescriptor.direction === "descending"
                        ? "ascending"
                        : "descending",
                  })
                }
              >
                <span className="inline-flex items-center justify-end gap-1 w-full">
                  {simulation.isActive ? `Wk ${currentWeek} Proj` : "This Wk"}
                  {sortDescriptor.column === "thisWeekProj" && (
                    <span className="text-xs">
                      {sortDescriptor.direction === "ascending" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
              <th
                className="text-right font-medium text-muted-foreground px-4 py-2 cursor-pointer hover:bg-muted/50 w-[100px]"
                onClick={() =>
                  handleSortChange({
                    column: "seasonAvg",
                    direction:
                      sortDescriptor.column === "seasonAvg" &&
                      sortDescriptor.direction === "descending"
                        ? "ascending"
                        : "descending",
                  })
                }
              >
                <span className="inline-flex items-center justify-end gap-1 w-full">
                  Proj Avg
                  {sortDescriptor.column === "seasonAvg" && (
                    <span className="text-xs">
                      {sortDescriptor.direction === "ascending" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
              <th className="text-center font-medium text-muted-foreground px-4 py-2 w-[60px]">
                Trend
              </th>
              {onAddToLineup && <th className="w-[100px]" />}
            </tr>
          </thead>
          <tbody>
            {visiblePlayers.length === 0 ? (
              <tr>
                <td
                  colSpan={onAddToLineup ? 7 : 6}
                  className="text-center py-12 text-muted-foreground"
                >
                  No players found matching your criteria.
                </td>
              </tr>
            ) : (
              visiblePlayers.map((player) => (
                <tr
                  key={player.playerId}
                  onClick={() => handlePlayerClick(player)}
                  className="cursor-pointer hover:bg-muted/50 border-b last:border-b-0"
                >
                  <td className="px-4 py-2 w-[250px]">
                    <div className="flex items-center gap-3">
                      <Avatar
                        src={player.headshotUrl}
                        alt={player.name}
                        fallback={player.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                        size="sm"
                      />
                      <div>
                        <div className="font-medium">{player.name}</div>
                        <Badge variant="secondary" className="text-[10px] mt-0.5">
                          {player.position}
                        </Badge>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2 w-[80px]">
                    <span className="text-sm">{player.team}</span>
                  </td>
                  <td className="px-4 py-2 w-[100px] text-right">
                    {simulation.isActive && simulation.completedWeeks === 0 ? (
                      <span className="text-muted-foreground">—</span>
                    ) : player.lastWeekActual > 0 ? (
                      <div className="space-y-0.5">
                        <div className="font-medium">
                          {player.lastWeekActual.toFixed(1)}
                        </div>
                        {player.lastWeekPred > 0 && (
                          <div className="text-xs text-muted-foreground">
                            ({player.lastWeekPred.toFixed(1)})
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 w-[100px] text-right">
                    {player.thisWeekProj > 0 ? (
                      <span className="font-semibold text-primary">
                        {player.thisWeekProj.toFixed(1)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 w-[100px] text-right">
                    {player.seasonAvg > 0 ? (
                      <span className="text-sm">{player.seasonAvg.toFixed(1)}</span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 w-[60px] text-center">
                    <TrendIcon trend={player.trend} />
                  </td>
                  {onAddToLineup && (
                    <td className="px-4 py-2 w-[100px]">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onAddToLineup(player.playerId);
                        }}
                      >
                        <Plus className="h-3.5 w-3.5 mr-1" />
                        Add
                      </Button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Load more trigger */}
        {hasMore && (
          <div
            ref={loadMoreRef}
            className="flex items-center justify-center py-4 text-muted-foreground border-t"
          >
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            <span className="text-sm">Loading more players...</span>
          </div>
        )}
      </div>
    </div>
  );
}
