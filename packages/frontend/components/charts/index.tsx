"use client";

import dynamic from "next/dynamic";

/**
 * Loading placeholder for chart components.
 * Height matches chart height (200px) to prevent layout shift.
 */
const ChartLoader = () => (
  <div className="h-[200px] flex items-center justify-center bg-muted/30 rounded-lg animate-pulse">
    <span className="text-sm text-muted-foreground">Loading chart...</span>
  </div>
);

/**
 * SSR-safe FantasyPointsChart export.
 * Uses dynamic import with ssr: false to avoid hydration mismatches.
 * Recharts uses browser APIs (window, document) that break SSR.
 */
export const FantasyPointsChart = dynamic(
  () => import("./FantasyPointsChart").then((mod) => mod.FantasyPointsChart),
  { ssr: false, loading: ChartLoader }
);
