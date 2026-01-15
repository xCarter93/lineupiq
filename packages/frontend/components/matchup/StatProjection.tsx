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
}

interface StatDisplayProps {
  label: string;
  value: number;
  unit?: string;
}

function StatDisplay({ label, value, unit }: StatDisplayProps) {
  return (
    <div className="flex flex-col">
      <span className="text-3xl font-bold text-foreground tabular-nums">
        {value.toFixed(1)}
        {unit && <span className="text-lg font-normal ml-1">{unit}</span>}
      </span>
      <span className="text-sm text-muted-foreground uppercase tracking-wide mt-1">
        {label}
      </span>
    </div>
  );
}

function StatSkeleton() {
  return (
    <div className="flex flex-col">
      <div className="h-9 w-20 bg-muted/50 rounded animate-pulse" />
      <div className="h-4 w-16 bg-muted/30 rounded animate-pulse mt-2" />
    </div>
  );
}

export function StatProjection({
  position,
  prediction,
  playerName,
  opponentTeam,
  isLoading = false,
}: StatProjectionProps) {
  // Render loading skeleton
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8">
        <div className="mb-6">
          <SectionLabel className="block mb-2">PROJECTED STATS</SectionLabel>
          <div className="h-5 w-48 bg-muted/30 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
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
          <StatDisplay label="Receptions" value={rb.receptions} />
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
      </>
    );
  };

  // Determine grid columns based on stat count
  const gridCols = cn(
    "grid gap-6",
    position === "QB"
      ? "grid-cols-2"
      : position === "RB"
        ? "grid-cols-2 md:grid-cols-3 lg:grid-cols-5"
        : "grid-cols-3"
  );

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
