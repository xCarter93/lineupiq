"use client";

import { useState, useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { PositionTabs } from "./PositionTabs";
import { PlayerCard } from "./PlayerCard";
import { PlayerDrawer } from "./PlayerDrawer";
import { Input } from "@/components/ui/input";

export function PlayerRepository() {
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlayer, setSelectedPlayer] = useState<{
    playerId: string;
    playerName: string;
    position: string;
    team: string;
    headshotUrl?: string;
  } | null>(null);

  // Fetch all players from Convex
  const allPlayers = useQuery(api.players.list) ?? [];

  // Filter by position and search
  const filteredPlayers = useMemo(() => {
    let filtered = allPlayers;

    // Position filter
    if (selectedPosition) {
      filtered = filtered.filter((p) => p.position === selectedPosition);
    }

    // Search filter (name or team)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.team?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [allPlayers, selectedPosition, searchQuery]);

  // Count players per position
  const playerCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    allPlayers.forEach((p) => {
      counts[p.position] = (counts[p.position] || 0) + 1;
    });
    return counts;
  }, [allPlayers]);

  const handlePlayerClick = (player: {
    playerId: string;
    playerName: string;
    position: string;
    team: string;
    headshotUrl?: string;
  }) => {
    setSelectedPlayer({
      playerId: player.playerId,
      playerName: player.playerName,
      position: player.position,
      team: player.team || "N/A",
      headshotUrl: player.headshotUrl,
    });
  };

  return (
    <div className="space-y-6">
      {/* Position Tabs */}
      <PositionTabs
        selectedPosition={selectedPosition}
        onPositionSelect={setSelectedPosition}
        playerCounts={playerCounts}
      />

      {/* Search Bar */}
      <div className="max-w-md">
        <Input
          type="text"
          placeholder="Search players by name or team..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full"
        />
      </div>

      {/* Player Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredPlayers.length === 0 ? (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            No players found matching your criteria.
          </div>
        ) : (
          filteredPlayers.map((player) => (
            <PlayerCard
              key={player.playerId}
              playerId={player.playerId}
              playerName={player.name}
              position={player.position}
              team={player.team || "N/A"}
              headshotUrl={player.headshotUrl}
              onClick={() => handlePlayerClick({
                playerId: player.playerId,
                playerName: player.name,
                position: player.position,
                team: player.team || "N/A",
                headshotUrl: player.headshotUrl,
              })}
            />
          ))
        )}
      </div>

      {/* Player Drawer */}
      {selectedPlayer && (
        <PlayerDrawer
          isOpen={!!selectedPlayer}
          onClose={() => setSelectedPlayer(null)}
          playerId={selectedPlayer.playerId}
          playerName={selectedPlayer.playerName}
          position={selectedPlayer.position}
          team={selectedPlayer.team}
          headshotUrl={selectedPlayer.headshotUrl}
        />
      )}
    </div>
  );
}
