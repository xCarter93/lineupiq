"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface PositionData {
  position: string;
  points: number;
  percentage: number;
  [key: string]: string | number;
}

interface PositionContributionChartProps {
  data: PositionData[];
}

const COLORS = [
  "#3b82f6", // QB - blue
  "#10b981", // RB - green
  "#f59e0b", // WR - amber
  "#8b5cf6", // TE - purple
  "#ec4899", // K - pink
  "#6b7280", // DEF - gray
];

export function PositionContributionChart({
  data,
}: PositionContributionChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Points by Position</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="points"
                nameKey="position"
                label={({ name, percent }) =>
                  `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
                labelLine={false}
              >
                {data.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                formatter={(value) =>
                  typeof value === "number" ? `${value.toFixed(1)} pts` : value
                }
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
