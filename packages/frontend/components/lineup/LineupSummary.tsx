"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Target } from "lucide-react";

interface LineupSummaryProps {
  totalProjected: number;
  /** How many filled slots actually have a prediction behind them. */
  projectedPlayers: number;
  isLoading?: boolean;
  positionBreakdown: Record<string, number>;
  filledSlots: number;
  totalSlots: number;
}

export function LineupSummary({
  totalProjected,
  projectedPlayers,
  isLoading = false,
  positionBreakdown,
  filledSlots,
  totalSlots,
}: LineupSummaryProps) {
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
            {projectedPlayers > 0 ? (
              <>
                <span className="text-2xl font-bold text-primary">
                  {totalProjected.toFixed(1)}
                </span>
                <span className="text-sm text-muted-foreground ml-1">pts</span>
              </>
            ) : (
              <span
                className={`text-2xl font-bold text-muted-foreground${isLoading ? " animate-pulse" : ""}`}
              >
                &mdash;
              </span>
            )}
          </div>
        </div>

        {/* Prediction coverage */}
        {filledSlots > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">With Predictions</span>
            <span
              className={
                projectedPlayers === filledSlots
                  ? "text-muted-foreground"
                  : "text-foreground"
              }
            >
              {projectedPlayers} / {filledSlots}
            </span>
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
