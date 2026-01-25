"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
// import { useQuery } from "convex/react";
// import { api } from "@/convex/_generated/api";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
// import { SectionLabel } from "@/components/ui/section-label";
import { useValidationPredictions } from "@/hooks/useValidationPredictions";
import { ValidationChart } from "./ValidationChart";
import {
  Plus,
  MapPin,
  Clock,
  Cloud,
  Wind,
  TrendingUp,
  BarChart3,
  Activity,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
// import { cn } from "@/lib/utils";

// Lazy load PlayerHistory from existing component
const PlayerHistory = dynamic(
  () =>
    import("@/components/matchup/PlayerHistory").then((mod) => ({
      default: mod.PlayerHistory,
    })),
  {
    loading: () => <div className="h-48 rounded-lg bg-muted animate-pulse" />,
    ssr: false,
  }
);

interface PlayerDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  headshotUrl?: string;
  onAddToLineup?: (playerId: string) => void;
}

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

interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function CollapsibleSection({
  title,
  icon,
  defaultOpen = true,
  children,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-sm">{title}</span>
        </div>
        {isOpen ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {isOpen && <div className="p-4 bg-background">{children}</div>}
    </div>
  );
}

export function PlayerDetailDrawer({
  isOpen,
  onClose,
  playerId,
  playerName,
  position,
  team,
  headshotUrl,
  onAddToLineup,
}: PlayerDetailDrawerProps) {
  const [imageError, setImageError] = useState(false);
  const season = 2025;
  const { groupedByTarget, isLoading } = useValidationPredictions(
    playerId,
    season
  );

  // Get player features for this week (commented out - using mock data for now)
  // const features = useQuery(api.playerFeatures.getByPlayerWeek, {
  //   playerId,
  //   week: 1, // Current week - would be dynamic in production
  //   season: 2025,
  // });

  // Mock data for sections that would come from backend
  const mockGameContext = {
    opponent: "vs. DAL",
    gameTime: "Sun 1:00 PM",
    location: "Home",
    weather: { temp: 72, wind: 8, condition: "Clear" },
  };

  const mockVegas = {
    spread: -3.5,
    overUnder: 47.5,
    impliedTotal: 25.5,
    oppDefenseRank: 12,
  };

  const mockProjectedPoints = 18.5;

  const imageUrl =
    headshotUrl ||
    `https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/${playerId}.png&w=150&h=110`;

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-[48vw] lg:max-w-[45vw] xl:max-w-[45vw] overflow-y-auto p-0"
      >
        {/* Header Section */}
        <div className="sticky top-0 z-10 bg-background border-b">
          <SheetHeader className="p-6 pb-4">
            <div className="flex items-start gap-4">
              {/* Player Image */}
              <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center overflow-hidden flex-shrink-0">
                {imageError ? (
                  <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-500 font-bold text-3xl">
                    {playerName.charAt(0)}
                  </div>
                ) : (
                  <img
                    src={imageUrl}
                    alt={playerName}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    onError={() => setImageError(true)}
                  />
                )}
              </div>

              {/* Player Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <SheetTitle className="text-xl">{playerName}</SheetTitle>
                    <SheetDescription className="text-sm">
                      {team} • {position}
                    </SheetDescription>
                  </div>
                  <Badge className="text-sm px-3 py-1 shrink-0">
                    {position}
                  </Badge>
                </div>

                {/* Projected Points */}
                <div className="flex items-center gap-4 mt-3">
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold text-primary">
                      {mockProjectedPoints.toFixed(1)}
                    </span>
                    <span className="text-sm text-muted-foreground">pts</span>
                  </div>
                  {onAddToLineup && (
                    <Button
                      size="sm"
                      onClick={() => onAddToLineup(playerId)}
                      className="ml-auto"
                    >
                      <Plus className="h-3.5 w-3.5 mr-1.5" />
                      Add to Lineup
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </SheetHeader>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Game Context */}
          <CollapsibleSection
            title="Game Context"
            icon={<MapPin className="h-4 w-4 text-muted-foreground" />}
            defaultOpen={true}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Opponent</p>
                <p className="font-medium">{mockGameContext.opponent}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Game Time</p>
                <p className="font-medium flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {mockGameContext.gameTime}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Location</p>
                <p className="font-medium">{mockGameContext.location}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Weather</p>
                <p className="font-medium flex items-center gap-1">
                  <Cloud className="h-3.5 w-3.5" />
                  {mockGameContext.weather.temp}°F
                  <Wind className="h-3.5 w-3.5 ml-1" />
                  {mockGameContext.weather.wind} mph
                </p>
              </div>
            </div>
          </CollapsibleSection>

          {/* Vegas & Matchup */}
          <CollapsibleSection
            title="Vegas & Matchup"
            icon={<BarChart3 className="h-4 w-4 text-muted-foreground" />}
            defaultOpen={true}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Spread</p>
                <p className="font-medium">
                  {mockVegas.spread > 0 ? "+" : ""}
                  {mockVegas.spread}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">O/U</p>
                <p className="font-medium">{mockVegas.overUnder}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Implied Total</p>
                <p className="font-medium">{mockVegas.impliedTotal}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Opp Def Rank</p>
                <p className="font-medium">#{mockVegas.oppDefenseRank}</p>
              </div>
            </div>
          </CollapsibleSection>

          {/* Prediction Breakdown */}
          <CollapsibleSection
            title="Prediction Breakdown"
            icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
            defaultOpen={true}
          >
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-32 rounded-lg bg-muted animate-pulse"
                  />
                ))}
              </div>
            ) : groupedByTarget && Object.keys(groupedByTarget).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(groupedByTarget)
                  .slice(0, 3)
                  .map(([target, data]) => (
                    <ValidationChart
                      key={target}
                      target={target}
                      data={data}
                      targetDisplayName={TARGET_DISPLAY_NAMES[target] || target}
                      syncId="playerDetail"
                    />
                  ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No prediction data available</p>
              </div>
            )}
          </CollapsibleSection>

          {/* Historical Performance */}
          <CollapsibleSection
            title="Historical Performance"
            icon={<Activity className="h-4 w-4 text-muted-foreground" />}
            defaultOpen={false}
          >
            {["QB", "RB", "WR", "TE"].includes(position) ? (
              <PlayerHistory
                playerId={playerId}
                playerName={playerName}
                position={position as "QB" | "RB" | "WR" | "TE"}
                compact={false}
              />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  Historical data not available for {position}
                </p>
              </div>
            )}
          </CollapsibleSection>

          {/* Injury & News */}
          <CollapsibleSection
            title="Injury & News"
            icon={<AlertCircle className="h-4 w-4 text-muted-foreground" />}
            defaultOpen={false}
          >
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge
                  variant="secondary"
                  className="bg-green-100 text-green-700"
                >
                  Healthy
                </Badge>
                <span className="text-sm text-muted-foreground">
                  No injury designation
                </span>
              </div>
              <Separator />
              <div className="text-sm text-muted-foreground">
                <p>No recent news updates</p>
              </div>
            </div>
          </CollapsibleSection>
        </div>
      </SheetContent>
    </Sheet>
  );
}
