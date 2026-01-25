"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface WeeklyData {
  week: string;
  predicted: number;
  actual: number;
}

interface WeeklyTrendChartProps {
  data: WeeklyData[];
}

export function WeeklyTrendChart({ data }: WeeklyTrendChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Weekly Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis
                dataKey="week"
                type="category"
                tick={{ fontSize: 12 }}
                width={60}
              />
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
                dataKey="predicted"
                fill="#3b82f6"
                name="Predicted"
                radius={[0, 4, 4, 0]}
              />
              <Bar
                dataKey="actual"
                fill="#10b981"
                name="Actual"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
