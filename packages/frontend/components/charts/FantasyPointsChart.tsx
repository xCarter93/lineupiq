"use client";

import {
  LineChart,
  Line,
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
 * Line chart for week-over-week fantasy points trend.
 * Uses Recharts with theme-aware colors.
 */
export function FantasyPointsChart({ data }: FantasyPointsChartProps) {
  // Sort by week ascending for proper line rendering
  const sortedData = [...data].sort((a, b) => a.week - b.week);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={sortedData}>
        <XAxis
          dataKey="week"
          tickFormatter={(w) => `Wk ${w}`}
          fontSize={12}
        />
        <YAxis domain={[0, "auto"]} fontSize={12} />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="fantasyPoints"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
