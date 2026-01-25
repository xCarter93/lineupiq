"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { PositionTabs } from "./PositionTabs";
import { PlayerTableFilters } from "./PlayerTableFilters";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Plus,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

type SortField = "name" | "team" | "seasonAvg" | "thisWeekProj" | "lastWeekActual";
type SortDirection = "asc" | "desc";

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

export function PlayerTable({ onPlayerClick, onAddToLineup }: PlayerTableProps) {
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>("seasonAvg");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // Fetch players
  const allPlayers = useQuery(api.players.list) ?? [];

  // Track recent players
  const addRecentPlayer = useMutation(api.recentPlayers.add);

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

  // Enhance players with mock stats (in production, this would come from real data)
  const playersWithStats: PlayerWithStats[] = useMemo(() => {
    // Mock position-based stats (deterministic)
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
      // Add small variation based on index for visual variety (but deterministic)
      const variation = (index % 10) * 0.5;
      const seasonAvg = stats.avg + variation;
      const thisWeekProj = stats.proj + variation;
      const lastWeekActual = stats.actual + variation;
      const lastWeekPred = lastWeekActual * 0.95; // 5% off
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
  }, [allPlayers]);

  // Filter players
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

    // Sort
    filtered.sort((a, b) => {
      let aVal: string | number;
      let bVal: string | number;

      switch (sortField) {
        case "name":
          aVal = a.name;
          bVal = b.name;
          break;
        case "team":
          aVal = a.team;
          bVal = b.team;
          break;
        case "seasonAvg":
          aVal = a.seasonAvg;
          bVal = b.seasonAvg;
          break;
        case "thisWeekProj":
          aVal = a.thisWeekProj;
          bVal = b.thisWeekProj;
          break;
        case "lastWeekActual":
          aVal = a.lastWeekActual;
          bVal = b.lastWeekActual;
          break;
        default:
          return 0;
      }

      if (typeof aVal === "string") {
        return sortDirection === "asc"
          ? aVal.localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal);
      }

      return sortDirection === "asc" ? aVal - (bVal as number) : (bVal as number) - aVal;
    });

    return filtered;
  }, [playersWithStats, selectedPosition, selectedTeam, searchQuery, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

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

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3.5 w-3.5 ml-1.5 opacity-50" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="h-3.5 w-3.5 ml-1.5" />
    ) : (
      <ArrowDown className="h-3.5 w-3.5 ml-1.5" />
    );
  };

  const TrendIcon = ({ trend }: { trend: "up" | "down" | "flat" }) => {
    if (trend === "up") {
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    }
    if (trend === "down") {
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    }
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  // Note: Loading state could be shown if needed
  // const isLoading = allPlayers.length === 0 && allPlayers !== undefined;

  return (
    <div className="space-y-4">
      {/* Position Tabs */}
      <PositionTabs
        selectedPosition={selectedPosition}
        onPositionSelect={setSelectedPosition}
        playerCounts={playerCounts}
      />

      {/* Filters */}
      <PlayerTableFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedTeam={selectedTeam}
        onTeamChange={setSelectedTeam}
        teams={teams}
      />

      {/* Results Count */}
      <div className="text-sm text-muted-foreground">
        {filteredPlayers.length} players
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="w-[250px]">
                <button
                  onClick={() => handleSort("name")}
                  className="flex items-center font-medium hover:text-foreground transition-colors"
                >
                  Player
                  <SortIcon field="name" />
                </button>
              </TableHead>
              <TableHead className="w-[80px]">
                <button
                  onClick={() => handleSort("team")}
                  className="flex items-center font-medium hover:text-foreground transition-colors"
                >
                  Team
                  <SortIcon field="team" />
                </button>
              </TableHead>
              <TableHead className="w-[100px] text-right">
                <button
                  onClick={() => handleSort("lastWeekActual")}
                  className="flex items-center justify-end w-full font-medium hover:text-foreground transition-colors"
                >
                  Last Wk
                  <SortIcon field="lastWeekActual" />
                </button>
              </TableHead>
              <TableHead className="w-[100px] text-right">
                <button
                  onClick={() => handleSort("thisWeekProj")}
                  className="flex items-center justify-end w-full font-medium hover:text-foreground transition-colors"
                >
                  This Wk
                  <SortIcon field="thisWeekProj" />
                </button>
              </TableHead>
              <TableHead className="w-[100px] text-right">
                <button
                  onClick={() => handleSort("seasonAvg")}
                  className="flex items-center justify-end w-full font-medium hover:text-foreground transition-colors"
                >
                  Avg
                  <SortIcon field="seasonAvg" />
                </button>
              </TableHead>
              <TableHead className="w-[60px] text-center">Trend</TableHead>
              {onAddToLineup && <TableHead className="w-[100px]" />}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredPlayers.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={onAddToLineup ? 7 : 6}
                  className="text-center py-12 text-muted-foreground"
                >
                  No players found matching your criteria.
                </TableCell>
              </TableRow>
            ) : (
              filteredPlayers.map((player) => (
                <TableRow
                  key={player.playerId}
                  className="cursor-pointer"
                  onClick={() => handlePlayerClick(player)}
                >
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar
                        src={player.headshotUrl}
                        alt={player.name}
                        fallback={player.name.split(" ").map((n) => n[0]).join("")}
                        size="sm"
                      />
                      <div>
                        <div className="font-medium">{player.name}</div>
                        <Badge variant="secondary" className="text-[10px] mt-0.5">
                          {player.position}
                        </Badge>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{player.team}</span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="space-y-0.5">
                      <div className="font-medium">{player.lastWeekActual.toFixed(1)}</div>
                      <div className="text-xs text-muted-foreground">
                        ({player.lastWeekPred.toFixed(1)})
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="font-semibold text-primary">
                      {player.thisWeekProj.toFixed(1)}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-sm">{player.seasonAvg.toFixed(1)}</span>
                  </TableCell>
                  <TableCell className="text-center">
                    <TrendIcon trend={player.trend} />
                  </TableCell>
                  {onAddToLineup && (
                    <TableCell>
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
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
