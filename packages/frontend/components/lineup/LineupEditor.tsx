"use client";

import { useState, useMemo, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { LineupSlot } from "./LineupSlot";
import { LineupSummary } from "./LineupSummary";
import { AddPlayerSheet } from "./AddPlayerSheet";
import { Loader2, Users } from "lucide-react";
import { getCurrentSeason } from "@/lib/season";
import { usePlayersWeekProjections } from "@/hooks/usePredictions";

interface LineupEditorProps {
  week?: number;
  season?: number;
}

export function LineupEditor({
  week = 1,
  season = getCurrentSeason(),
}: LineupEditorProps) {
  const [addingToSlot, setAddingToSlot] = useState<{
    index: number;
    position: string;
    eligiblePositions: string[];
  } | null>(null);

  // Get lineup settings and current lineup
  const lineupSettings = useQuery(api.lineupSettings.get);
  const lineup = useQuery(api.lineups.getByWeek, { week, season });

  // Mutations
  const initializeLineup = useMutation(api.lineups.initialize);
  const addPlayerMutation = useMutation(api.lineups.addPlayer);
  const removePlayerMutation = useMutation(api.lineups.removePlayer);

  // Initialize lineup if it doesn't exist
  useEffect(() => {
    if (lineup === null) {
      initializeLineup({ week, season });
    }
  }, [lineup, initializeLineup, week, season]);

  // Get rostered player IDs
  const rosteredPlayerIds = useMemo(() => {
    if (!lineup?.slots) return [];
    return lineup.slots
      .map((slot) => slot.playerId)
      .filter((id): id is string => !!id);
  }, [lineup]);

  const { projections, isLoading: projectionsLoading } =
    usePlayersWeekProjections(rosteredPlayerIds, season, week);

  const totalProjected = useMemo(
    () =>
      rosteredPlayerIds.reduce(
        (sum, playerId) => sum + (projections.get(playerId)?.points ?? 0),
        0
      ),
    [rosteredPlayerIds, projections]
  );

  const positionBreakdown = useMemo(() => {
    if (!lineup?.slots) return {};
    const breakdown: Record<string, number> = {};
    lineup.slots.forEach((slot) => {
      const points = slot.playerId
        ? projections.get(slot.playerId)?.points
        : undefined;
      if (points !== undefined) {
        breakdown[slot.position] = (breakdown[slot.position] ?? 0) + points;
      }
    });
    return breakdown;
  }, [lineup, projections]);

  const projectedCount = useMemo(
    () => rosteredPlayerIds.filter((id) => projections.has(id)).length,
    [rosteredPlayerIds, projections]
  );

  const handleAddPlayer = async (playerId: string) => {
    if (addingToSlot === null) return;

    await addPlayerMutation({
      week,
      season,
      slotIndex: addingToSlot.index,
      playerId,
    });

    setAddingToSlot(null);
  };

  const handleRemovePlayer = async (slotIndex: number) => {
    await removePlayerMutation({
      week,
      season,
      slotIndex,
    });
  };

  const isLoading = lineupSettings === undefined || lineup === undefined;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const slots = lineup?.slots ?? [];
  const settings = lineupSettings?.slots ?? [];

  return (
    <div className="grid lg:grid-cols-3 gap-6">
      {/* Lineup Slots */}
      <div className="lg:col-span-2 space-y-3">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Users className="h-5 w-5" />
            Week {week} Lineup
          </h2>
        </div>

        {slots.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Users className="h-12 w-12 mb-4 opacity-50" />
              <p>No lineup configured</p>
              <p className="text-sm">Visit Settings to configure your roster slots</p>
            </CardContent>
          </Card>
        ) : (
          slots.map((slot, index) => {
            const slotSettings = settings[index];
            const eligiblePositions = slotSettings?.eligiblePositions ?? [
              slot.position,
            ];

            return (
              <LineupSlot
                key={index}
                position={slot.position}
                eligiblePositions={eligiblePositions}
                playerId={slot.playerId}
                projection={
                  slot.playerId ? (projections.get(slot.playerId) ?? null) : null
                }
                onAddClick={() =>
                  setAddingToSlot({
                    index,
                    position: slot.position,
                    eligiblePositions,
                  })
                }
                onRemoveClick={() => handleRemovePlayer(index)}
              />
            );
          })
        )}
      </div>

      {/* Summary */}
      <div className="lg:col-span-1">
        <LineupSummary
          totalProjected={totalProjected}
          projectedPlayers={projectedCount}
          isLoading={projectionsLoading}
          positionBreakdown={positionBreakdown}
          filledSlots={rosteredPlayerIds.length}
          totalSlots={slots.length}
        />
      </div>

      {/* Add Player Sheet */}
      {addingToSlot && (
        <AddPlayerSheet
          isOpen={!!addingToSlot}
          onClose={() => setAddingToSlot(null)}
          week={week}
          season={season}
          eligiblePositions={addingToSlot.eligiblePositions}
          slotPosition={addingToSlot.position}
          rosteredPlayerIds={rosteredPlayerIds}
          onSelectPlayer={handleAddPlayer}
        />
      )}
    </div>
  );
}
