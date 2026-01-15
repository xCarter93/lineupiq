"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PositionFilterProps {
  selected: string;
  onSelect: (position: string) => void;
}

const POSITIONS = ["All", "QB", "RB", "WR", "TE"] as const;

export function PositionFilter({ selected, onSelect }: PositionFilterProps) {
  return (
    <div className="flex gap-2">
      {POSITIONS.map((position) => {
        const isSelected = selected.toLowerCase() === position.toLowerCase();
        return (
          <Button
            key={position}
            variant={isSelected ? "default" : "ghost"}
            size="sm"
            className={cn(
              "rounded-full transition-all",
              !isSelected && "hover:bg-muted"
            )}
            onClick={() => onSelect(position.toLowerCase())}
          >
            {position}
          </Button>
        );
      })}
    </div>
  );
}
