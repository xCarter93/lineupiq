"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface FantasyPointsData {
  week: number;
  fantasyPoints: number;
}

interface FantasyPointsChartProps {
  data: FantasyPointsData[];
}

interface TooltipPayload {
  payload: FantasyPointsData;
  value: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

// Emerald-500 color for consistent branding
const CHART_COLOR = "#10b981";

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border rounded-lg shadow-sm p-2">
      <p className="text-sm font-medium">Week {payload[0].payload.week}</p>
      <p className="text-sm text-muted-foreground">
        {payload[0].value?.toFixed(1)} pts
      </p>
    </div>
  );
}

/**
 * Area chart for week-over-week fantasy points trend.
 * Uses explicit color values (emerald-500) for visibility.
 * Note: CSS variables use OKLCH format which doesn't work with Recharts.
 */
export function FantasyPointsChart({ data }: FantasyPointsChartProps) {
  // Sort by week ascending for proper line rendering
  const sortedData = [...data].sort((a, b) => a.week - b.week);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={sortedData}>
        <defs>
          <linearGradient id="colorFantasyPts" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={CHART_COLOR} stopOpacity={0.3} />
            <stop offset="95%" stopColor={CHART_COLOR} stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="week"
          tickFormatter={(w) => `Wk ${w}`}
          fontSize={12}
        />
        <YAxis domain={[0, "auto"]} fontSize={12} />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="fantasyPoints"
          stroke={CHART_COLOR}
          strokeWidth={2}
          fill="url(#colorFantasyPts)"
          dot={{ r: 4, fill: CHART_COLOR, stroke: CHART_COLOR }}
          activeDot={{ r: 6, fill: CHART_COLOR, stroke: "#fff", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
