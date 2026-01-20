"use client";

import { useState, useMemo } from "react";
import { useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { usePlayers, usePlayersByPosition } from "@/hooks/usePlayers";
import {
  Combobox,
  ComboboxInput,
  ComboboxContent,
  ComboboxList,
  ComboboxItem,
  ComboboxEmpty,
} from "@/components/ui/combobox";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";
import { FixedSizeList } from "react-window";

// Get initials from player name (e.g., "Patrick Mahomes" -> "PM")
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// Virtualized list wrapper for ComboboxList
interface VirtualizedListProps {
  players: Player[];
  selectedValue: string | null;
  onPlayerClick: (playerId: string) => void;
}

function VirtualizedComboboxList({ players, selectedValue, onPlayerClick }: VirtualizedListProps) {
  // Item height: 48px (player item with avatar is ~48px tall)
  const ITEM_HEIGHT = 48;
  const MAX_HEIGHT = 300; // Max height for dropdown

  // Calculate visible height to avoid empty space
  const listHeight = Math.min(MAX_HEIGHT, players.length * ITEM_HEIGHT);

  // Row renderer for react-window
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const player = players[index];
    return (
      <div style={style}>
        <ComboboxItem
          key={player.playerId}
          value={player.playerId}
          className={cn(
            "hover:bg-muted/50 flex items-center gap-2",
            selectedValue === player.playerId && "bg-primary/10 text-primary"
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
        </ComboboxItem>
      </div>
    );
  };

  return (
    <FixedSizeList
      height={listHeight}
      itemCount={players.length}
      itemSize={ITEM_HEIGHT}
      width="100%"
      className="no-scrollbar"
    >
      {Row}
    </FixedSizeList>
  );
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
  const [searchQuery, setSearchQuery] = useState("");
  const [isSeeding, setIsSeeding] = useState(false);

  // Use appropriate hook based on whether position filter is applied
  const { players: allPlayers, isLoading: allLoading } = usePlayers();
  const { players: positionPlayers, isLoading: positionLoading } = usePlayersByPosition(
    position ?? "QB"
  );

  // Seed mutation
  const seedPlayers = useMutation(api.seedPlayers.seedSamplePlayers);

  const isLoading = position ? positionLoading : allLoading;
  const rawPlayers = position ? positionPlayers : allPlayers;

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
      <div className="h-11 w-full flex items-center justify-center rounded-lg border border-border/50 bg-white">
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
        {filteredPlayers.length > 0 ? (
          <VirtualizedComboboxList
            players={filteredPlayers}
            selectedValue={value}
            onPlayerClick={handleSelect}
          />
        ) : (
          <ComboboxEmpty>No players found</ComboboxEmpty>
        )}
      </ComboboxContent>
    </Combobox>
  );
}
