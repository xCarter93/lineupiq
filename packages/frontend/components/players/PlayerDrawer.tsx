"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { SectionLabel } from "@/components/ui/section-label";
import { useValidationPredictions } from "@/hooks/useValidationPredictions";
import { ValidationChart } from "./ValidationChart";

// Lazy load PlayerHistory from existing component
const PlayerHistory = dynamic(
  () => import("@/components/matchup/PlayerHistory").then((mod) => ({ default: mod.PlayerHistory })),
  {
    loading: () => <div className="h-48 rounded-lg bg-muted animate-pulse" />,
    ssr: false,
  }
);

interface PlayerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  playerId: string;
  playerName: string;
  position: string;
  team: string;
}

const TABS = ["2025 Validation", "History", "Stats"] as const;
type Tab = typeof TABS[number];

// Map stat targets to display names
const TARGET_DISPLAY_NAMES: Record<string, string> = {
  passing_yards: "Passing Yards",
  passing_tds: "Passing TDs",
  interceptions: "Interceptions",
  rushing_yards: "Rushing Yards",
  rushing_tds: "Rushing TDs",
  carries: "Carries",
  receiving_yards: "Receiving Yards",
  receiving_tds: "Receiving TDs",
  receptions: "Receptions",
  fumbles_lost: "Fumbles Lost",
  fg_made_0_39: "FG Made (0-39)",
  fg_made_40_49: "FG Made (40-49)",
  fg_made_50_plus: "FG Made (50+)",
  extra_points_made: "Extra Points",
  def_sacks: "Sacks",
  def_interceptions: "Interceptions",
  def_fumbles_recovered: "Fumbles Recovered",
  def_safeties: "Safeties",
  def_touchdowns: "Defensive TDs",
};

export function PlayerDrawer({
  isOpen,
  onClose,
  playerId,
  playerName,
  position,
  team,
}: PlayerDrawerProps) {
  const [activeTab, setActiveTab] = useState<Tab>("2025 Validation");
  const [imageError, setImageError] = useState(false);
  const { groupedByTarget, isLoading } = useValidationPredictions(playerId, 2025);

  const headshotUrl = `https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/${playerId}.png&w=150&h=110`;

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="w-full sm:w-[600px] lg:w-[800px] overflow-y-auto">
        <SheetHeader className="space-y-4 pb-6">
          {/* Player Info */}
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center overflow-hidden flex-shrink-0">
              {imageError ? (
                <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-500 font-bold text-3xl">
                  {playerName.charAt(0)}
                </div>
              ) : (
                <img
                  src={headshotUrl}
                  alt={playerName}
                  className="w-full h-full object-cover"
                  loading="lazy"
                  onError={() => setImageError(true)}
                />
              )}
            </div>
            <div className="flex-1">
              <SheetTitle className="text-2xl">{playerName}</SheetTitle>
              <SheetDescription className="text-base">
                {team} • {position}
              </SheetDescription>
            </div>
            <Badge className="text-sm px-3 py-1">{position}</Badge>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b pb-2">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`
                  px-4 py-2 text-sm font-medium rounded-t-lg transition-colors
                  ${activeTab === tab
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }
                `}
              >
                {tab}
              </button>
            ))}
          </div>
        </SheetHeader>

        {/* Tab Content */}
        <div className="py-6 space-y-6">
          {activeTab === "2025 Validation" && (
            <div className="space-y-6">
              <SectionLabel>PREDICTED VS ACTUAL (2025 SEASON)</SectionLabel>

              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-48 rounded-lg bg-muted animate-pulse" />
                  ))}
                </div>
              ) : groupedByTarget && Object.keys(groupedByTarget).length > 0 ? (
                Object.entries(groupedByTarget).map(([target, data]) => (
                  <ValidationChart
                    key={target}
                    target={target}
                    data={data}
                    targetDisplayName={TARGET_DISPLAY_NAMES[target] || target}
                  />
                ))
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  No validation data available for this player yet.
                  <br />
                  Run validation script to generate predictions.
                </div>
              )}
            </div>
          )}

          {activeTab === "History" && (
            <div>
              <SectionLabel className="mb-4">RECENT PERFORMANCE</SectionLabel>
              <PlayerHistory
                playerId={playerId}
                playerName={playerName}
                position={position as "QB" | "RB" | "WR" | "TE"}
                compact={false}
              />
            </div>
          )}

          {activeTab === "Stats" && (
            <div className="text-center py-12 text-muted-foreground">
              Player stats overview coming soon
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
