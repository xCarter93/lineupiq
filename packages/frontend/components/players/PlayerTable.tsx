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
import { PredictionSourceDot } from "@/components/ui/prediction-source";
import { PositionTabs } from "./PositionTabs";
import { PlayerTableFilters } from "./PlayerTableFilters";
import { Plus } from "lucide-react";
import { useWeekProjections } from "@/hooks/usePredictions";
import { formatMatchup, type SourceMix } from "@/lib/prediction-points";
import { getCurrentNFLWeek, getCurrentSeason } from "@/lib/season";

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

interface PlayerWithProjection {
  playerId: string;
  name: string;
  position: string;
  team: string;
  headshotUrl?: string;
  matchup: string | null;
  projectedPoints: number | null;
  sourceMix: SourceMix | null;
  modelCount: number;
  baselineCount: number;
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
    { id: "projectedPoints", desc: true },
  ]);

  const season = getCurrentSeason();
  const week = getCurrentNFLWeek(season);

  const allPlayersQuery = useQuery(api.players.list);
  const allPlayers = useMemo(() => allPlayersQuery ?? [], [allPlayersQuery]);

  const addRecentPlayer = useMutation(api.recentPlayers.add);

  const { projections, scoringName, isLoading: projectionsLoading } =
    useWeekProjections(season, week);

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

  const playersWithProjections: PlayerWithProjection[] = useMemo(
    () =>
      allPlayers.map((player) => {
        const projection = projections.get(player.playerId);

        return {
          playerId: player.playerId,
          name: player.name,
          position: player.position,
          team: player.team || "N/A",
          headshotUrl: player.headshotUrl,
          matchup: projection ? formatMatchup(projection) : null,
          projectedPoints: projection?.points ?? null,
          sourceMix: projection?.sourceMix ?? null,
          modelCount: projection?.modelCount ?? 0,
          baselineCount: projection?.baselineCount ?? 0,
        };
      }),
    [allPlayers, projections]
  );

  // Filter players (sorting is owned by the grid)
  const filteredPlayers = useMemo(() => {
    let filtered = playersWithProjections;

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
  }, [playersWithProjections, selectedPosition, selectedTeam, searchQuery]);

  const projectedCount = useMemo(
    () => filteredPlayers.filter((p) => p.projectedPoints !== null).length,
    [filteredPlayers]
  );

  const handlePlayerClick = useCallback(
    async (player: PlayerWithProjection) => {
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

  const columns = useMemo<ColumnDef<DataGridFeatures, PlayerWithProjection>[]>(() => {
    const defs: ColumnDef<DataGridFeatures, PlayerWithProjection>[] = [
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
        accessorFn: (row: PlayerWithProjection) => row.matchup ?? "",
        id: "matchup",
        header: ({ column }) => <DataGridColumnHeader title="Opp" column={column} />,
        cell: ({ row }) =>
          row.original.matchup ? (
            <span className="text-sm">{row.original.matchup}</span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
        size: 100,
      },
      {
        // Players without a prediction sort to the bottom of a descending sort
        // rather than clumping at the top as nulls would.
        accessorFn: (row: PlayerWithProjection) =>
          row.projectedPoints ?? Number.NEGATIVE_INFINITY,
        id: "projectedPoints",
        header: ({ column }) => (
          <DataGridColumnHeader title={`Wk ${week} Proj`} column={column} />
        ),
        cell: ({ row }) =>
          row.original.projectedPoints !== null && row.original.sourceMix ? (
            <span className="inline-flex items-center justify-end gap-1.5">
              <PredictionSourceDot
                mix={row.original.sourceMix}
                modelCount={row.original.modelCount}
                baselineCount={row.original.baselineCount}
              />
              <span className="font-semibold text-primary">
                {row.original.projectedPoints.toFixed(1)}
              </span>
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
        size: 120,
        meta: NUMERIC_COLUMN_META,
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
  }, [week, onAddToLineup]);

  const table = useTable({
    features: dataGridFeatures,
    // The grid renders every filtered row through the virtualizer, so opt out of
    // the bundled paginated row model that would otherwise slice to 10 rows.
    manualPagination: true,
    columns,
    data: filteredPlayers,
    getRowId: (row: PlayerWithProjection) => row.playerId,
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
        {projectionsLoading ? (
          <span className="text-xs animate-pulse">Loading projections...</span>
        ) : (
          <span className="text-xs">
            {projectedCount} projected for Week {week} · {scoringName} scoring
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
