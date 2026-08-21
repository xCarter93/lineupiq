"use client";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { SourceMix } from "@/lib/prediction-points";

const DOT_STYLES: Record<SourceMix, string> = {
  model: "bg-primary/70",
  mixed: "bg-muted-foreground/60",
  baseline: "border border-muted-foreground/50",
};

function describe(
  mix: SourceMix,
  modelCount?: number,
  baselineCount?: number
): string {
  if (mix === "mixed" && modelCount !== undefined && baselineCount !== undefined) {
    return `${modelCount} stat${modelCount === 1 ? "" : "s"} from model prediction, ${baselineCount} from recent-form average`;
  }
  return mix === "model" ? "model prediction" : "recent-form average";
}

/**
 * Quiet marker for where a displayed number came from. Single-stat surfaces
 * pass "model" or "baseline"; a rolled-up fantasy total passes "mixed" with
 * counts so the tooltip can say how the split falls.
 */
export function PredictionSourceDot({
  mix,
  modelCount,
  baselineCount,
  className,
}: {
  mix: SourceMix;
  modelCount?: number;
  baselineCount?: number;
  className?: string;
}) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            aria-label={describe(mix, modelCount, baselineCount)}
            className={cn(
              "inline-block size-1.5 shrink-0 rounded-full align-middle",
              DOT_STYLES[mix],
              className
            )}
          />
        </TooltipTrigger>
        <TooltipContent className="text-xs tracking-wide">
          {describe(mix, modelCount, baselineCount)}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
