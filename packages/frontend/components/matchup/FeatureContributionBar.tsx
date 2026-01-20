"use client";

import { cn } from "@/lib/utils";

interface FeatureContributionBarProps {
  displayName: string;
  contribution: number;
  maxContribution: number;
  value?: number;
}

/**
 * Horizontal bar showing a single feature's contribution to prediction.
 *
 * Positive contributions (green) indicate the feature pushed the prediction up.
 * Negative contributions (red) indicate the feature pushed the prediction down.
 * Width is proportional to |contribution| / maxContribution.
 */
export function FeatureContributionBar({
  displayName,
  contribution,
  maxContribution,
  value,
}: FeatureContributionBarProps) {
  const isPositive = contribution >= 0;
  const absContribution = Math.abs(contribution);
  const widthPct = maxContribution > 0 ? (absContribution / maxContribution) * 100 : 0;
  // Cap at 100% to handle edge cases
  const clampedWidth = Math.min(widthPct, 100);

  return (
    <div className="flex items-center gap-3">
      {/* Feature name - fixed width for alignment */}
      <span className="text-sm text-muted-foreground w-40 truncate shrink-0" title={displayName}>
        {displayName}
      </span>

      {/* Bar track */}
      <div className="flex-1 h-3 bg-muted/50 rounded-full overflow-hidden relative">
        {/* Contribution bar */}
        <div
          className={cn(
            "absolute top-0 h-full rounded-full transition-all duration-200",
            isPositive ? "bg-emerald-500" : "bg-red-500"
          )}
          style={{ width: `${clampedWidth}%` }}
        />
      </div>

      {/* Contribution value */}
      <span
        className={cn(
          "text-sm font-medium tabular-nums w-14 text-right shrink-0",
          isPositive ? "text-emerald-600" : "text-red-600"
        )}
      >
        {isPositive ? "+" : ""}
        {contribution.toFixed(1)}
      </span>

      {/* Optional feature value */}
      {value !== undefined && (
        <span className="text-xs text-muted-foreground w-16 text-right shrink-0 tabular-nums">
          ({value.toFixed(1)})
        </span>
      )}
    </div>
  );
}
