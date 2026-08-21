"use client";

import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { PredictionSourceDot } from "@/components/ui/prediction-source";
import type { PointsBreakdown } from "@/lib/fantasy-points";
import type { PredictionRow } from "@/lib/prediction-points";

interface ProjectedPointsBreakdownProps {
  /** Per-stat contributions from the app's scoring calculator. */
  breakdown: PointsBreakdown;
  /** The prediction rows behind the breakdown, for per-stat source markers. */
  scoredRows: PredictionRow[];
  week: number;
  /** Name of the active scoring config, shown so the math is attributable. */
  scoringName: string;
}

export function ProjectedPointsBreakdown({
  breakdown,
  scoredRows,
  week,
  scoringName,
}: ProjectedPointsBreakdownProps) {
  const sourceByTarget = useMemo(
    () => new Map(scoredRows.map((row) => [row.target, row.source])),
    [scoredRows]
  );

  const contributions = useMemo(
    () =>
      [...breakdown.categories].sort(
        (a, b) => Math.abs(b.points) - Math.abs(a.points)
      ),
    [breakdown.categories]
  );

  const maxContribution = useMemo(() => {
    const positive = contributions.filter((c) => c.points > 0);
    return positive.length > 0
      ? Math.max(...positive.map((c) => c.points))
      : 1;
  }, [contributions]);

  if (contributions.length === 0) {
    return (
      <div className="text-center py-4 text-muted-foreground">
        <p className="text-sm">No projection data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Total Points Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">
          Week {week} Projection
        </span>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-primary">
            {breakdown.total.toFixed(1)}
          </span>
          <span className="text-sm text-muted-foreground">pts</span>
        </div>
      </div>

      {/* Breakdown List */}
      <div className="space-y-3">
        {contributions.map((contrib) => {
          const source = sourceByTarget.get(contrib.target);

          return (
            <div key={contrib.target} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  {source && <PredictionSourceDot mix={source} />}
                  <span className="font-medium">{contrib.label}</span>
                  <span className="text-muted-foreground">{contrib.detail}</span>
                </div>
                <Badge
                  variant="outline"
                  className={
                    contrib.points > 0
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : contrib.points < 0
                        ? "bg-red-50 text-red-700 border-red-200"
                        : ""
                  }
                >
                  {contrib.points > 0 ? "+" : ""}
                  {contrib.points.toFixed(1)}
                </Badge>
              </div>
              {contrib.points > 0 && (
                <Progress
                  value={(contrib.points / maxContribution) * 100}
                  className="h-1.5"
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Scoring Format Note */}
      <div className="text-xs text-muted-foreground text-center pt-2 border-t">
        {scoringName} scoring
      </div>
    </div>
  );
}
