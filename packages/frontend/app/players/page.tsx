"use client";

import { SectionLabel } from "@/components/ui/section-label";
import { PlayerRepository } from "@/components/players/PlayerRepository";
import { Badge } from "@/components/ui/badge";
import { useSimulation } from "@/hooks/useSimulation";

export default function PlayersPage() {
  const simulation = useSimulation();

  // Get description based on simulation state
  const getDescription = () => {
    if (simulation.isActive) {
      if (simulation.completedWeeks === 0) {
        return `View player statistics from the ${simulation.trainingSeasons.filter(s => s < simulation.targetSeason).join(", ")} seasons. The ${simulation.targetSeason} season has not started yet.`;
      }
      return `Explore predicted vs actual stats through Week ${simulation.completedWeeks}. See how our ML models are performing against ${simulation.targetSeason} season data.`;
    }
    return `Explore predicted vs actual stats for all NFL players. Select a player to see week-by-week validation of our ML models against ${simulation.targetSeason} season data.`;
  };

  return (
    <div className="min-h-screen">
      <div className="max-w-[1800px] mx-auto px-6 lg:px-10 py-12">
        {/* Hero Section */}
        <div className="mb-8">
          <SectionLabel className="mb-4 block">PLAYER LOOKUP</SectionLabel>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-3">
            {simulation.targetSeason} Player Performance
            {simulation.isActive && (
              <Badge variant="outline" className="ml-3 text-sm align-middle">
                Simulation
              </Badge>
            )}
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            {getDescription()}
          </p>
        </div>

        {/* Player Repository Component */}
        <PlayerRepository />
      </div>
    </div>
  );
}
