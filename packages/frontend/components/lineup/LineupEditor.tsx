"use client";

import { useState, useMemo, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { LineupSlot } from "./LineupSlot";
import { LineupSummary } from "./LineupSummary";
import { AddPlayerSheet } from "./AddPlayerSheet";
import { Loader2, Users } from "lucide-react";

interface LineupEditorProps {
  week?: number;
  season?: number;
}

export function LineupEditor({ week = 1, season = 2025 }: LineupEditorProps) {
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

  // Calculate totals (mock values - would come from real predictions)
  const totalProjected = useMemo(() => {
    return rosteredPlayerIds.length * 15; // Mock: 15 pts per player
  }, [rosteredPlayerIds]);

  const positionBreakdown = useMemo(() => {
    if (!lineup?.slots) return {};
    const breakdown: Record<string, number> = {};
    const mockPts: Record<string, number> = {
      QB: 22.5,
      RB: 15.0,
      WR: 16.5,
      TE: 12.0,
      K: 8.5,
      DEF: 7.0,
      FLEX: 14.0,
    };
    lineup.slots.forEach((slot) => {
      if (slot.playerId) {
        const pts = mockPts[slot.position] ?? 10;
        breakdown[slot.position] = (breakdown[slot.position] ?? 0) + pts;
      }
    });
    return breakdown;
  }, [lineup]);

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
                projectedPoints={slot.playerId ? (positionBreakdown[slot.position] ?? 15) : 0}
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
          lastWeekActual={85.5}
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
          eligiblePositions={addingToSlot.eligiblePositions}
          slotPosition={addingToSlot.position}
          rosteredPlayerIds={rosteredPlayerIds}
          onSelectPlayer={handleAddPlayer}
        />
      )}
    </div>
  );
}
