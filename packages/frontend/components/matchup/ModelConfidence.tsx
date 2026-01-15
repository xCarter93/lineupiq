"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ModelConfidenceProps {
  accuracyPct: number | null;
  confidence: string | null;
  isLoading?: boolean;
  className?: string;
}

/**
 * Display model confidence indicator.
 *
 * Shows accuracy percentage with color-coded badge based on confidence tier.
 */
export function ModelConfidence({
  accuracyPct,
  confidence,
  isLoading = false,
  className,
}: ModelConfidenceProps) {
  if (isLoading) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div className="h-5 w-24 bg-muted/30 rounded animate-pulse" />
      </div>
    );
  }

  if (accuracyPct === null) {
    return null; // Don't show if no data available
  }

  // Color based on confidence tier
  const badgeVariant =
    confidence === "High"
      ? "default" // Primary color
      : confidence === "Medium"
        ? "secondary"
        : "outline";

  // Color classes for the percentage text
  const textColor =
    confidence === "High"
      ? "text-emerald-600"
      : confidence === "Medium"
        ? "text-amber-600"
        : "text-muted-foreground";

  return (
    <div
      className={cn("flex items-center gap-2 text-sm", className)}
      title={`Model accuracy: ${accuracyPct.toFixed(1)}%`}
    >
      <span className={cn("font-medium tabular-nums", textColor)}>
        {accuracyPct.toFixed(0)}% accurate
      </span>
      <Badge variant={badgeVariant} className="text-xs">
        {confidence} confidence
      </Badge>
    </div>
  );
}
