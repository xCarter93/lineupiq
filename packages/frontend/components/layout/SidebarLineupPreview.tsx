"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { cn } from "@/lib/utils";
import { getCurrentSeason } from "@/lib/season";
import { useSidebar } from "./sidebar-context";

export function SidebarLineupPreview() {
  const [isOpen, setIsOpen] = useState(true);
  const { isCollapsed } = useSidebar();

  // Week is still pinned to 1 - will be dynamic later
  const lineup = useQuery(api.lineups.getByWeek, {
    week: 1,
    season: getCurrentSeason(),
  });

  if (isCollapsed) {
    return null;
  }

  // Calculate filled slots and projected points
  const filledSlots =
    lineup?.slots.filter((slot) => slot.playerId).length ?? 0;
  const totalSlots = lineup?.slots.length ?? 9;
  const projectedPoints = lineup?.totalProjectedPoints ?? 0;

  // Get slot summary
  const slotSummary = lineup?.slots.reduce(
    (acc, slot) => {
      if (slot.playerId) {
        acc[slot.position] = (acc[slot.position] ?? 0) + 1;
      }
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="px-2">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-sidebar-accent/50 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            My Lineup
          </span>
        </div>
        <span className="text-xs text-muted-foreground">
          {filledSlots}/{totalSlots}
        </span>
      </button>

      {isOpen && (
        <div className="px-3 py-2 animate-in fade-in slide-in-from-top-1 duration-200">
          {/* Projected Points */}
          <div className="flex items-baseline justify-between mb-3">
            <span className="text-xs text-muted-foreground">Projected</span>
            <span className="text-lg font-bold text-primary">
              {projectedPoints.toFixed(1)}
              <span className="text-xs font-normal text-muted-foreground ml-1">
                pts
              </span>
            </span>
          </div>

          {/* Slot Summary */}
          {slotSummary && Object.keys(slotSummary).length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(slotSummary).map(([position, count]) => (
                <span
                  key={position}
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full font-medium",
                    "bg-primary/10 text-primary"
                  )}
                >
                  {count} {position}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              No players added yet
            </p>
          )}
        </div>
      )}
    </div>
  );
}
