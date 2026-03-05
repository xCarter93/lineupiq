"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Badge } from "@/components/ui/badge";

interface ValidationChartProps {
  target: string;
  data: Array<{ week: number; predicted: number; actual?: number; error?: number }>;
  targetDisplayName: string;
  syncId?: string;
  /** Whether to show the actual line (default: true) */
  showActuals?: boolean;
}

export function ValidationChart({ target, data, targetDisplayName, syncId, showActuals = true }: ValidationChartProps) {
  // Sort by week
  const sortedData = [...data].sort((a, b) => a.week - b.week);

  // Check if we have actual data
  const hasActuals = showActuals && data.some(d => d.actual !== undefined && d.actual !== null);

  // Calculate MAE and R² only if we have actuals
  let mae = 0;
  let r2 = 0;
  let accuracyPct = 0;

  if (hasActuals) {
    const dataWithActuals = data.filter(d => d.actual !== undefined && d.error !== undefined);
    mae = dataWithActuals.reduce((sum, d) => sum + Math.abs(d.error!), 0) / dataWithActuals.length;

    const actualMean = dataWithActuals.reduce((sum, d) => sum + d.actual!, 0) / dataWithActuals.length;
    const ssRes = dataWithActuals.reduce((sum, d) => sum + Math.pow(d.error!, 2), 0);
    const ssTot = dataWithActuals.reduce((sum, d) => sum + Math.pow(d.actual! - actualMean, 2), 0);
    r2 = ssTot > 0 ? Math.max(0, 1 - ssRes / ssTot) : 0;

    accuracyPct = Math.max(0, Math.min(100, r2 * 100));
  }

  return (
    <div className="space-y-3">
      {/* Metric Badges */}
      <div className="flex items-center gap-3 text-sm flex-wrap">
        <span className="font-medium text-muted-foreground">{targetDisplayName}</span>
        {hasActuals ? (
          <>
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
          </>
        ) : (
          <Badge variant="outline" className="text-blue-600 border-blue-200">
            Predictions Only
          </Badge>
        )}
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
          {hasActuals && (
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ r: 3 }}
              name="Actual"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
