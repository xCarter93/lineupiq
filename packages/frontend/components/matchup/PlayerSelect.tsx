"use client";

import { useState, useMemo } from "react";
import { usePlayers, usePlayersByPosition } from "@/hooks/usePlayers";
import {
  Combobox,
  ComboboxInput,
  ComboboxContent,
  ComboboxList,
  ComboboxItem,
  ComboboxEmpty,
} from "@/components/ui/combobox";
import { cn } from "@/lib/utils";

export interface Player {
  _id: string;
  playerId: string;
  name: string;
  position: string;
  team: string;
}

interface PlayerSelectProps {
  position?: "QB" | "RB" | "WR" | "TE";
  value: string | null;
  onSelect: (playerId: string, player: Player) => void;
  placeholder?: string;
}

export function PlayerSelect({
  position,
  value,
  onSelect,
  placeholder = "Search players...",
}: PlayerSelectProps) {
  const [searchQuery, setSearchQuery] = useState("");

  // Use appropriate hook based on whether position filter is applied
  const { players: allPlayers, isLoading: allLoading } = usePlayers();
  const { players: positionPlayers, isLoading: positionLoading } = usePlayersByPosition(
    position ?? "QB"
  );

  const isLoading = position ? positionLoading : allLoading;
  const rawPlayers = position ? positionPlayers : allPlayers;

  // Filter players by search query
  const filteredPlayers = useMemo(() => {
    if (!rawPlayers) return [];
    const query = searchQuery.toLowerCase();
    return rawPlayers.filter((player) =>
      player.name.toLowerCase().includes(query)
    );
  }, [rawPlayers, searchQuery]);

  // Find selected player for display
  const selectedPlayer = useMemo(() => {
    if (!value || !rawPlayers) return null;
    return rawPlayers.find((p) => p.playerId === value) ?? null;
  }, [value, rawPlayers]);

  const handleSelect = (playerId: string | null) => {
    if (!playerId || !rawPlayers) return;
    const player = rawPlayers.find((p) => p.playerId === playerId);
    if (player) {
      onSelect(playerId, player as Player);
    }
  };

  if (isLoading) {
    return (
      <div className="h-8 w-full animate-pulse rounded-lg bg-muted/50" />
    );
  }

  return (
    <Combobox
      value={value}
      onValueChange={handleSelect}
      inputValue={searchQuery}
      onInputValueChange={(newValue) => setSearchQuery(newValue ?? "")}
    >
      <ComboboxInput
        placeholder={placeholder}
        className={cn(
          "w-full",
          "[&_input]:bg-white [&_input]:rounded-lg [&_input]:border-border/50 [&_input]:shadow-sm"
        )}
      />
      <ComboboxContent
        className={cn(
          "bg-white rounded-xl shadow-lg border-border/30"
        )}
      >
        <ComboboxList>
          {filteredPlayers.map((player) => (
            <ComboboxItem
              key={player.playerId}
              value={player.playerId}
              className={cn(
                "hover:bg-muted/50",
                value === player.playerId && "bg-primary/10 text-primary"
              )}
            >
              <span>{player.name}</span>
              <span className="text-muted-foreground ml-1">
                {"\u00B7"} {player.team}
              </span>
            </ComboboxItem>
          ))}
        </ComboboxList>
        <ComboboxEmpty>No players found</ComboboxEmpty>
      </ComboboxContent>
    </Combobox>
  );
}
