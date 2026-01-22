"use client";

import { Badge } from "@/components/ui/badge";

interface PlayerCardProps {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  onClick: () => void;
}

export function PlayerCard({ playerId, playerName, position, team, onClick }: PlayerCardProps) {
  const headshotUrl = `https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/${playerId}.png&w=96&h=70`;

  return (
    <button
      onClick={onClick}
      className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-all hover:scale-[1.02] text-left w-full"
    >
      <div className="flex items-center gap-3">
        {/* Player Headshot */}
        <div className="w-16 h-16 rounded-full overflow-hidden bg-muted flex-shrink-0">
          <img
            src={headshotUrl}
            alt={playerName}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.src = "/placeholder-player.png";
            }}
          />
        </div>

        {/* Player Info */}
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-foreground truncate">{playerName}</div>
          <div className="text-sm text-muted-foreground">{team}</div>
        </div>

        {/* Position Badge */}
        <Badge className="flex-shrink-0">{position}</Badge>
      </div>
    </button>
  );
}
