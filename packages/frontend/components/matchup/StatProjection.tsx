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

interface StatCardProps {
  label: string;
  value: number;
  isNegative?: boolean;
  highlight?: boolean;
}

function StatCard({ label, value, isNegative = false, highlight = false }: StatCardProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col rounded-xl border p-4 transition-all",
        highlight
          ? "bg-primary/5 border-primary/20"
          : "bg-white border-border/50 hover:border-border"
      )}
    >
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
        {label}
      </span>
      <span
        className={cn(
          "text-2xl font-bold tabular-nums",
          isNegative ? "text-red-600" : "text-foreground"
        )}
      >
        {value.toFixed(1)}
      </span>
    </div>
  );
}

function StatCardSkeleton() {
  return (
    <div className="flex flex-col rounded-xl border border-border/50 bg-white p-4">
      <div className="h-3 w-16 bg-muted/30 rounded animate-pulse mb-3" />
      <div className="h-7 w-12 bg-muted/50 rounded animate-pulse" />
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
  // Loading skeleton
  if (isLoading) {
    const skeletonCount = position === "QB" ? 6 : position === "RB" ? 7 : 4;
    const content = (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    );

    if (compact) return content;
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="mb-4">
          <SectionLabel className="block mb-2">PROJECTED STATS</SectionLabel>
          <div className="h-5 w-48 bg-muted/30 rounded animate-pulse" />
        </div>
        {content}
      </div>
    );
  }

  // Build stats array based on position
  const getStats = () => {
    if (position === "QB") {
      const qb = prediction as QBPrediction;
      return [
        { label: "Pass Yards", value: qb.passing_yards, highlight: true },
        { label: "Pass TDs", value: qb.passing_tds, highlight: true },
        { label: "Interceptions", value: qb.interceptions, isNegative: true },
        { label: "Rush Yards", value: qb.rushing_yards },
        { label: "Rush TDs", value: qb.rushing_tds },
        { label: "Fumbles", value: qb.fumbles_lost, isNegative: true },
      ];
    }

    if (position === "RB") {
      const rb = prediction as RBPrediction;
      return [
        { label: "Rush Yards", value: rb.rushing_yards, highlight: true },
        { label: "Rush TDs", value: rb.rushing_tds, highlight: true },
        { label: "Carries", value: rb.carries },
        { label: "Rec Yards", value: rb.receiving_yards },
        { label: "Rec TDs", value: rb.receiving_tds },
        { label: "Receptions", value: rb.receptions },
        { label: "Fumbles", value: rb.fumbles_lost, isNegative: true },
      ];
    }

    // WR or TE
    const rec = prediction as ReceiverPrediction;
    return [
      { label: "Rec Yards", value: rec.receiving_yards, highlight: true },
      { label: "Rec TDs", value: rec.receiving_tds, highlight: true },
      { label: "Receptions", value: rec.receptions },
      { label: "Fumbles", value: rec.fumbles_lost, isNegative: true },
    ];
  };

  const stats = getStats();

  // Grid layout - responsive
  const gridCols = cn(
    "grid gap-3",
    position === "QB"
      ? "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6"
      : position === "RB"
        ? "grid-cols-2 sm:grid-cols-4 lg:grid-cols-7"
        : "grid-cols-2 sm:grid-cols-4"
  );

  const statsGrid = (
    <div className={gridCols}>
      {stats.map((stat) => (
        <StatCard
          key={stat.label}
          label={stat.label}
          value={stat.value}
          isNegative={stat.isNegative}
          highlight={stat.highlight}
        />
      ))}
    </div>
  );

  // Compact mode: no outer wrapper
  if (compact) {
    return (
      <div role="region" aria-label={`Projected stats for ${playerName} versus ${opponentTeam}`}>
        <p className="text-sm text-muted-foreground mb-3">
          <span className="font-medium text-foreground">{playerName}</span>
          <span className="mx-2">vs</span>
          <span className="font-medium text-foreground">{opponentTeam}</span>
        </p>
        {statsGrid}
      </div>
    );
  }

  return (
    <div
      className="bg-white rounded-xl shadow-sm p-6"
      role="region"
      aria-label={`Projected stats for ${playerName} versus ${opponentTeam}`}
    >
      <div className="mb-4">
        <SectionLabel className="block mb-2">PROJECTED STATS</SectionLabel>
        <p className="text-muted-foreground">
          <span className="font-medium text-foreground">{playerName}</span>
          <span className="mx-2">vs</span>
          <span className="font-medium text-foreground">{opponentTeam}</span>
        </p>
      </div>
      {statsGrid}
    </div>
  );
}
