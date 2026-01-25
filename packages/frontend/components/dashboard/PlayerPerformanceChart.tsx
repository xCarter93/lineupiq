"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from "recharts";

interface PlayerPerformanceData {
  player: string;
  actual: number;
  predicted: number;
  position: string;
}

interface PlayerPerformanceChartProps {
  data: PlayerPerformanceData[];
}

// Position colors (for future use with colored bars)
// const POSITION_COLORS: Record<string, string> = {
//   QB: "#3b82f6", RB: "#10b981", WR: "#f59e0b", TE: "#8b5cf6", K: "#ec4899", DEF: "#6b7280",
// };

export function PlayerPerformanceChart({ data }: PlayerPerformanceChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    name: d.player.split(" ").pop(), // Last name only for chart
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Player Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                formatter={(value) =>
                  typeof value === "number" ? value.toFixed(1) : value
                }
              />
              <Legend wrapperStyle={{ fontSize: "12px" }} />
              <Bar
                dataKey="actual"
                fill="#3b82f6"
                name="Actual"
                radius={[4, 4, 0, 0]}
              />
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Predicted"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
