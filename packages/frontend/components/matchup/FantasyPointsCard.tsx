"use client";

import { SectionLabel } from "@/components/ui/section-label";
import type { PointsBreakdown } from "@/lib/fantasy-points";

interface FantasyPointsCardProps {
  points: number;
  breakdown: PointsBreakdown;
  scoringConfigName: string;
  isLoading?: boolean;
}

export function FantasyPointsCard({
  points,
  breakdown,
  scoringConfigName,
  isLoading = false,
}: FantasyPointsCardProps) {
  // Render loading skeleton
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8 md:p-10">
        {/* Header skeleton */}
        <div className="mb-6">
          <SectionLabel className="block mb-2">FANTASY POINTS</SectionLabel>
        </div>

        {/* Points skeleton */}
        <div className="text-center mb-8">
          <div className="h-20 w-32 mx-auto bg-muted/50 rounded animate-pulse" />
          <div className="h-5 w-40 mx-auto bg-muted/30 rounded animate-pulse mt-3" />
          <div className="h-6 w-28 mx-auto bg-muted/20 rounded-full animate-pulse mt-4" />
        </div>

        {/* Breakdown skeleton */}
        <div className="border-t border-border/30 pt-6 space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-10 bg-muted/20 rounded animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-8 md:p-10">
      {/* Header */}
      <div className="mb-6">
        <SectionLabel className="block mb-2">FANTASY POINTS</SectionLabel>
      </div>

      {/* Hero Points Display */}
      <div className="text-center mb-8">
        <div className="text-6xl md:text-7xl font-bold text-primary tabular-nums">
          {points.toFixed(1)}
        </div>
        <div className="text-lg text-muted-foreground mt-2">
          projected points
        </div>
        <div className="inline-flex items-center mt-4 px-4 py-1.5 bg-muted/30 rounded-full">
          <span className="text-sm font-medium text-muted-foreground">
            {scoringConfigName} Scoring
          </span>
        </div>
      </div>

      {/* Points Breakdown */}
      <div className="border-t border-border/30 pt-6">
        <div className="space-y-1">
          {breakdown.categories.map((category, index) => (
            <div
              key={category.label}
              className={`flex items-center justify-between py-3 ${
                index < breakdown.categories.length - 1
                  ? "border-b border-border/20"
                  : ""
              }`}
            >
              {/* Label */}
              <span className="text-sm font-medium text-foreground">
                {category.label}
              </span>

              {/* Detail (center) */}
              <span className="text-sm text-muted-foreground flex-1 text-center px-4">
                {category.detail}
              </span>

              {/* Points (right) */}
              <span className="text-sm font-semibold text-primary tabular-nums">
                +{category.points.toFixed(1)} pts
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
