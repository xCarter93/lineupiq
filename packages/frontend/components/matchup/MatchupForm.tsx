"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionLabel } from "@/components/ui/section-label";
import { PositionFilter } from "@/components/matchup/PositionFilter";
import { PlayerSelect, Player } from "@/components/matchup/PlayerSelect";
import { TeamSelect } from "@/components/matchup/TeamSelect";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface MatchupData {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  opponentTeam: string;
  week: number;
  season: number;
  isHome: boolean;
}

interface MatchupFormProps {
  onSubmit: (matchup: MatchupData) => void;
  isLoading?: boolean;
}

export function MatchupForm({ onSubmit, isLoading = false }: MatchupFormProps) {
  // Player selection state
  const [selectedPosition, setSelectedPosition] = useState("all");
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);

  // Matchup details state
  const [opponentTeam, setOpponentTeam] = useState<string | null>(null);
  const [week, setWeek] = useState<number>(1);
  const [season, setSeason] = useState<number>(new Date().getFullYear());
  const [isHome, setIsHome] = useState<boolean>(true);

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

  // Form is valid when player and opponent are selected
  const isFormValid = selectedPlayer !== null && opponentTeam !== null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlayer || !opponentTeam) return;

    onSubmit({
      playerId: selectedPlayer.playerId,
      playerName: selectedPlayer.name,
      position: selectedPlayer.position,
      team: selectedPlayer.team,
      opponentTeam,
      week,
      season,
      isHome,
    });
  };

  // Map position filter to correct type for PlayerSelect
  const positionFilter =
    selectedPosition === "all"
      ? undefined
      : (selectedPosition.toUpperCase() as "QB" | "RB" | "WR" | "TE");

  return (
    <form onSubmit={handleSubmit} aria-busy={isLoading}>
      <fieldset disabled={isLoading} className="contents">
      <div className="bg-white rounded-xl shadow-sm p-8">
        {/* Section 1: Player Selection */}
        <div className="space-y-6">
          <SectionLabel>SELECT PLAYER</SectionLabel>

          {/* Position Filter */}
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">
              Position
            </label>
            <PositionFilter
              selected={selectedPosition}
              onSelect={handlePositionChange}
            />
          </div>

          {/* Player Select */}
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">
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
        </div>

        {/* Divider */}
        <div className="border-t border-border/30 my-8" />

        {/* Section 2: Matchup Details */}
        <div className="space-y-6">
          <SectionLabel>MATCHUP DETAILS</SectionLabel>

          {/* Grid layout for matchup details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Opponent Team */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Opponent
              </label>
              <TeamSelect
                value={opponentTeam}
                onSelect={setOpponentTeam}
                placeholder="Select opponent..."
              />
            </div>

            {/* Week */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Week
              </label>
              <Input
                type="number"
                min={1}
                max={18}
                value={week}
                onChange={(e) =>
                  setWeek(Math.max(1, Math.min(18, parseInt(e.target.value) || 1)))
                }
                className={cn(
                  "bg-white rounded-lg border-border/50 shadow-sm h-11",
                  "focus:ring-2 focus:ring-primary/20"
                )}
              />
              <p className="text-xs text-muted-foreground mt-1">
                NFL regular season week (1-18)
              </p>
            </div>

            {/* Season */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Season
              </label>
              <Input
                type="number"
                min={2019}
                max={2030}
                value={season}
                onChange={(e) =>
                  setSeason(parseInt(e.target.value) || new Date().getFullYear())
                }
                className={cn(
                  "bg-white rounded-lg border-border/50 shadow-sm h-11",
                  "focus:ring-2 focus:ring-primary/20"
                )}
              />
              <p className="text-xs text-muted-foreground mt-1">
                NFL season year
              </p>
            </div>

            {/* Home/Away Toggle */}
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">
                Game Location
              </label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={isHome ? "default" : "ghost"}
                  className={cn(
                    "rounded-full transition-all flex-1",
                    !isHome && "hover:bg-muted"
                  )}
                  onClick={() => setIsHome(true)}
                >
                  Home
                </Button>
                <Button
                  type="button"
                  variant={!isHome ? "default" : "ghost"}
                  className={cn(
                    "rounded-full transition-all flex-1",
                    isHome && "hover:bg-muted"
                  )}
                  onClick={() => setIsHome(false)}
                >
                  Away
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Home field advantage affects predictions
              </p>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-8">
          <Button
            type="submit"
            disabled={!isFormValid || isLoading}
            className={cn(
              "bg-primary text-primary-foreground rounded-lg py-3 px-8 h-auto text-base font-semibold",
              "hover:brightness-110 transition-all",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "w-full md:w-auto"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Getting Prediction...
              </>
            ) : (
              "Get Prediction"
            )}
          </Button>
        </div>
      </div>
      </fieldset>
    </form>
  );
}
