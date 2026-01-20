"use client";

import { SectionLabel } from "@/components/ui/section-label";
import { cn } from "@/lib/utils";
import type {
  QBPrediction,
  RBPrediction,
  ReceiverPrediction,
} from "@/lib/fantasy-points";

interface StatProjectionProps {
  position: "QB" | "RB" | "WR" | "TE";
  prediction: QBPrediction | RBPrediction | ReceiverPrediction;
  playerName: string;
  opponentTeam: string;
  isLoading?: boolean;
  compact?: boolean;
}

interface StatDisplayProps {
  label: string;
  value: number;
  unit?: string;
  isNegative?: boolean; // For fumbles and interceptions
}

function StatDisplay({ label, value, unit, isNegative = false }: StatDisplayProps) {
  return (
    <div className="flex flex-col items-center text-center p-4 bg-muted/20 rounded-lg">
      <span className={cn(
        "text-3xl font-bold tabular-nums",
        isNegative ? "text-red-600" : "text-foreground"
      )}>
        {value.toFixed(1)}
        {unit && <span className="text-lg font-normal ml-1">{unit}</span>}
      </span>
      <span className="text-xs text-muted-foreground uppercase tracking-wide mt-2">
        {label}
      </span>
    </div>
  );
}

function StatSkeleton() {
  return (
    <div className="flex flex-col items-center text-center p-4 bg-muted/20 rounded-lg">
      <div className="h-9 w-16 bg-muted/50 rounded animate-pulse" />
      <div className="h-3 w-20 bg-muted/30 rounded animate-pulse mt-3" />
    </div>
  );
}

export function StatProjection({
  position,
  prediction,
  playerName,
  opponentTeam,
  isLoading = false,
  compact = false,
}: StatProjectionProps) {
  // Render loading skeleton
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8">
        <div className="mb-6">
          <SectionLabel className="block mb-2">PROJECTED STATS</SectionLabel>
          <div className="h-5 w-48 bg-muted/30 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-4">
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
        </div>
      </div>
    );
  }

  // Get stats based on position
  const renderStats = () => {
    if (position === "QB") {
      const qb = prediction as QBPrediction;
      return (
        <>
          <StatDisplay label="Passing Yards" value={qb.passing_yards} />
          <StatDisplay label="Passing TDs" value={qb.passing_tds} />
          <StatDisplay label="Interceptions" value={qb.interceptions} isNegative />
          <StatDisplay label="Rushing Yards" value={qb.rushing_yards} />
          <StatDisplay label="Rushing TDs" value={qb.rushing_tds} />
          <StatDisplay label="Fumbles Lost" value={qb.fumbles_lost} isNegative />
        </>
      );
    }

    if (position === "RB") {
      const rb = prediction as RBPrediction;
      return (
        <>
          <StatDisplay label="Rushing Yards" value={rb.rushing_yards} />
          <StatDisplay label="Rushing TDs" value={rb.rushing_tds} />
          <StatDisplay label="Carries" value={rb.carries} />
          <StatDisplay label="Receiving Yards" value={rb.receiving_yards} />
          <StatDisplay label="Receiving TDs" value={rb.receiving_tds} />
          <StatDisplay label="Receptions" value={rb.receptions} />
          <StatDisplay label="Fumbles Lost" value={rb.fumbles_lost} isNegative />
        </>
      );
    }

    // WR or TE
    const rec = prediction as ReceiverPrediction;
    return (
      <>
        <StatDisplay label="Receiving Yards" value={rec.receiving_yards} />
        <StatDisplay label="Receiving TDs" value={rec.receiving_tds} />
        <StatDisplay label="Receptions" value={rec.receptions} />
        <StatDisplay label="Fumbles Lost" value={rec.fumbles_lost} isNegative />
      </>
    );
  };

  // Determine grid columns based on stat count - full width layout
  const gridCols = cn(
    "grid gap-4",
    position === "QB"
      ? "grid-cols-3 sm:grid-cols-6" // 6 stats - 3 per row on mobile, all on desktop
      : position === "RB"
        ? "grid-cols-2 sm:grid-cols-4 lg:grid-cols-7" // 7 stats
        : "grid-cols-2 sm:grid-cols-4" // WR/TE: 4 stats
  );

  // Compact mode: no card wrapper, smaller padding
  if (compact) {
    return (
      <div
        role="region"
        aria-label={`Projected stats for ${playerName} versus ${opponentTeam}`}
      >
        <p className="text-sm text-muted-foreground mb-3">
          <span className="font-medium text-foreground">{playerName}</span>
          <span className="mx-2">vs</span>
          <span className="font-medium text-foreground">{opponentTeam}</span>
        </p>
        <div className={gridCols}>{renderStats()}</div>
      </div>
    );
  }

  return (
    <div
      className="bg-white rounded-xl shadow-sm p-8"
      role="region"
      aria-label={`Projected stats for ${playerName} versus ${opponentTeam}`}
    >
      <div className="mb-6">
        <SectionLabel className="block mb-2">PROJECTED STATS</SectionLabel>
        <p className="text-muted-foreground">
          <span className="font-medium text-foreground">{playerName}</span>
          <span className="mx-2">vs</span>
          <span className="font-medium text-foreground">{opponentTeam}</span>
        </p>
      </div>
      <div className={gridCols}>{renderStats()}</div>
    </div>
  );
}
