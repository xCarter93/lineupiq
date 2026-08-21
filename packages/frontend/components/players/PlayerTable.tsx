"use client";

import { useState, useMemo, useCallback } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import {
  type ColumnDef,
  type SortingState,
  useTable,
} from "@tanstack/react-table";
import {
  DataGrid,
  DataGridContainer,
  dataGridFeatures,
  type DataGridFeatures,
} from "@/components/reui/data-grid/data-grid";
import { DataGridColumnHeader } from "@/components/reui/data-grid/data-grid-column-header";
import { DataGridScrollArea } from "@/components/reui/data-grid/data-grid-scroll-area";
import { DataGridTableVirtual } from "@/components/reui/data-grid/data-grid-table-virtual";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { PositionTabs } from "./PositionTabs";
import { PlayerTableFilters } from "./PlayerTableFilters";
import { Plus, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useSimulation } from "@/hooks/useSimulation";
import { usePlayerTablePredictions } from "@/hooks/usePlayerTablePredictions";

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
    return <TrendingUp className="h-4 w-4 text-success" />;
  }
  if (trend === "down") {
    return <TrendingDown className="h-4 w-4 text-destructive" />;
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

const NUMERIC_COLUMN_META = {
  headerClassName: "text-right *:justify-end",
  cellClassName: "text-right",
} as const;

export function PlayerTable({ onPlayerClick, onAddToLineup }: PlayerTableProps) {
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([
    { id: "thisWeekProj", desc: true },
  ]);

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

  // Filter players (sorting is owned by the grid)
  const filteredPlayers = useMemo(() => {
    let filtered = playersWithStats;

    if (selectedPosition) {
      filtered = filtered.filter((p) => p.position === selectedPosition);
    }

    if (selectedTeam) {
      filtered = filtered.filter((p) => p.team === selectedTeam);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.team.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [playersWithStats, selectedPosition, selectedTeam, searchQuery]);

  const handlePlayerClick = useCallback(
    async (player: PlayerWithStats) => {
      // Track in recent players
      await addRecentPlayer({ playerId: player.playerId });

      onPlayerClick({
        playerId: player.playerId,
        playerName: player.name,
        position: player.position,
        team: player.team,
        headshotUrl: player.headshotUrl,
      });
    },
    [addRecentPlayer, onPlayerClick]
  );

  const lastWeekHeader =
    simulation.isActive && simulation.completedWeeks > 0
      ? `Wk ${simulation.completedWeeks}`
      : "Last Wk";
  const thisWeekHeader = simulation.isActive ? `Wk ${currentWeek} Proj` : "This Wk";
  const hideLastWeek = simulation.isActive && simulation.completedWeeks === 0;

  const columns = useMemo<ColumnDef<DataGridFeatures, PlayerWithStats>[]>(() => {
    const defs: ColumnDef<DataGridFeatures, PlayerWithStats>[] = [
      {
        accessorKey: "name",
        id: "name",
        header: ({ column }) => <DataGridColumnHeader title="Player" column={column} />,
        cell: ({ row }) => (
          <div className="flex items-center gap-3">
            <Avatar
              src={row.original.headshotUrl}
              alt={row.original.name}
              fallback={row.original.name
                .split(" ")
                .map((n) => n[0])
                .join("")}
              size="sm"
            />
            <div>
              <div className="font-medium">{row.original.name}</div>
              <Badge variant="secondary" className="text-[10px] mt-0.5">
                {row.original.position}
              </Badge>
            </div>
          </div>
        ),
        size: 250,
        minSize: 180,
        meta: { autoSize: true },
      },
      {
        accessorKey: "team",
        id: "team",
        header: ({ column }) => <DataGridColumnHeader title="Team" column={column} />,
        cell: ({ row }) => <span className="text-sm">{row.original.team}</span>,
        size: 90,
      },
      {
        accessorKey: "lastWeekActual",
        id: "lastWeekActual",
        header: ({ column }) => (
          <DataGridColumnHeader title={lastWeekHeader} column={column} />
        ),
        cell: ({ row }) => {
          if (hideLastWeek || row.original.lastWeekActual <= 0) {
            return <span className="text-muted-foreground">—</span>;
          }
          return (
            <div className="space-y-0.5">
              <div className="font-medium">{row.original.lastWeekActual.toFixed(1)}</div>
              {row.original.lastWeekPred > 0 && (
                <div className="text-xs text-muted-foreground">
                  ({row.original.lastWeekPred.toFixed(1)})
                </div>
              )}
            </div>
          );
        },
        size: 110,
        meta: NUMERIC_COLUMN_META,
      },
      {
        accessorKey: "thisWeekProj",
        id: "thisWeekProj",
        header: ({ column }) => (
          <DataGridColumnHeader title={thisWeekHeader} column={column} />
        ),
        cell: ({ row }) =>
          row.original.thisWeekProj > 0 ? (
            <span className="font-semibold text-primary">
              {row.original.thisWeekProj.toFixed(1)}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
        size: 110,
        meta: NUMERIC_COLUMN_META,
      },
      {
        accessorKey: "seasonAvg",
        id: "seasonAvg",
        header: ({ column }) => <DataGridColumnHeader title="Proj Avg" column={column} />,
        cell: ({ row }) =>
          row.original.seasonAvg > 0 ? (
            <span className="text-sm">{row.original.seasonAvg.toFixed(1)}</span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
        size: 110,
        meta: NUMERIC_COLUMN_META,
      },
      {
        id: "trend",
        header: ({ column }) => <DataGridColumnHeader title="Trend" column={column} />,
        cell: ({ row }) => <TrendIcon trend={row.original.trend} />,
        size: 80,
        enableSorting: false,
        meta: {
          headerClassName: "text-center *:justify-center",
          cellClassName: "text-center [&>*]:mx-auto",
        },
      },
    ];

    if (onAddToLineup) {
      defs.push({
        id: "add",
        header: () => null,
        cell: ({ row }) => (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onAddToLineup(row.original.playerId);
            }}
          >
            <Plus className="h-3.5 w-3.5 mr-1" />
            Add
          </Button>
        ),
        size: 100,
        enableSorting: false,
      });
    }

    return defs;
  }, [lastWeekHeader, thisWeekHeader, hideLastWeek, onAddToLineup]);

  const table = useTable({
    features: dataGridFeatures,
    // The grid renders every filtered row through the virtualizer, so opt out of
    // the bundled paginated row model that would otherwise slice to 10 rows.
    manualPagination: true,
    columns,
    data: filteredPlayers,
    getRowId: (row: PlayerWithStats) => row.playerId,
    state: { sorting },
    onSortingChange: setSorting,
  });

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
      <div className="text-sm text-muted-foreground flex items-center gap-2">
        <span>{filteredPlayers.length} players</span>
        {simulation.isActive && predictionsLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">
            Loading predictions...
          </span>
        )}
        {simulation.isActive && !predictionsLoading && playerStats.size > 0 && (
          <span className="text-xs text-info">
            Week {currentWeek} projections loaded
          </span>
        )}
      </div>

      <DataGrid
        table={table}
        recordCount={filteredPlayers.length}
        isLoading={allPlayersQuery === undefined}
        onRowClick={handlePlayerClick}
        emptyMessage="No players found matching your criteria."
        tableLayout={{ headerSticky: true, columnsResizable: true }}
        tableClassNames={{
          headerSticky: "sticky top-0 z-10 bg-card",
          bodyRow: "cursor-pointer",
        }}
      >
        <DataGridContainer className="rounded-lg border bg-card">
          <DataGridScrollArea
            className="min-h-[300px] max-h-[calc(100vh-420px)]"
            orientation="vertical"
          >
            <DataGridTableVirtual estimateSize={58} />
          </DataGridScrollArea>
        </DataGridContainer>
      </DataGrid>
    </div>
  );
}
