"use client";

import { useSimulation } from "@/hooks/useSimulation";
import { useSidebar } from "./sidebar-context";
import { Badge } from "@/components/ui/badge";
import { PlayCircle } from "lucide-react";
import Link from "next/link";

export function SidebarSimulationStatus() {
  const { isActive, currentWeek, status, isBusy, completedWeeks } = useSimulation();
  const { isCollapsed } = useSidebar();

  if (!isActive) {
    return null;
  }

  if (isCollapsed) {
    return (
      <div className="px-2 py-2">
        <Link
          href="/admin/simulation"
          className="flex items-center justify-center p-2 rounded-lg bg-primary/10 hover:bg-primary/20 transition-colors"
          title={`Simulation Mode: Week ${currentWeek}`}
        >
          <PlayCircle className="h-5 w-5 text-primary" />
        </Link>
      </div>
    );
  }

  return (
    <div className="px-3 py-2">
      <Link
        href="/admin/simulation"
        className="block p-3 rounded-lg bg-primary/10 hover:bg-primary/20 transition-colors"
      >
        <div className="flex items-center gap-2 mb-1">
          <PlayCircle className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-primary">Simulation Mode</span>
          {isBusy && (
            <Badge variant="secondary" className="text-xs px-1.5 py-0">
              {status}
            </Badge>
          )}
        </div>
        <div className="text-xs text-muted-foreground">
          Showing <span className="font-medium text-foreground">Week {currentWeek}</span>
          {completedWeeks > 0 && (
            <span> • {completedWeeks} weeks trained</span>
          )}
        </div>
      </Link>
    </div>
  );
}
