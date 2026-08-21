"use client";

import { useState, useMemo } from "react";
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
import { useSimulation } from "@/hooks/useSimulation";
import { useSimulationPredictions } from "@/hooks/useSimulationPredictions";
import { useGameInfo } from "@/hooks/useGameInfo";
import { usePlayerWeekProjection } from "@/hooks/usePredictions";
import { useActiveScoringConfig } from "@/hooks/useScoringConfigs";
import { getPointsBreakdown } from "@/lib/fantasy-points";
import { formatMatchup } from "@/lib/prediction-points";
import {
  getCurrentNFLWeek,
  getCurrentSeason,
  getLastCompletedSeason,
} from "@/lib/season";
import { PredictionSourceDot } from "@/components/ui/prediction-source";
import { ValidationChart } from "./ValidationChart";
import { ConsolidatedPredictionChart } from "./ConsolidatedPredictionChart";
import { ProjectedPointsBreakdown } from "./ProjectedPointsBreakdown";
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
  Calculator,
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
  const simulation = useSimulation();
  // Predicted-vs-actual needs a season with actuals; a live simulation supplies its own
  const validationSeason = simulation.isActive
    ? simulation.targetSeason
    : getLastCompletedSeason();

  // Predictions are cached per real season/week, independent of simulation state
  const projectionSeason = getCurrentSeason();
  const currentGameWeek = getCurrentNFLWeek(projectionSeason);

  // Fetch real game info from schedule API
  const { gameInfo } = useGameInfo(team, currentGameWeek, projectionSeason);

  // Create simulation filter for validation predictions
  const simulationFilter = useMemo(() => ({
    enabled: simulation.isActive,
    completedWeeks: simulation.completedWeeks,
  }), [simulation.isActive, simulation.completedWeeks]);

  // Get validation data (actuals vs predicted) - filtered by simulation state
  const { groupedByTarget: validationGrouped, isLoading: validationLoading } = useValidationPredictions(
    playerId,
    validationSeason,
    simulationFilter
  );

  // Get simulation predictions (predictions only, for pre-season display)
  const {
    groupedByTarget: simulationGrouped,
    isLoading: simulationLoading,
  } = useSimulationPredictions(playerId, position);

  // This week's cached prediction, rolled into fantasy points
  const {
    projection,
    scoringName,
    isLoading: projectionLoading,
  } = usePlayerWeekProjection(playerId, projectionSeason, currentGameWeek);
  const { scoring } = useActiveScoringConfig();

  // Determine which data to use for charts
  // During simulation mode, always use simulation predictions (which now include actuals for completed weeks)
  // Outside of simulation mode, use validation data from Convex
  const useSimulationData = simulation.isActive;
  const chartData = useSimulationData ? simulationGrouped : validationGrouped;
  const isLoading = useSimulationData ? simulationLoading : validationLoading;

  // Get game context from schedule API data
  const gameContext = useMemo(() => {
    if (gameInfo) {
      // Format game time from weekday and gametime
      const dayAbbrev = gameInfo.weekday?.substring(0, 3) || "TBD";
      const formattedTime = gameInfo.gametime || "TBD";
      const gameTime = formattedTime !== "TBD" ? `${dayAbbrev} ${formattedTime}` : "TBD";

      // Determine weather condition based on roof type
      let weatherCondition = "Clear";
      if (gameInfo.roof === "dome" || gameInfo.roof === "closed") {
        weatherCondition = "Dome";
      } else if (gameInfo.temp === null) {
        weatherCondition = "TBD";
      }

      return {
        opponent: `${gameInfo.is_home ? "vs." : "@"} ${gameInfo.opponent}`,
        gameTime,
        location: gameInfo.is_home ? "Home" : "Away",
        stadium: gameInfo.stadium || "TBD",
        weather: {
          temp: gameInfo.temp,
          wind: gameInfo.wind,
          condition: weatherCondition,
          roof: gameInfo.roof,
        },
      };
    }
    // Fallback when the schedule API is unavailable: the prediction row still
    // carries the matchup it was generated against.
    const matchup = projection ? formatMatchup(projection) : null;
    return {
      opponent: matchup ?? "TBD",
      gameTime: "TBD",
      location: projection?.isHome === undefined
        ? "TBD"
        : projection.isHome
          ? "Home"
          : "Away",
      stadium: "TBD",
      weather: { temp: null as number | null, wind: null as number | null, condition: "TBD", roof: null as string | null },
    };
  }, [gameInfo, projection]);

  // Vegas lines from schedule API
  const vegasLines = useMemo(() => {
    if (gameInfo) {
      return {
        spread: gameInfo.spread_line,
        overUnder: gameInfo.total_line,
        impliedTotal: gameInfo.team_implied_total,
        oppDefenseRank: null, // Would need separate API for this
      };
    }
    return {
      spread: null,
      overUnder: null,
      impliedTotal: null,
      oppDefenseRank: null,
    };
  }, [gameInfo]);

  const pointsBreakdown = useMemo(
    () =>
      projection
        ? getPointsBreakdown(projection.position, projection.stats, scoring)
        : null,
    [projection, scoring]
  );

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
                  <div className="flex items-baseline gap-1.5">
                    {projection ? (
                      <>
                        <PredictionSourceDot
                          mix={projection.sourceMix}
                          modelCount={projection.modelCount}
                          baselineCount={projection.baselineCount}
                        />
                        <span className="text-2xl font-bold text-primary">
                          {projection.points.toFixed(1)}
                        </span>
                        <span className="text-sm text-muted-foreground">pts</span>
                      </>
                    ) : (
                      <span
                        className={`text-2xl font-bold text-muted-foreground${projectionLoading ? " animate-pulse" : ""}`}
                        title={projectionLoading ? "Loading projection" : `No prediction yet for Week ${currentGameWeek}`}
                      >
                        &mdash;
                      </span>
                    )}
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
                <p className="font-medium">{gameContext.opponent}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Game Time</p>
                <p className="font-medium flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {gameContext.gameTime}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Location</p>
                <p className="font-medium">{gameContext.location}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Weather</p>
                <p className="font-medium flex items-center gap-1">
                  {gameContext.weather.temp !== null ? (
                    <>
                      <Cloud className="h-3.5 w-3.5" />
                      {gameContext.weather.temp}°F
                      <Wind className="h-3.5 w-3.5 ml-1" />
                      {gameContext.weather.wind} mph
                    </>
                  ) : (
                    <span className="text-muted-foreground">TBD</span>
                  )}
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
                  {vegasLines.spread !== null ? (
                    <>
                      {vegasLines.spread > 0 ? "+" : ""}
                      {vegasLines.spread}
                    </>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">O/U</p>
                <p className="font-medium">
                  {vegasLines.overUnder !== null ? (
                    vegasLines.overUnder
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Implied Total</p>
                <p className="font-medium">
                  {vegasLines.impliedTotal !== null ? (
                    vegasLines.impliedTotal
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Stadium</p>
                <p className="font-medium text-sm">
                  {gameContext.stadium !== "TBD" ? (
                    gameContext.stadium
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </p>
              </div>
            </div>
          </CollapsibleSection>

          {/* Projected Points Breakdown */}
          <CollapsibleSection
            title={`Week ${currentGameWeek} Points Breakdown`}
            icon={<Calculator className="h-4 w-4 text-muted-foreground" />}
            defaultOpen={true}
          >
            {projectionLoading ? (
              <div className="h-48 rounded-lg bg-muted animate-pulse" />
            ) : projection && pointsBreakdown ? (
              <ProjectedPointsBreakdown
                breakdown={pointsBreakdown}
                scoredRows={projection.scoredRows}
                week={currentGameWeek}
                scoringName={scoringName}
              />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calculator className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  No prediction yet for Week {currentGameWeek}
                </p>
              </div>
            )}
          </CollapsibleSection>

          {/* Prediction Chart (Consolidated) */}
          <CollapsibleSection
            title={simulation.isActive && simulation.completedWeeks > 0
              ? `Prediction Accuracy (Weeks 1-${simulation.completedWeeks})`
              : simulation.isActive
              ? "Season Predictions"
              : "Prediction Trends"}
            icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
            defaultOpen={true}
          >
            {isLoading ? (
              <div className="h-64 rounded-lg bg-muted animate-pulse" />
            ) : chartData && Object.keys(chartData).length > 0 ? (
              <ConsolidatedPredictionChart
                groupedData={chartData}
                showActuals={!simulation.isActive || simulation.completedWeeks > 0}
                syncId="playerDetail"
              />
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
                simulationFilter={simulation.isActive ? {
                  enabled: true,
                  targetSeason: simulation.targetSeason,
                  completedWeeks: simulation.completedWeeks,
                } : undefined}
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
