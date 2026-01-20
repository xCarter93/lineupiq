"use client";

import { useState, useRef } from "react";
import { SectionLabel } from "@/components/ui/section-label";
import { CollapsibleSection } from "@/components/ui/collapsible-section";
import { MatchupForm, MatchupData } from "@/components/matchup/MatchupForm";
import { StatProjection } from "@/components/matchup/StatProjection";
import { FantasyPointsCard } from "@/components/matchup/FantasyPointsCard";
import { ExplainabilityPanel } from "@/components/matchup/ExplainabilityPanel";
import {
  predict,
  createDefaultFeatures,
  fetchPlayerFeatures,
  type Prediction,
  type PredictionFeatures,
} from "@/lib/prediction-api";
import {
  fetchExplanation,
  getPrimaryTarget,
  type ExplainabilityResponse,
} from "@/lib/explainability-api";
import {
  calculateFantasyPoints,
  getPointsBreakdown,
  type ScoringConfig,
  type PointsBreakdown,
} from "@/lib/fantasy-points";
import { useDefaultScoringConfig } from "@/hooks/useScoringConfigs";
import { useModelMetrics } from "@/hooks/useModelMetrics";
import { ModelConfidence } from "@/components/matchup/ModelConfidence";
import { PlayerHistory } from "@/components/matchup/PlayerHistory";

// Default scoring config (PPR) as fallback while Convex loads
const DEFAULT_SCORING_CONFIG: ScoringConfig = {
  passing: { yardsPerPoint: 25, tdPoints: 4, intPoints: -2 },
  rushing: { yardsPerPoint: 10, tdPoints: 6 },
  receiving: { yardsPerPoint: 10, tdPoints: 6, receptionPoints: 1 }, // Full PPR
};

export default function MatchupPage() {
  const [matchupData, setMatchupData] = useState<MatchupData | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explanationData, setExplanationData] =
    useState<ExplainabilityResponse | null>(null);
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);

  // Keep track of features for explanation requests
  const featuresRef = useRef<PredictionFeatures | null>(null);

  // Get default scoring config from Convex
  const { config: convexConfig } = useDefaultScoringConfig();

  // Get model metrics for confidence display
  const {
    overallAccuracy,
    overallConfidence,
    isLoading: metricsLoading,
  } = useModelMetrics();

  // Use Convex config if available and has PPR, otherwise use PPR default
  // This ensures receptions count toward fantasy points
  const scoringConfig: ScoringConfig = convexConfig && convexConfig.receiving.receptionPoints > 0
    ? {
        passing: convexConfig.passing,
        rushing: convexConfig.rushing,
        receiving: convexConfig.receiving,
      }
    : DEFAULT_SCORING_CONFIG;

  // Show PPR if using default config (with receptions), otherwise show Convex config name
  const scoringConfigName = convexConfig && convexConfig.receiving.receptionPoints > 0
    ? convexConfig.name
    : "PPR";

  // Clear projections when player changes
  const handlePlayerChange = () => {
    setPrediction(null);
    setMatchupData(null);
    setExplanationData(null);
    setError(null);
  };

  const handleSubmit = async (matchup: MatchupData) => {
    setIsLoading(true);
    setError(null);
    setMatchupData(matchup);
    setPrediction(null);
    setExplanationData(null);

    try {
      // Fetch player-specific features from their historical data
      let features: PredictionFeatures;

      try {
        const playerFeatures = await fetchPlayerFeatures(
          matchup.playerId,
          matchup.opponentTeam,
          matchup.isHome
        );

        // Start with position defaults as base
        const defaults = createDefaultFeatures(matchup.position, matchup.isHome);

        // Merge player-specific features on top (overrides defaults for stats they have)
        features = {
          ...defaults,
          // Override with player's actual stats for the fields that exist
          passing_yards_roll3:
            (playerFeatures.features.passing_yards_roll3 as number) ??
            defaults.passing_yards_roll3,
          passing_tds_roll3:
            (playerFeatures.features.passing_tds_roll3 as number) ??
            defaults.passing_tds_roll3,
          rushing_yards_roll3:
            (playerFeatures.features.rushing_yards_roll3 as number) ??
            defaults.rushing_yards_roll3,
          rushing_tds_roll3:
            (playerFeatures.features.rushing_tds_roll3 as number) ??
            defaults.rushing_tds_roll3,
          carries_roll3:
            (playerFeatures.features.carries_roll3 as number) ??
            defaults.carries_roll3,
          receiving_yards_roll3:
            (playerFeatures.features.receiving_yards_roll3 as number) ??
            defaults.receiving_yards_roll3,
          receiving_tds_roll3:
            (playerFeatures.features.receiving_tds_roll3 as number) ??
            defaults.receiving_tds_roll3,
          receptions_roll3:
            (playerFeatures.features.receptions_roll3 as number) ??
            defaults.receptions_roll3,
          // Volatility features
          passing_yards_std3:
            (playerFeatures.features.passing_yards_std3 as number) ??
            defaults.passing_yards_std3,
          passing_yards_cv3:
            (playerFeatures.features.passing_yards_cv3 as number) ??
            defaults.passing_yards_cv3,
          rushing_yards_std3:
            (playerFeatures.features.rushing_yards_std3 as number) ??
            defaults.rushing_yards_std3,
          rushing_yards_cv3:
            (playerFeatures.features.rushing_yards_cv3 as number) ??
            defaults.rushing_yards_cv3,
          receiving_yards_std3:
            (playerFeatures.features.receiving_yards_std3 as number) ??
            defaults.receiving_yards_std3,
          receiving_yards_cv3:
            (playerFeatures.features.receiving_yards_cv3 as number) ??
            defaults.receiving_yards_cv3,
          receptions_std3:
            (playerFeatures.features.receptions_std3 as number) ??
            defaults.receptions_std3,
          receptions_cv3:
            (playerFeatures.features.receptions_cv3 as number) ??
            defaults.receptions_cv3,
          // Keep home/away from matchup
          is_home: matchup.isHome,
        };
      } catch (featureErr) {
        // Fallback to position defaults if player features unavailable
        console.warn(
          "Player features unavailable, using position defaults:",
          featureErr
        );
        features = createDefaultFeatures(matchup.position, matchup.isHome);
      }

      // Store features for explanation request
      featuresRef.current = features;

      const result = await predict(matchup.position, features);
      setPrediction(result);

      // Fetch explanation for the primary stat after prediction succeeds
      setIsLoadingExplanation(true);
      const primaryTarget = getPrimaryTarget(matchup.position);
      const explanation = await fetchExplanation(
        matchup.position,
        primaryTarget,
        features
      );
      setExplanationData(explanation);
      setIsLoadingExplanation(false);
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
      setIsLoadingExplanation(false);
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

  const hasResults = prediction || isLoading || error;

  return (
    <div className="min-h-screen">
      <div className="max-w-[1600px] mx-auto px-6 lg:px-10 py-12">
        {/* Hero Section */}
        <div className="mb-8">
          <SectionLabel className="mb-4 block">MATCHUP SIMULATOR</SectionLabel>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-3">
            Build Your Matchup
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Select a player and opponent to see ML-powered stat projections
          </p>
        </div>

        {/* Master-Detail Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Form + Primary Results */}
          <div className="space-y-6">
            {/* Matchup Form */}
            <MatchupForm
              onSubmit={handleSubmit}
              onPlayerChange={handlePlayerChange}
              isLoading={isLoading}
            />

            {/* Error State */}
            {error && !isLoading && (
              <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-destructive animate-in fade-in duration-300">
                <SectionLabel className="mb-3 block">ERROR</SectionLabel>
                <p className="text-destructive font-medium mb-2">
                  Failed to get prediction
                </p>
                <p className="text-sm text-muted-foreground mb-4 font-mono bg-muted/30 p-3 rounded-lg overflow-x-auto">
                  {error}
                </p>
                <button
                  onClick={() => matchupData && handleSubmit(matchupData)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Primary Results: Fantasy Points Hero */}
            {(prediction || isLoading) && !error && matchupData && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                <FantasyPointsCard
                  points={fantasyPoints}
                  breakdown={pointsBreakdown}
                  scoringConfigName={scoringConfigName}
                  isLoading={isLoading}
                  playerHeadshotUrl={matchupData.playerHeadshotUrl}
                  playerName={matchupData.playerName}
                />
              </div>
            )}
          </div>

          {/* Right Column: Detail Sections (collapsible) */}
          <div className="space-y-4">
            {/* Only show when we have results */}
            {hasResults && matchupData && !error && (
              <>
                {/* Model Confidence - always visible */}
                <div className="bg-white rounded-xl shadow-sm px-4 py-3 flex items-center justify-between animate-in fade-in duration-300">
                  <span className="text-sm text-muted-foreground">
                    Model Performance
                  </span>
                  <ModelConfidence
                    accuracyPct={overallAccuracy}
                    confidence={overallConfidence}
                    isLoading={metricsLoading}
                  />
                </div>

                {/* Stat Breakdown */}
                <CollapsibleSection
                  title="Stat Projections"
                  badge={matchupData.position}
                  defaultOpen={false}
                  className="animate-in fade-in slide-in-from-right-2 duration-300 delay-75"
                >
                  <StatProjection
                    position={matchupData.position as "QB" | "RB" | "WR" | "TE"}
                    prediction={prediction!}
                    playerName={matchupData.playerName}
                    opponentTeam={matchupData.opponentTeam}
                    isLoading={isLoading}
                    compact
                  />
                </CollapsibleSection>

                {/* Why This Projection */}
                <CollapsibleSection
                  title="Why This Projection?"
                  badge="SHAP"
                  defaultOpen={false}
                  className="animate-in fade-in slide-in-from-right-2 duration-300 delay-150"
                >
                  <ExplainabilityPanel
                    position={matchupData.position}
                    target={getPrimaryTarget(matchupData.position)}
                    prediction={explanationData?.prediction ?? fantasyPoints}
                    baseValue={explanationData?.baseValue ?? 0}
                    contributions={explanationData?.contributions ?? []}
                    summary={
                      explanationData?.summary ??
                      "Loading prediction explanation..."
                    }
                    isLoading={isLoadingExplanation}
                    compact
                  />
                </CollapsibleSection>

                {/* Recent Performance */}
                <CollapsibleSection
                  title="Recent Performance"
                  badge="History"
                  defaultOpen={false}
                  className="animate-in fade-in slide-in-from-right-2 duration-300 delay-200"
                >
                  <PlayerHistory
                    playerId={matchupData.playerId}
                    playerName={matchupData.playerName}
                    position={matchupData.position as "QB" | "RB" | "WR" | "TE"}
                    compact
                  />
                </CollapsibleSection>
              </>
            )}

            {/* Empty state for right column when no results */}
            {!hasResults && (
              <div className="hidden lg:block bg-white/50 rounded-xl border-2 border-dashed border-muted p-8 text-center animate-in fade-in duration-300">
                <p className="text-muted-foreground">
                  Select a player and get a prediction to see detailed analysis
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
