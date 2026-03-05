"use client";

import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

// Defense points allowed scoring (bracket-based)
function getDefensePointsAllowedScore(pointsAllowed: number): number {
  if (pointsAllowed <= 0) return 10;
  if (pointsAllowed <= 6) return 7;
  if (pointsAllowed <= 13) return 4;
  if (pointsAllowed <= 20) return 1;
  if (pointsAllowed <= 27) return 0;
  if (pointsAllowed <= 34) return -1;
  return -4;
}

// Standard PPR scoring values
const SCORING_VALUES: Record<string, number> = {
  passing_yards: 0.04, // 1 point per 25 yards
  passing_tds: 4,
  interceptions: -2,
  rushing_yards: 0.1, // 1 point per 10 yards
  rushing_tds: 6,
  receiving_yards: 0.1, // 1 point per 10 yards
  receiving_tds: 6,
  receptions: 1, // PPR
  fumbles_lost: -2,
  // Kicker scoring (attempts × expected success rate × points)
  fg_att_0_39: 3, // Short FG (high success rate)
  fg_att_40_49: 4, // Medium FG
  fg_att_50_plus: 5, // Long FG
  pat_att: 1, // Extra point
  fg_att: 0, // Total FG attempts (not scored directly, but shown)
  // Defense scoring
  points_allowed: 0, // Shown but scored via bracket
  def_sacks: 1,
  def_interceptions: 2,
  def_fumbles: 2,
  total_def_tds: 6,
};

// Display names for stats
const STAT_DISPLAY_NAMES: Record<string, string> = {
  passing_yards: "Passing Yards",
  passing_tds: "Passing TDs",
  interceptions: "Interceptions",
  rushing_yards: "Rushing Yards",
  rushing_tds: "Rushing TDs",
  receiving_yards: "Receiving Yards",
  receiving_tds: "Receiving TDs",
  receptions: "Receptions",
  fumbles_lost: "Fumbles Lost",
  // Kicker stats
  fg_att: "FG Attempts",
  fg_att_0_39: "FG 0-39 yds",
  fg_att_40_49: "FG 40-49 yds",
  fg_att_50_plus: "FG 50+ yds",
  pat_att: "PAT Attempts",
  // Defense stats
  points_allowed: "Points Allowed",
  def_sacks: "Sacks",
  def_interceptions: "Interceptions",
  def_fumbles: "Fumble Recoveries",
  total_def_tds: "Defensive TDs",
};

// Order of stats for display (most impactful first)
const STAT_ORDER = [
  "passing_yards",
  "passing_tds",
  "rushing_yards",
  "rushing_tds",
  "receiving_yards",
  "receiving_tds",
  "receptions",
  "interceptions",
  "fumbles_lost",
  // Kicker stats
  "fg_att_50_plus",
  "fg_att_40_49",
  "fg_att_0_39",
  "pat_att",
  "fg_att",
  // Defense stats
  "total_def_tds",
  "def_interceptions",
  "def_fumbles",
  "def_sacks",
  "points_allowed",
];

interface StatPrediction {
  week: number;
  predicted: number;
  actual?: number;
}

interface ProjectedPointsBreakdownProps {
  /** Data grouped by stat target */
  groupedData: Record<string, StatPrediction[]>;
  /** Week to show breakdown for (defaults to first week in data) */
  week?: number;
  /** Position for context-aware display */
  position?: string;
}

interface PointContribution {
  stat: string;
  displayName: string;
  predictedValue: number;
  points: number;
  perUnit: number;
  isNegative: boolean;
}

export function ProjectedPointsBreakdown({
  groupedData,
  week,
  position,
}: ProjectedPointsBreakdownProps) {
  // Calculate point contributions for each stat
  const { contributions, totalPoints, targetWeek } = useMemo(() => {
    // Find the target week (use provided week or first available)
    const allWeeks = new Set<number>();
    Object.values(groupedData).forEach((data) => {
      data.forEach((d) => allWeeks.add(d.week));
    });
    const sortedWeeks = Array.from(allWeeks).sort((a, b) => a - b);
    const targetWeek = week ?? sortedWeeks[0] ?? 1;

    // Calculate contributions
    const contributions: PointContribution[] = [];
    let totalPoints = 0;

    // Order stats based on position-relevance
    const orderedStats = STAT_ORDER.filter((stat) => {
      // Filter out irrelevant stats based on position
      if (position === "QB") {
        return ["passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds", "fumbles_lost"].includes(stat);
      }
      if (position === "RB") {
        return ["rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds", "receptions", "fumbles_lost"].includes(stat);
      }
      if (position === "WR" || position === "TE") {
        return ["receiving_yards", "receiving_tds", "receptions", "fumbles_lost"].includes(stat);
      }
      if (position === "K") {
        return ["fg_att_0_39", "fg_att_40_49", "fg_att_50_plus", "pat_att"].includes(stat);
      }
      if (position === "DEF") {
        return ["points_allowed", "def_sacks", "def_interceptions", "def_fumbles", "total_def_tds"].includes(stat);
      }
      return true;
    });

    orderedStats.forEach((stat) => {
      const data = groupedData[stat];
      if (!data) return;

      const weekData = data.find((d) => d.week === targetWeek);
      if (!weekData) return;

      // Special handling for defense points allowed (bracket-based scoring)
      let points: number;
      let perUnit: number;
      if (stat === "points_allowed") {
        points = getDefensePointsAllowedScore(weekData.predicted);
        perUnit = 0; // Show 0 for "per unit" since it's bracket-based
      } else {
        perUnit = SCORING_VALUES[stat] || 0;
        points = weekData.predicted * perUnit;
      }
      totalPoints += points;

      contributions.push({
        stat,
        displayName: STAT_DISPLAY_NAMES[stat] || stat,
        predictedValue: weekData.predicted,
        points,
        perUnit,
        isNegative: perUnit < 0 || (stat === "points_allowed" && points < 0),
      });
    });

    // Sort by absolute points contribution (highest first)
    contributions.sort((a, b) => Math.abs(b.points) - Math.abs(a.points));

    return { contributions, totalPoints, targetWeek };
  }, [groupedData, week, position]);

  // Calculate max positive contribution for progress bar scaling
  const maxContribution = useMemo(() => {
    const positiveContributions = contributions.filter((c) => c.points > 0);
    return positiveContributions.length > 0
      ? Math.max(...positiveContributions.map((c) => c.points))
      : 1;
  }, [contributions]);

  if (contributions.length === 0) {
    return (
      <div className="text-center py-4 text-muted-foreground">
        <p className="text-sm">No projection data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Total Points Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Week {targetWeek} Projection</span>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-primary">
            {totalPoints.toFixed(1)}
          </span>
          <span className="text-sm text-muted-foreground">pts</span>
        </div>
      </div>

      {/* Breakdown List */}
      <div className="space-y-3">
        {contributions.map((contrib) => (
          <div key={contrib.stat} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="font-medium">{contrib.displayName}</span>
                <span className="text-muted-foreground">
                  {contrib.predictedValue.toFixed(1)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {contrib.stat === "points_allowed"
                    ? "bracket"
                    : contrib.perUnit > 0 ? "+" : ""}
                  {contrib.stat !== "points_allowed" && (
                    contrib.perUnit === 0.04
                      ? "1pt/25"
                      : contrib.perUnit === 0.1
                      ? "1pt/10"
                      : `${contrib.perUnit}pt`
                  )}
                </span>
                <Badge
                  variant="outline"
                  className={
                    contrib.points > 0
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : contrib.points < 0
                      ? "bg-red-50 text-red-700 border-red-200"
                      : ""
                  }
                >
                  {contrib.points > 0 ? "+" : ""}
                  {contrib.points.toFixed(1)}
                </Badge>
              </div>
            </div>
            {/* Progress bar for positive contributions */}
            {contrib.points > 0 && (
              <Progress
                value={(contrib.points / maxContribution) * 100}
                className="h-1.5"
              />
            )}
          </div>
        ))}
      </div>

      {/* Scoring Format Note */}
      <div className="text-xs text-muted-foreground text-center pt-2 border-t">
        {position === "K" ? (
          "Kicker: 3pt FG 0-39 | 4pt FG 40-49 | 5pt FG 50+ | 1pt PAT"
        ) : position === "DEF" ? (
          "Defense: 1pt/sack | 2pt INT/fumble | 6pt TD | PA brackets"
        ) : (
          "PPR Scoring: Pass 1pt/25yd, 4pt TD | Rush/Rec 1pt/10yd, 6pt TD | 1pt/rec"
        )}
      </div>
    </div>
  );
}
