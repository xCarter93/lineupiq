import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useEffect, useMemo } from "react";
import { getLastCompletedSeason } from "@/lib/season";

interface SimulationFilter {
  /** When true, filter predictions based on simulation state */
  enabled: boolean;
  /** Number of completed weeks in simulation (0 = pre-season) */
  completedWeeks: number;
}

/**
 * Hook to get validation predictions (predicted vs actual) for a player.
 *
 * @param playerId - The player's ID
 * @param season - The season to fetch (default: last completed season)
 * @param simulationFilter - Optional filter to only show completed weeks during simulation
 */
export function useValidationPredictions(
  playerId: string,
  season: number = getLastCompletedSeason(),
  simulationFilter?: SimulationFilter
) {
  const predictions = useQuery(
    api.validationPredictions.getPlayerValidationPredictions,
    { playerId, season }
  );

  // Debug logging
  useEffect(() => {
    if (predictions !== undefined) {
      console.log(`[useValidationPredictions] Player ${playerId}, Season ${season}:`, {
        count: predictions?.length ?? 0,
        simulationFilter,
        predictions: predictions,
      });
    }
  }, [predictions, playerId, season, simulationFilter]);

  // Filter predictions based on simulation state
  const filteredPredictions = useMemo(() => {
    if (!predictions) return undefined;

    // If no simulation filter or not enabled, return all predictions
    if (!simulationFilter?.enabled) {
      return predictions;
    }

    // Only show predictions for completed weeks (where we have actuals)
    return predictions.filter((pred) => pred.week <= simulationFilter.completedWeeks);
  }, [predictions, simulationFilter]);

  // Group by target stat for chart display
  const groupedByTarget = useMemo(() => {
    if (!filteredPredictions) return undefined;

    return filteredPredictions.reduce((acc, pred) => {
      if (!acc[pred.target]) {
        acc[pred.target] = [];
      }
      acc[pred.target].push({
        week: pred.week,
        predicted: pred.predictedValue,
        actual: pred.actualValue,
        error: pred.error,
      });
      return acc;
    }, {} as Record<string, Array<{ week: number; predicted: number; actual: number; error: number }>>);
  }, [filteredPredictions]);

  return {
    predictions: filteredPredictions,
    groupedByTarget,
    isLoading: predictions === undefined,
    // Expose whether there's data available (even if filtered out)
    hasAnyData: (predictions?.length ?? 0) > 0,
  };
}
