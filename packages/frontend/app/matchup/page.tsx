"use client";

import { useState } from "react";
import { SectionLabel } from "@/components/ui/section-label";
import { MatchupForm, MatchupData } from "@/components/matchup/MatchupForm";

export default function MatchupPage() {
  const [matchupData, setMatchupData] = useState<MatchupData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (matchup: MatchupData) => {
    setIsLoading(true);
    // Store matchup data and log to console (prediction display in 09-03)
    console.log("Matchup submitted:", matchup);
    setMatchupData(matchup);
    // Simulate loading state for UI feedback
    setTimeout(() => {
      setIsLoading(false);
    }, 500);
  };

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

        {/* Results Section - placeholder for 09-03 */}
        {matchupData && !isLoading && (
          <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
            <SectionLabel className="mb-4 block">MATCHUP CONFIGURED</SectionLabel>
            <p className="text-foreground">
              <span className="font-semibold">{matchupData.playerName}</span>
              <span className="text-muted-foreground"> ({matchupData.position})</span>
              {" vs "}
              <span className="font-semibold">{matchupData.opponentTeam}</span>
              {" "}
              <span className="text-muted-foreground">
                (Week {matchupData.week}, {matchupData.season})
              </span>
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {matchupData.isHome ? "Home" : "Away"} game
            </p>
            <div className="mt-4 p-4 bg-muted/20 rounded-lg border border-border/30">
              <p className="text-sm text-muted-foreground">
                Prediction results will be displayed here in the next phase (09-03).
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
