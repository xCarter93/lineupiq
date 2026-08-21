"use client";

import { useState, useMemo, useCallback } from "react";
import { useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { usePlayers, usePlayersByPosition } from "@/hooks/usePlayers";
import {
  Autocomplete,
  AutocompleteContent,
  AutocompleteEmpty,
  AutocompleteInput,
  AutocompleteItem,
  AutocompleteList,
} from "@/components/reui/autocomplete";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

// Cap the rendered suggestion list; the roster is ~2k players.
const MAX_SUGGESTIONS = 50;

// Get initials from player name (e.g., "Patrick Mahomes" -> "PM")
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export interface Player {
  _id: string;
  playerId: string;
  name: string;
  position: string;
  team: string;
  headshotUrl?: string;
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
  const [inputValue, setInputValue] = useState("");
  const [isSeeding, setIsSeeding] = useState(false);

  // Use appropriate hook based on whether position filter is applied
  const { players: allPlayers, isLoading: allLoading } = usePlayers();
  const { players: positionPlayers, isLoading: positionLoading } = usePlayersByPosition(
    position ?? "QB"
  );

  // Seed mutation
  const seedPlayers = useMutation(api.seedPlayers.seedSamplePlayers);

  const isLoading = position ? positionLoading : allLoading;
  const rawPlayers = useMemo(
    () => (position ? positionPlayers : allPlayers) ?? [],
    [position, positionPlayers, allPlayers]
  );

  // Check if no players exist at all
  const hasNoPlayers = !allLoading && (!allPlayers || allPlayers.length === 0);

  const handleSeedPlayers = async () => {
    setIsSeeding(true);
    try {
      await seedPlayers();
    } finally {
      setIsSeeding(false);
    }
  };

  const handleSelect = useCallback(
    (player: Player) => {
      onSelect(player.playerId, player);
    },
    [onSelect]
  );

  if (isLoading) {
    return (
      <div className="h-11 w-full flex items-center justify-center rounded-lg border border-border/50 bg-card">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading players...</span>
      </div>
    );
  }

  // Show seed button when no players exist
  if (hasNoPlayers) {
    return (
      <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg border border-dashed border-border/50">
        <div className="flex-1">
          <p className="text-sm text-muted-foreground">
            No players in database. Seed sample players to test the UI.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleSeedPlayers}
          disabled={isSeeding}
          className="shrink-0"
        >
          {isSeeding ? "Seeding..." : "Seed Players"}
        </Button>
      </div>
    );
  }

  return (
    <Autocomplete
      items={rawPlayers as Player[]}
      value={inputValue}
      onValueChange={setInputValue}
      itemToStringValue={(player: Player) => player.name}
      limit={MAX_SUGGESTIONS}
      autoHighlight
    >
      <AutocompleteInput
        placeholder={placeholder}
        size="lg"
        showClear
        className="rounded-lg border-border/50 bg-card shadow-sm"
      />
      <AutocompleteContent className="rounded-xl border-border/30 shadow-lg">
        <AutocompleteEmpty>No players found</AutocompleteEmpty>
        <AutocompleteList>
          {(player: Player) => (
            <AutocompleteItem
              key={player.playerId}
              value={player}
              onClick={() => handleSelect(player)}
              className={cn(
                "flex items-center gap-2",
                value === player.playerId && "bg-primary/10 text-primary"
              )}
            >
              <Avatar
                src={player.headshotUrl}
                alt={player.name}
                fallback={getInitials(player.name)}
                size="sm"
              />
              <span>{player.name}</span>
              <span className="text-muted-foreground ml-auto text-xs px-2 py-0.5 bg-muted/50 rounded">
                {player.team}
              </span>
            </AutocompleteItem>
          )}
        </AutocompleteList>
      </AutocompleteContent>
    </Autocomplete>
  );
}
