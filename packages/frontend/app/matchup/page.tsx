"use client";

import { useState } from "react";
import { SectionLabel } from "@/components/ui/section-label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { PositionFilter } from "@/components/matchup/PositionFilter";
import { PlayerSelect, Player } from "@/components/matchup/PlayerSelect";

export default function MatchupPage() {
  const [selectedPosition, setSelectedPosition] = useState("all");
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);

  const handlePositionChange = (position: string) => {
    setSelectedPosition(position);
    // Clear selected player when position changes
    setSelectedPlayer(null);
    setSelectedPlayerId(null);
  };

  const handlePlayerSelect = (playerId: string, player: Player) => {
    setSelectedPlayerId(playerId);
    setSelectedPlayer(player);
  };

  // Map position filter to correct type for PlayerSelect
  const positionFilter =
    selectedPosition === "all"
      ? undefined
      : (selectedPosition.toUpperCase() as "QB" | "RB" | "WR" | "TE");

  return (
    <div className="min-h-screen">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="mb-12">
          <SectionLabel className="mb-4 block">MATCHUP SIMULATOR</SectionLabel>
          <h1 className="text-4xl font-bold text-foreground mb-3">
            Build Your Matchup
          </h1>
          <p className="text-lg text-muted-foreground">
            Select a player and opponent to see projected stats
          </p>
        </div>

        {/* Player Selection Card */}
        <Card className="rounded-xl shadow-sm border-0 bg-card">
          <CardHeader className="pb-6">
            <CardTitle className="text-3xl font-bold">Select Player</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Position Filter */}
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Position
              </label>
              <PositionFilter
                selected={selectedPosition}
                onSelect={handlePositionChange}
              />
            </div>

            {/* Player Select */}
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Player
              </label>
              <PlayerSelect
                position={positionFilter}
                value={selectedPlayerId}
                onSelect={handlePlayerSelect}
                placeholder="Search players..."
              />
            </div>

            {/* Selected Player Display */}
            {selectedPlayer && (
              <div className="bg-muted/30 rounded-lg p-4">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-semibold text-foreground">
                      {selectedPlayer.name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {selectedPlayer.position} {"\u00B7"} {selectedPlayer.team}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
