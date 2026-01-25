"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, Target } from "lucide-react";

interface LineupSummaryProps {
  totalProjected: number;
  lastWeekActual?: number;
  positionBreakdown: Record<string, number>;
  filledSlots: number;
  totalSlots: number;
}

export function LineupSummary({
  totalProjected,
  lastWeekActual,
  positionBreakdown,
  filledSlots,
  totalSlots,
}: LineupSummaryProps) {
  const difference = lastWeekActual ? totalProjected - lastWeekActual : 0;
  const percentChange = lastWeekActual
    ? ((difference / lastWeekActual) * 100).toFixed(1)
    : null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Target className="h-4 w-4" />
          Lineup Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Total Projected */}
        <div className="flex items-baseline justify-between">
          <span className="text-sm text-muted-foreground">Total Projected</span>
          <div className="text-right">
            <span className="text-2xl font-bold text-primary">
              {totalProjected.toFixed(1)}
            </span>
            <span className="text-sm text-muted-foreground ml-1">pts</span>
          </div>
        </div>

        {/* Comparison to Last Week */}
        {lastWeekActual !== undefined && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">vs. Last Week</span>
            <div className="flex items-center gap-1">
              {difference > 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : difference < 0 ? (
                <TrendingDown className="h-4 w-4 text-red-500" />
              ) : (
                <Minus className="h-4 w-4 text-muted-foreground" />
              )}
              <span
                className={
                  difference > 0
                    ? "text-green-600"
                    : difference < 0
                      ? "text-red-500"
                      : "text-muted-foreground"
                }
              >
                {difference > 0 ? "+" : ""}
                {difference.toFixed(1)} ({percentChange}%)
              </span>
            </div>
          </div>
        )}

        {/* Slots Filled */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Slots Filled</span>
          <Badge variant={filledSlots === totalSlots ? "default" : "secondary"}>
            {filledSlots} / {totalSlots}
          </Badge>
        </div>

        {/* Position Breakdown */}
        {Object.keys(positionBreakdown).length > 0 && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground mb-2">By Position</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(positionBreakdown).map(([position, points]) => (
                <div
                  key={position}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-muted-foreground">{position}</span>
                  <span className="font-medium">{points.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
