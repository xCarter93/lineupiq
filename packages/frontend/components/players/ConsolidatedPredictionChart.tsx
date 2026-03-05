"use client";

import { useState, useMemo, useCallback } from "react";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "@/components/ui/badge";

// Stats measured in yards (use left Y-axis)
const YARD_STATS = ["passing_yards", "rushing_yards", "receiving_yards"];

// Stats measured in counts (use right Y-axis)
const COUNT_STATS = [
  "passing_tds",
  "interceptions",
  "rushing_tds",
  "carries",
  "receiving_tds",
  "receptions",
  "fumbles_lost",
  // Kicker stats
  "fg_att",
  "fg_att_0_39",
  "fg_att_40_49",
  "fg_att_50_plus",
  "pat_att",
  // Defense stats
  "points_allowed",
  "def_sacks",
  "def_interceptions",
  "def_fumbles",
  "total_def_tds",
];

// Color palette for lines
const STAT_COLORS: Record<string, string> = {
  passing_yards: "#3b82f6", // blue
  passing_tds: "#8b5cf6", // violet
  interceptions: "#ef4444", // red
  rushing_yards: "#10b981", // emerald
  rushing_tds: "#14b8a6", // teal
  carries: "#6366f1", // indigo
  receiving_yards: "#f59e0b", // amber
  receiving_tds: "#f97316", // orange
  receptions: "#ec4899", // pink
  fumbles_lost: "#dc2626", // red darker
  // Kicker colors
  fg_att: "#0ea5e9", // sky
  fg_att_0_39: "#22c55e", // green
  fg_att_40_49: "#eab308", // yellow
  fg_att_50_plus: "#ef4444", // red
  pat_att: "#a855f7", // purple
  // Defense colors
  points_allowed: "#f43f5e", // rose
  def_sacks: "#06b6d4", // cyan
  def_interceptions: "#8b5cf6", // violet
  def_fumbles: "#f97316", // orange
  total_def_tds: "#10b981", // emerald
};

// Display names for stats
const STAT_DISPLAY_NAMES: Record<string, string> = {
  passing_yards: "Pass Yds",
  passing_tds: "Pass TDs",
  interceptions: "INTs",
  rushing_yards: "Rush Yds",
  rushing_tds: "Rush TDs",
  carries: "Carries",
  receiving_yards: "Rec Yds",
  receiving_tds: "Rec TDs",
  receptions: "Receptions",
  fumbles_lost: "Fumbles",
  // Kicker display names
  fg_att: "FG Att",
  fg_att_0_39: "FG 0-39",
  fg_att_40_49: "FG 40-49",
  fg_att_50_plus: "FG 50+",
  pat_att: "PAT Att",
  // Defense display names
  points_allowed: "Pts Allowed",
  def_sacks: "Sacks",
  def_interceptions: "INTs",
  def_fumbles: "Fumbles",
  total_def_tds: "Def TDs",
};

interface StatData {
  week: number;
  predicted: number;
  actual?: number;
  error?: number;
}

interface ConsolidatedPredictionChartProps {
  /** Data grouped by stat target */
  groupedData: Record<string, StatData[]>;
  /** Whether to show actual lines alongside predictions */
  showActuals?: boolean;
  /** Sync ID for synchronized tooltip/crosshair with other charts */
  syncId?: string;
}

export function ConsolidatedPredictionChart({
  groupedData,
  showActuals = true,
  syncId,
}: ConsolidatedPredictionChartProps) {
  const [highlightedStat, setHighlightedStat] = useState<string | null>(null);

  // Transform grouped data into a format suitable for ComposedChart
  // Each data point has week and values for each stat
  const chartData = useMemo(() => {
    const weekMap = new Map<number, Record<string, number | undefined>>();

    Object.entries(groupedData).forEach(([target, data]) => {
      data.forEach((item) => {
        const existing = weekMap.get(item.week) || { week: item.week };
        existing[`${target}_predicted`] = item.predicted;
        if (showActuals && item.actual !== undefined) {
          existing[`${target}_actual`] = item.actual;
        }
        weekMap.set(item.week, existing);
      });
    });

    return Array.from(weekMap.values()).sort((a, b) => (a.week ?? 0) - (b.week ?? 0));
  }, [groupedData, showActuals]);

  // Separate stats into yard stats and count stats
  const { yardStats, countStats } = useMemo(() => {
    const targets = Object.keys(groupedData);
    return {
      yardStats: targets.filter((t) => YARD_STATS.includes(t)),
      countStats: targets.filter((t) => COUNT_STATS.includes(t)),
    };
  }, [groupedData]);

  // Check if we have actuals
  const hasActuals = useMemo(() => {
    if (!showActuals) return false;
    return Object.values(groupedData).some((data) =>
      data.some((d) => d.actual !== undefined && d.actual !== null)
    );
  }, [groupedData, showActuals]);

  // Handle legend mouse events for highlighting
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleLegendMouseEnter = useCallback((data: any) => {
    if (data?.dataKey && typeof data.dataKey === "string") {
      // Extract base stat name from dataKey (e.g., "passing_yards_predicted" -> "passing_yards")
      const baseStat = data.dataKey.replace(/_predicted$|_actual$/, "");
      setHighlightedStat(baseStat);
    }
  }, []);

  const handleLegendMouseLeave = useCallback(() => {
    setHighlightedStat(null);
  }, []);

  // Calculate opacity for a line based on highlight state
  const getLineOpacity = useCallback(
    (stat: string) => {
      if (!highlightedStat) return 1;
      return stat === highlightedStat ? 1 : 0.15;
    },
    [highlightedStat]
  );

  // Calculate stroke width for a line based on highlight state
  const getStrokeWidth = useCallback(
    (stat: string, isActual: boolean) => {
      if (!highlightedStat) return isActual ? 1.5 : 2;
      return stat === highlightedStat ? (isActual ? 2 : 3) : isActual ? 1 : 1.5;
    },
    [highlightedStat]
  );

  if (Object.keys(groupedData).length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p className="text-sm">No prediction data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Legend with stats summary */}
      <div className="flex items-center gap-2 flex-wrap">
        {!hasActuals && (
          <Badge variant="outline" className="text-blue-600 border-blue-200">
            Predictions Only
          </Badge>
        )}
        <span className="text-xs text-muted-foreground ml-auto">
          Hover legend to highlight
        </span>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          syncId={syncId}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="week"
            tick={{ fontSize: 11 }}
            label={{ value: "Week", position: "insideBottom", offset: -5, fontSize: 11 }}
          />

          {/* Left Y-axis for yards (or counts if no yard stats) */}
          {yardStats.length > 0 ? (
            <YAxis
              yAxisId="yards"
              orientation="left"
              tick={{ fontSize: 11 }}
              label={{
                value: "Yards",
                angle: -90,
                position: "insideLeft",
                style: { textAnchor: "middle", fontSize: 11 },
              }}
            />
          ) : countStats.length > 0 ? (
            <YAxis
              yAxisId="counts"
              orientation="left"
              tick={{ fontSize: 11 }}
              label={{
                value: "Count",
                angle: -90,
                position: "insideLeft",
                style: { textAnchor: "middle", fontSize: 11 },
              }}
            />
          ) : null}

          {/* Right Y-axis for counts (only when we have both yard and count stats) */}
          {yardStats.length > 0 && countStats.length > 0 && (
            <YAxis
              yAxisId="counts"
              orientation="right"
              tick={{ fontSize: 11 }}
              label={{
                value: "Count",
                angle: 90,
                position: "insideRight",
                style: { textAnchor: "middle", fontSize: 11 },
              }}
            />
          )}

          <Tooltip
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              fontSize: "11px",
              maxHeight: "300px",
              overflow: "auto",
            }}
            formatter={(value, name) => {
              if (value === undefined || value === null) return ["—", name];
              const displayName = String(name)
                .replace(/_predicted$/, " (pred)")
                .replace(/_actual$/, " (actual)")
                .split("_")
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(" ");
              return [Number(value).toFixed(1), displayName];
            }}
          />

          <Legend
            wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }}
            onMouseEnter={handleLegendMouseEnter}
            onMouseLeave={handleLegendMouseLeave}
            formatter={(value: string) => {
              // Format legend text more nicely
              const isActual = value.endsWith("_actual");
              const baseStat = value.replace(/_predicted$|_actual$/, "");
              const displayName = STAT_DISPLAY_NAMES[baseStat] || baseStat;
              return isActual ? `${displayName} (A)` : displayName;
            }}
          />

          {/* Yard stat lines */}
          {yardStats.map((stat) => (
            <Line
              key={`${stat}_predicted`}
              type="monotone"
              dataKey={`${stat}_predicted`}
              stroke={STAT_COLORS[stat] || "#888"}
              strokeWidth={getStrokeWidth(stat, false)}
              strokeOpacity={getLineOpacity(stat)}
              dot={{ r: 2 }}
              yAxisId="yards"
              connectNulls
            />
          ))}

          {hasActuals &&
            yardStats.map((stat) => (
              <Line
                key={`${stat}_actual`}
                type="monotone"
                dataKey={`${stat}_actual`}
                stroke={STAT_COLORS[stat] || "#888"}
                strokeWidth={getStrokeWidth(stat, true)}
                strokeOpacity={getLineOpacity(stat)}
                strokeDasharray="5 5"
                dot={{ r: 2 }}
                yAxisId="yards"
                connectNulls
              />
            ))}

          {/* Count stat lines */}
          {countStats.map((stat) => (
            <Line
              key={`${stat}_predicted`}
              type="monotone"
              dataKey={`${stat}_predicted`}
              stroke={STAT_COLORS[stat] || "#888"}
              strokeWidth={getStrokeWidth(stat, false)}
              strokeOpacity={getLineOpacity(stat)}
              dot={{ r: 2 }}
              yAxisId="counts"
              connectNulls
            />
          ))}

          {hasActuals &&
            countStats.map((stat) => (
              <Line
                key={`${stat}_actual`}
                type="monotone"
                dataKey={`${stat}_actual`}
                stroke={STAT_COLORS[stat] || "#888"}
                strokeWidth={getStrokeWidth(stat, true)}
                strokeOpacity={getLineOpacity(stat)}
                strokeDasharray="5 5"
                dot={{ r: 2 }}
                yAxisId="counts"
                connectNulls
              />
            ))}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Axis Legend */}
      <div className="flex justify-between text-xs text-muted-foreground px-4">
        {yardStats.length > 0 && (
          <span>
            Left axis: {yardStats.map((s) => STAT_DISPLAY_NAMES[s]).join(", ")}
          </span>
        )}
        {countStats.length > 0 && yardStats.length > 0 && (
          <span>
            Right axis: {countStats.map((s) => STAT_DISPLAY_NAMES[s]).join(", ")}
          </span>
        )}
        {countStats.length > 0 && yardStats.length === 0 && (
          <span>
            {countStats.map((s) => STAT_DISPLAY_NAMES[s]).join(", ")}
          </span>
        )}
      </div>
    </div>
  );
}
