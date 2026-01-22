"use client";

import { Badge } from "@/components/ui/badge";

interface PositionTabsProps {
  selectedPosition: string | null;
  onPositionSelect: (position: string | null) => void;
  playerCounts: Record<string, number>;
}

const POSITIONS = [
  { value: null, label: "All", color: "bg-muted text-muted-foreground" },
  { value: "QB", label: "QB", color: "bg-blue-100 text-blue-700" },
  { value: "RB", label: "RB", color: "bg-emerald-100 text-emerald-700" },
  { value: "WR", label: "WR", color: "bg-purple-100 text-purple-700" },
  { value: "TE", label: "TE", color: "bg-orange-100 text-orange-700" },
  { value: "K", label: "K", color: "bg-yellow-100 text-yellow-700" },
  { value: "DEF", label: "DEF", color: "bg-red-100 text-red-700" },
];

export function PositionTabs({ selectedPosition, onPositionSelect, playerCounts }: PositionTabsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {POSITIONS.map((pos) => {
        const isSelected = selectedPosition === pos.value;
        const count = pos.value === null
          ? Object.values(playerCounts).reduce((sum, c) => sum + c, 0)
          : playerCounts[pos.value] || 0;

        return (
          <button
            key={pos.label}
            onClick={() => onPositionSelect(pos.value)}
            className={`
              px-4 py-2 rounded-lg font-medium transition-all
              ${isSelected
                ? "bg-primary text-primary-foreground shadow-md scale-105"
                : "bg-white hover:bg-muted"
              }
            `}
          >
            <span className="mr-2">{pos.label}</span>
            <Badge variant="secondary" className="ml-1">{count}</Badge>
          </button>
        );
      })}
    </div>
  );
}
