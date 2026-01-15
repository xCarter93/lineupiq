"use client";

import { useState } from "react";
import { SectionLabel } from "@/components/ui/section-label";
import { MatchupForm, MatchupData } from "@/components/matchup/MatchupForm";
import { StatProjection } from "@/components/matchup/StatProjection";
import { FantasyPointsCard } from "@/components/matchup/FantasyPointsCard";
import {
  predict,
  createDefaultFeatures,
  type Prediction,
} from "@/lib/prediction-api";
import {
  calculateFantasyPoints,
  getPointsBreakdown,
  type ScoringConfig,
  type PointsBreakdown,
} from "@/lib/fantasy-points";
import { useDefaultScoringConfig } from "@/hooks/useScoringConfigs";

// Default scoring config (Standard) as fallback while Convex loads
const DEFAULT_SCORING_CONFIG: ScoringConfig = {
  passing: { yardsPerPoint: 25, tdPoints: 4, intPoints: -2 },
  rushing: { yardsPerPoint: 10, tdPoints: 6 },
  receiving: { yardsPerPoint: 10, tdPoints: 6, receptionPoints: 0 },
};

export default function MatchupPage() {
  const [matchupData, setMatchupData] = useState<MatchupData | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get default scoring config from Convex
  const { config: convexConfig } = useDefaultScoringConfig();

  // Use Convex config if available, otherwise use default
  const scoringConfig: ScoringConfig = convexConfig
    ? {
        passing: convexConfig.passing,
        rushing: convexConfig.rushing,
        receiving: convexConfig.receiving,
      }
    : DEFAULT_SCORING_CONFIG;

  const scoringConfigName = convexConfig?.name || "Standard";

  const handleSubmit = async (matchup: MatchupData) => {
    setIsLoading(true);
    setError(null);
    setMatchupData(matchup);
    setPrediction(null);

    try {
      const features = createDefaultFeatures(matchup.position, matchup.isHome);
      const result = await predict(matchup.position, features);
      setPrediction(result);
    } catch (err) {
      // Provide helpful error message for API not running
      if (
        err instanceof Error &&
        (err.message.includes("fetch") || err.message.includes("Failed"))
      ) {
        setError(
          "Prediction API not available. Start the API with: cd packages/backend && uv run uvicorn lineupiq.api.main:app --port 8000"
        );
      } else {
        setError(
          err instanceof Error ? err.message : "Failed to get prediction"
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate fantasy points when prediction is available
  const fantasyPoints =
    prediction && matchupData
      ? calculateFantasyPoints(matchupData.position, prediction, scoringConfig)
      : 0;

  const pointsBreakdown: PointsBreakdown =
    prediction && matchupData
      ? getPointsBreakdown(matchupData.position, prediction, scoringConfig)
      : { total: 0, categories: [] };

  return (
    <div className="min-h-screen">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="mb-12">
          <SectionLabel className="mb-4 block">MATCHUP SIMULATOR</SectionLabel>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-3">
            Build Your Matchup
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Select a player and opponent to see ML-powered stat projections
          </p>
        </div>

        {/* Matchup Form */}
        <MatchupForm onSubmit={handleSubmit} isLoading={isLoading} />

        {/* Results Section */}
        {(isLoading || prediction || error) && matchupData && (
          <div className="mt-8 animate-in fade-in duration-300">
            {/* Error State */}
            {error && !isLoading && (
              <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-destructive">
                <SectionLabel className="mb-3 block">ERROR</SectionLabel>
                <p className="text-destructive font-medium mb-2">
                  Failed to get prediction
                </p>
                <p className="text-sm text-muted-foreground mb-4 font-mono bg-muted/30 p-3 rounded-lg overflow-x-auto">
                  {error}
                </p>
                <button
                  onClick={() => handleSubmit(matchupData)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Success State - Two column layout */}
            {(prediction || isLoading) && !error && (
              <div className="space-y-6">
                {/* Fantasy Points Card - Hero */}
                <FantasyPointsCard
                  points={fantasyPoints}
                  breakdown={pointsBreakdown}
                  scoringConfigName={scoringConfigName}
                  isLoading={isLoading}
                />

                {/* Stat Projection */}
                <StatProjection
                  position={
                    matchupData.position as "QB" | "RB" | "WR" | "TE"
                  }
                  prediction={prediction!}
                  playerName={matchupData.playerName}
                  opponentTeam={matchupData.opponentTeam}
                  isLoading={isLoading}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
