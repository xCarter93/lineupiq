import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";

export function useValidationPredictions(playerId: string, season: number = 2025) {
  const predictions = useQuery(
    api.validationPredictions.getPlayerValidationPredictions,
    { playerId, season }
  );

  // Group by target stat for chart display
  const groupedByTarget = predictions?.reduce((acc, pred) => {
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

  return { predictions, groupedByTarget, isLoading: predictions === undefined };
}
