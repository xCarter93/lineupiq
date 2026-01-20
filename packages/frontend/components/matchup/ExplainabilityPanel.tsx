"use client";

import * as React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FeatureContributionBar } from "./FeatureContributionBar";

interface Contribution {
  feature: string;
  displayName: string;
  value: number;
  contribution: number;
  direction: "up" | "down";
}

interface ExplainabilityPanelProps {
  position: string;
  target: string;
  prediction: number;
  baseValue: number;
  contributions: Contribution[];
  summary: string;
  isLoading?: boolean;
  defaultExpanded?: boolean;
}

// Number of top contributions to show before "Show more"
const TOP_CONTRIBUTIONS_COUNT = 5;

// Format target name for display (e.g., "passing_yards" -> "Passing Yards")
function formatTarget(target: string): string {
  return target
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Panel displaying SHAP-based feature contributions for a prediction.
 *
 * Shows natural language summary, top contributing features with bars,
 * and expandable section for full feature list.
 */
export function ExplainabilityPanel({
  position,
  target,
  prediction,
  baseValue,
  contributions,
  summary,
  isLoading = false,
  defaultExpanded = false,
}: ExplainabilityPanelProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  // Sort contributions by absolute value (most impactful first)
  const sortedContributions = React.useMemo(() => {
    return [...contributions].sort(
      (a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)
    );
  }, [contributions]);

  // Split into top and remaining
  const topContributions = sortedContributions.slice(0, TOP_CONTRIBUTIONS_COUNT);
  const remainingContributions = sortedContributions.slice(TOP_CONTRIBUTIONS_COUNT);

  // Calculate max contribution for bar scaling
  const maxContribution = React.useMemo(() => {
    if (contributions.length === 0) return 1;
    return Math.max(...contributions.map((c) => Math.abs(c.contribution)));
  }, [contributions]);

  // Loading skeleton
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <div className="h-5 w-48 bg-muted/30 rounded animate-pulse" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-4 w-full bg-muted/30 rounded animate-pulse mb-4" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="h-4 w-32 bg-muted/30 rounded animate-pulse" />
                <div className="flex-1 h-3 bg-muted/30 rounded-full animate-pulse" />
                <div className="h-4 w-12 bg-muted/30 rounded animate-pulse" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const targetDisplay = formatTarget(target);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Why {prediction.toFixed(1)} {targetDisplay}?
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Summary text */}
        <p className="text-sm text-muted-foreground mb-4">{summary}</p>

        {/* Top contribution bars */}
        <div className="space-y-2">
          {topContributions.map((c) => (
            <FeatureContributionBar
              key={c.feature}
              displayName={c.displayName}
              contribution={c.contribution}
              maxContribution={maxContribution}
              value={c.value}
            />
          ))}
        </div>

        {/* Expand button for remaining contributions */}
        {!expanded && remainingContributions.length > 0 && (
          <Button
            variant="ghost"
            className="mt-4 w-full text-muted-foreground hover:text-foreground"
            onClick={() => setExpanded(true)}
          >
            Show {remainingContributions.length} more factor
            {remainingContributions.length !== 1 ? "s" : ""}
          </Button>
        )}

        {/* Expanded contributions */}
        {expanded && remainingContributions.length > 0 && (
          <div className="space-y-2 mt-4 pt-4 border-t border-border">
            {remainingContributions.map((c) => (
              <FeatureContributionBar
                key={c.feature}
                displayName={c.displayName}
                contribution={c.contribution}
                maxContribution={maxContribution}
                value={c.value}
              />
            ))}
            <Button
              variant="ghost"
              className="mt-2 w-full text-muted-foreground hover:text-foreground"
              onClick={() => setExpanded(false)}
            >
              Show less
            </Button>
          </div>
        )}

        {/* Base value info */}
        <p className="text-xs text-muted-foreground mt-4 pt-4 border-t border-border">
          Base prediction: {baseValue.toFixed(1)} {targetDisplay.toLowerCase()} (league average)
        </p>
      </CardContent>
    </Card>
  );
}
