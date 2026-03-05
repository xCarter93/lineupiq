"use client";

import { DashboardHeroCards } from "@/components/dashboard/DashboardHeroCards";
import { PlayerPerformanceChart } from "@/components/dashboard/PlayerPerformanceChart";
import { PositionContributionChart } from "@/components/dashboard/PositionContributionChart";
import { WeeklyTrendChart } from "@/components/dashboard/WeeklyTrendChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ArrowRight, Users, Settings } from "lucide-react";
import { useSimulation } from "@/hooks/useSimulation";

// Mock data - in production this would come from Convex
const mockPlayerPerformance = [
  { player: "Josh Allen", actual: 24.5, predicted: 22.8, position: "QB" },
  { player: "Derrick Henry", actual: 18.2, predicted: 19.5, position: "RB" },
  { player: "Ja'Marr Chase", actual: 21.3, predicted: 18.7, position: "WR" },
  { player: "Travis Kelce", actual: 14.8, predicted: 15.2, position: "TE" },
  { player: "Bijan Robinson", actual: 16.5, predicted: 17.1, position: "RB" },
  { player: "Tyreek Hill", actual: 19.2, predicted: 20.5, position: "WR" },
];

const mockPositionContribution = [
  { position: "QB", points: 24.5, percentage: 22 },
  { position: "RB", points: 34.7, percentage: 31 },
  { position: "WR", points: 40.5, percentage: 36 },
  { position: "TE", points: 12.3, percentage: 11 },
];

const mockWeeklyTrend = [
  { week: "Week 14", predicted: 105.2, actual: 98.5 },
  { week: "Week 15", predicted: 112.3, actual: 115.8 },
  { week: "Week 16", predicted: 108.7, actual: 102.3 },
  { week: "Week 17", predicted: 118.5, actual: 121.2 },
  { week: "Week 18", predicted: 115.8, actual: 110.5 },
];

export default function Page() {
  const simulation = useSimulation();

  // Mock data for hero cards
  const projectedPoints = 118.5;
  const lastWeekAccuracy = 92.3;
  const seasonTrend = 2.8;

  // Get week display based on simulation state
  const weekDisplay = simulation.isActive
    ? simulation.completedWeeks === 0
      ? "Pre-Season"
      : `Week ${simulation.currentWeek}`
    : `Week ${simulation.currentWeek}`;

  const seasonDisplay = `${simulation.targetSeason} Season`;

  // Get training data display
  const trainingDataDisplay = simulation.isActive
    ? simulation.completedWeeks === 0
      ? simulation.trainingSeasons.filter(s => s < simulation.targetSeason).join("-")
      : `${simulation.trainingSeasons[0]}-${simulation.targetSeason} (through Wk ${simulation.completedWeeks})`
    : "2022-2025";

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              {weekDisplay}, {seasonDisplay}
              {simulation.isActive && (
                <Badge variant="outline" className="ml-2 text-xs">
                  Simulation
                </Badge>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href="/settings">
                <Settings className="h-4 w-4 mr-1.5" />
                Settings
              </Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/lineup">
                <Users className="h-4 w-4 mr-1.5" />
                Edit Lineup
              </Link>
            </Button>
          </div>
        </div>

        {/* Hero Cards */}
        <div className="mb-8">
          <DashboardHeroCards
            projectedPoints={projectedPoints}
            lastWeekAccuracy={lastWeekAccuracy}
            seasonTrend={seasonTrend}
          />
        </div>

        {/* Charts Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Player Performance - Takes 2 columns */}
          <div className="lg:col-span-2">
            <PlayerPerformanceChart data={mockPlayerPerformance} />
          </div>

          {/* Position Contribution */}
          <div className="lg:col-span-1">
            <PositionContributionChart data={mockPositionContribution} />
          </div>
        </div>

        {/* Second Row */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Weekly Trend */}
          <WeeklyTrendChart data={mockWeeklyTrend} />

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Link
                href="/players"
                className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div>
                  <p className="font-medium">Browse Players</p>
                  <p className="text-sm text-muted-foreground">
                    Search and analyze player projections
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </Link>

              <Link
                href="/lineup"
                className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div>
                    <p className="font-medium">My Lineup</p>
                    <p className="text-sm text-muted-foreground">
                      Manage your starting roster
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">7/9 filled</Badge>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
              </Link>

              <Link
                href="/settings"
                className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div>
                  <p className="font-medium">Configure Scoring</p>
                  <p className="text-sm text-muted-foreground">
                    Customize your league settings
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Model Info Footer */}
        <Card className="bg-muted/30">
          <CardContent className="py-4">
            <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-muted-foreground">Models: </span>
                  <span className="font-medium">32 LightGBM</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Training Data: </span>
                  <span className="font-medium">{trainingDataDisplay}</span>
                </div>
                {!simulation.isActive && (
                  <div>
                    <span className="text-muted-foreground">Last Updated: </span>
                    <span className="font-medium">Jan 24, 2026</span>
                  </div>
                )}
              </div>
              <Badge variant="outline">Powered by LineupIQ ML</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
