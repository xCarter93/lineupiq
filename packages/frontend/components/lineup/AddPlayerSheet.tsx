"use client";

import { useState, useMemo, useCallback } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import {
  type ColumnDef,
  type SortingState,
  useTable,
} from "@tanstack/react-table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import {
  DataGrid,
  DataGridContainer,
  dataGridFeatures,
  type DataGridFeatures,
} from "@/components/reui/data-grid/data-grid";
import { DataGridColumnHeader } from "@/components/reui/data-grid/data-grid-column-header";
import { DataGridTable } from "@/components/reui/data-grid/data-grid-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { PredictionSourceDot } from "@/components/ui/prediction-source";
import { Search, Plus, Check } from "lucide-react";
import { useWeekProjections } from "@/hooks/usePredictions";
import type { SourceMix } from "@/lib/prediction-points";

interface AddPlayerSheetProps {
  isOpen: boolean;
  onClose: () => void;
  eligiblePositions: string[];
  slotPosition: string;
  rosteredPlayerIds: string[];
  week: number;
  season: number;
  onSelectPlayer: (playerId: string) => void;
}

interface PlayerWithProjection {
  playerId: string;
  name: string;
  position: string;
  team: string | undefined;
  headshotUrl: string | undefined;
  projected: number | null;
  sourceMix: SourceMix | null;
  modelCount: number;
  baselineCount: number;
  isRostered: boolean;
  initials: string;
}

export function AddPlayerSheet({
  isOpen,
  onClose,
  eligiblePositions,
  slotPosition,
  rosteredPlayerIds,
  week,
  season,
  onSelectPlayer,
}: AddPlayerSheetProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sorting, setSorting] = useState<SortingState>([
    { id: "projected", desc: true },
  ]);

  const allPlayersQuery = useQuery(api.players.list);
  const allPlayers = useMemo(() => allPlayersQuery ?? [], [allPlayersQuery]);
  const { projections } = useWeekProjections(season, week);

  // Filter to eligible positions and add projection data
  const eligiblePlayers: PlayerWithProjection[] = useMemo(() => {
    let filtered = allPlayers.filter((p) =>
      eligiblePositions.includes(p.position)
    );

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.team?.toLowerCase().includes(query)
      );
    }

    return filtered.map((player) => {
      const projection = projections.get(player.playerId);

      return {
        playerId: player.playerId,
        name: player.name,
        position: player.position,
        team: player.team,
        headshotUrl: player.headshotUrl,
        projected: projection?.points ?? null,
        sourceMix: projection?.sourceMix ?? null,
        modelCount: projection?.modelCount ?? 0,
        baselineCount: projection?.baselineCount ?? 0,
        isRostered: rosteredPlayerIds.includes(player.playerId),
        initials: player.name.split(" ").map((n) => n[0]).join(""),
      };
    });
  }, [allPlayers, eligiblePositions, searchQuery, rosteredPlayerIds, projections]);

  const handleSelect = useCallback(
    (playerId: string) => {
      onSelectPlayer(playerId);
      onClose();
      setSearchQuery("");
    },
    [onSelectPlayer, onClose]
  );

  const columns = useMemo<ColumnDef<DataGridFeatures, PlayerWithProjection>[]>(
    () => [
      {
        accessorKey: "name",
        id: "name",
        header: ({ column }) => (
          <DataGridColumnHeader title="Player" column={column} />
        ),
        cell: ({ row }) => (
          <div className="flex items-center gap-3">
            <Avatar
              src={row.original.headshotUrl}
              alt={row.original.name}
              fallback={row.original.initials}
              size="sm"
            />
            <div>
              <div className="font-medium">{row.original.name}</div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Badge variant="secondary" className="text-[10px] px-1">
                  {row.original.position}
                </Badge>
                <span>{row.original.team}</span>
              </div>
            </div>
          </div>
        ),
        minSize: 180,
        meta: { autoSize: true },
      },
      {
        // Players without a prediction sort to the bottom of a descending sort
        // rather than clumping at the top as nulls would.
        accessorFn: (row: PlayerWithProjection) =>
          row.projected ?? Number.NEGATIVE_INFINITY,
        id: "projected",
        header: ({ column }) => (
          <DataGridColumnHeader title="Proj" column={column} />
        ),
        cell: ({ row }) =>
          row.original.projected !== null && row.original.sourceMix ? (
            <span className="inline-flex items-center justify-end gap-1.5">
              <PredictionSourceDot
                mix={row.original.sourceMix}
                modelCount={row.original.modelCount}
                baselineCount={row.original.baselineCount}
              />
              <span className="font-medium">
                {row.original.projected.toFixed(1)}
              </span>
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
        size: 100,
        meta: {
          headerClassName: "text-right *:justify-end",
          cellClassName: "text-right",
        },
      },
      {
        id: "action",
        header: () => null,
        cell: ({ row }) =>
          row.original.isRostered ? (
            <Badge variant="secondary" className="text-xs" data-rostered="">
              <Check className="h-3 w-3 mr-1" />
              In Lineup
            </Badge>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              aria-label={`Add ${row.original.name} to lineup`}
              onClick={() => handleSelect(row.original.playerId)}
            >
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
            </Button>
          ),
        size: 90,
        enableSorting: false,
      },
    ],
    [handleSelect]
  );

  const table = useTable({
    features: dataGridFeatures,
    // Every eligible player is rendered in one list, so opt out of the bundled
    // paginated row model that would otherwise slice to 10 rows.
    manualPagination: true,
    columns,
    data: eligiblePlayers,
    getRowId: (row: PlayerWithProjection) => row.playerId,
    state: { sorting },
    onSortingChange: setSorting,
  });

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-lg overflow-y-auto"
      >
        <SheetHeader className="pb-4">
          <SheetTitle>Add Player to {slotPosition}</SheetTitle>
          <SheetDescription>
            Select from eligible {eligiblePositions.join("/")} players
          </SheetDescription>
        </SheetHeader>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search players..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Player List */}
        <DataGrid
          table={table}
          recordCount={eligiblePlayers.length}
          isLoading={allPlayersQuery === undefined}
          emptyMessage="No eligible players found"
          tableLayout={{ dense: true, width: "auto" }}
          tableClassNames={{
            bodyRow:
              "has-[[data-rostered]]:bg-muted/30 has-[[data-rostered]]:opacity-50",
          }}
        >
          <DataGridContainer className="rounded-lg border">
            <DataGridTable />
          </DataGridContainer>
        </DataGrid>
      </SheetContent>
    </Sheet>
  );
}
