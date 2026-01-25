"use client";

import { useState } from "react";
import { PlayerTable } from "./PlayerTable";
import { PlayerDetailDrawer } from "./PlayerDetailDrawer";

export function PlayerRepository() {
  const [selectedPlayer, setSelectedPlayer] = useState<{
    playerId: string;
    playerName: string;
    position: string;
    team: string;
    headshotUrl?: string;
  } | null>(null);

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
      {/* Player Data Table */}
      <PlayerTable onPlayerClick={handlePlayerClick} />

      {/* Player Detail Drawer */}
      {selectedPlayer && (
        <PlayerDetailDrawer
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
