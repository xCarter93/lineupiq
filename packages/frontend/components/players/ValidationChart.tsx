"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Badge } from "@/components/ui/badge";

interface ValidationChartProps {
  target: string;
  data: Array<{ week: number; predicted: number; actual: number; error: number }>;
  targetDisplayName: string;
  syncId?: string;
}

export function ValidationChart({ target, data, targetDisplayName, syncId }: ValidationChartProps) {
  // Sort by week
  const sortedData = [...data].sort((a, b) => a.week - b.week);

  // Calculate MAE and R²
  const mae = data.reduce((sum, d) => sum + Math.abs(d.error), 0) / data.length;

  const actualMean = data.reduce((sum, d) => sum + d.actual, 0) / data.length;
  const ssRes = data.reduce((sum, d) => sum + Math.pow(d.error, 2), 0);
  const ssTot = data.reduce((sum, d) => sum + Math.pow(d.actual - actualMean, 2), 0);
  const r2 = Math.max(0, 1 - ssRes / ssTot);

  const accuracyPct = Math.max(0, Math.min(100, r2 * 100));

  return (
    <div className="space-y-3">
      {/* Metric Badges */}
      <div className="flex items-center gap-3 text-sm">
        <span className="font-medium text-muted-foreground">{targetDisplayName}</span>
        <Badge variant="outline">MAE: {mae.toFixed(1)}</Badge>
        <Badge variant="outline">R²: {r2.toFixed(3)}</Badge>
        <Badge
          className={
            accuracyPct >= 50
              ? "bg-emerald-100 text-emerald-700"
              : accuracyPct >= 30
              ? "bg-yellow-100 text-yellow-700"
              : "bg-red-100 text-red-700"
          }
        >
          {accuracyPct.toFixed(0)}% Accuracy
        </Badge>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={sortedData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }} syncId={syncId}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="week"
            label={{ value: "Week", position: "insideBottom", offset: -5 }}
            tick={{ fontSize: 12 }}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            formatter={(value) => typeof value === "number" ? value.toFixed(1) : value}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3 }}
            name="Predicted"
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 3 }}
            name="Actual"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
