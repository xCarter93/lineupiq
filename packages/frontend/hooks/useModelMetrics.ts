"use client";

import { useQuery } from "convex/react";
import { useEffect, useState } from "react";
import { api } from "../convex/_generated/api";
import { fetchValidationMetrics, ValidationResponse } from "@/lib/prediction-api";
import { getLastCompletedSeason } from "@/lib/season";

interface UseModelMetricsResult {
  overallAccuracy: number | null;
  overallConfidence: string | null;
  isLoading: boolean;
  error: Error | null;
  getModelAccuracy: (position: string, target: string) => number | null;
}

/**
 * Hook to access model validation metrics.
 *
 * First checks Convex cache, falls back to API fetch if not available.
 */
export function useModelMetrics(): UseModelMetricsResult {
  // Metrics are validated against the last season with complete actuals
  const validationSeason = getLastCompletedSeason();

  // Try Convex first (cached data)
  const convexMetrics = useQuery(api.modelMetrics.getOverallMetrics, {
    season: validationSeason,
  });
  const allModelMetrics = useQuery(api.modelMetrics.getAllMetrics, {});

  // API fallback state
  const [apiData, setApiData] = useState<ValidationResponse | null>(null);
  const [apiError, setApiError] = useState<Error | null>(null);

  // Fetch from API if Convex has no data
  // The async operation manages state transitions via promise callbacks
  useEffect(() => {
    if (convexMetrics === undefined) return; // Still loading from Convex
    if (convexMetrics !== null) return; // Have Convex data
    if (apiData || apiError) return; // Already have API result

    // Start fetch - state updates happen in callbacks
    void fetchValidationMetrics(validationSeason)
      .then(setApiData)
      .catch(setApiError);
  }, [convexMetrics, apiData, apiError, validationSeason]);

  // Determine overall metrics source
  const overallAccuracy =
    convexMetrics?.overallAccuracyPct ?? apiData?.overall.overall_accuracy_pct ?? null;
  const overallConfidence =
    convexMetrics?.overallConfidence ?? apiData?.overall.overall_confidence ?? null;

  // Helper to get specific model accuracy
  const getModelAccuracy = (position: string, target: string): number | null => {
    // Check Convex data first
    if (allModelMetrics) {
      const found = allModelMetrics.find(
        (m) => m.position === position && m.target === target
      );
      if (found) return found.accuracyPct;
    }

    // Fall back to API data
    if (apiData) {
      const found = apiData.by_model.find(
        (m) => m.position === position && m.target === target
      );
      if (found) return found.accuracy_pct;
    }

    return null;
  };

  // Derive loading state: waiting for Convex, or Convex is null but no API response yet
  const isLoading =
    convexMetrics === undefined ||
    (convexMetrics === null && !apiData && !apiError);

  return {
    overallAccuracy,
    overallConfidence,
    isLoading,
    error: apiError,
    getModelAccuracy,
  };
}
