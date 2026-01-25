"use client";

import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Target, BarChart3, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeroCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    direction: "up" | "down" | "neutral";
  };
  icon: React.ReactNode;
  variant?: "default" | "primary";
}

function HeroCard({
  title,
  value,
  subtitle,
  trend,
  icon,
  variant = "default",
}: HeroCardProps) {
  return (
    <Card
      className={cn(
        variant === "primary" && "bg-primary text-primary-foreground"
      )}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p
              className={cn(
                "text-sm font-medium",
                variant === "primary"
                  ? "text-primary-foreground/80"
                  : "text-muted-foreground"
              )}
            >
              {title}
            </p>
            <p className="text-3xl font-bold">{value}</p>
            {subtitle && (
              <p
                className={cn(
                  "text-xs",
                  variant === "primary"
                    ? "text-primary-foreground/70"
                    : "text-muted-foreground"
                )}
              >
                {subtitle}
              </p>
            )}
            {trend && (
              <div
                className={cn(
                  "flex items-center gap-1 text-sm",
                  trend.direction === "up" && "text-green-600",
                  trend.direction === "down" && "text-red-500",
                  trend.direction === "neutral" && "text-muted-foreground",
                  variant === "primary" && "text-primary-foreground/80"
                )}
              >
                {trend.direction === "up" && <TrendingUp className="h-4 w-4" />}
                {trend.direction === "down" && (
                  <TrendingDown className="h-4 w-4" />
                )}
                <span>
                  {trend.direction === "up" ? "+" : ""}
                  {trend.value.toFixed(1)}%
                </span>
              </div>
            )}
          </div>
          <div
            className={cn(
              "p-2 rounded-lg",
              variant === "primary" ? "bg-primary-foreground/10" : "bg-muted"
            )}
          >
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface DashboardHeroCardsProps {
  projectedPoints: number;
  lastWeekAccuracy: number;
  seasonTrend: number;
}

export function DashboardHeroCards({
  projectedPoints,
  lastWeekAccuracy,
  seasonTrend,
}: DashboardHeroCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <HeroCard
        title="This Week's Projection"
        value={projectedPoints.toFixed(1)}
        subtitle="Total lineup points"
        icon={<Target className="h-5 w-5 text-primary" />}
        variant="primary"
      />
      <HeroCard
        title="Last Week's Accuracy"
        value={`${lastWeekAccuracy.toFixed(1)}%`}
        subtitle="Predicted vs actual"
        trend={{
          value: lastWeekAccuracy > 85 ? 5.2 : -3.1,
          direction: lastWeekAccuracy > 85 ? "up" : "down",
        }}
        icon={<BarChart3 className="h-5 w-5 text-muted-foreground" />}
      />
      <HeroCard
        title="Season Trend"
        value={seasonTrend > 0 ? `+${seasonTrend.toFixed(1)}` : seasonTrend.toFixed(1)}
        subtitle="Average weekly change"
        trend={{
          value: Math.abs(seasonTrend),
          direction: seasonTrend > 0 ? "up" : "down",
        }}
        icon={<Activity className="h-5 w-5 text-muted-foreground" />}
      />
    </div>
  );
}
