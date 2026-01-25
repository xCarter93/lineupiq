"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Plus, X, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface LineupSlotProps {
  position: string;
  eligiblePositions: string[];
  playerId?: string;
  projectedPoints?: number;
  onAddClick: () => void;
  onRemoveClick: () => void;
}

export function LineupSlot({
  position,
  eligiblePositions,
  playerId,
  projectedPoints = 0,
  onAddClick,
  onRemoveClick,
}: LineupSlotProps) {
  // Fetch player details if filled
  const player = useQuery(
    api.players.getByPlayerId,
    playerId ? { playerId } : "skip"
  );

  const isFlex = position === "FLEX";
  const isEmpty = !playerId;

  if (isEmpty) {
    return (
      <Card
        className={cn(
          "flex items-center justify-between p-4 border-2 border-dashed",
          "hover:border-primary/50 hover:bg-muted/30 transition-colors cursor-pointer"
        )}
        onClick={onAddClick}
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
            <User className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-muted-foreground">
                {position}
              </span>
              {isFlex && (
                <span className="text-xs text-muted-foreground">
                  ({eligiblePositions.join("/")})
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">Click to add player</p>
          </div>
        </div>
        <Button variant="outline" size="sm">
          <Plus className="h-3.5 w-3.5 mr-1.5" />
          Add
        </Button>
      </Card>
    );
  }

  // Filled state
  const initials = player?.name
    .split(" ")
    .map((n) => n[0])
    .join("");

  return (
    <Card className="flex items-center justify-between p-4">
      <div className="flex items-center gap-4">
        <Avatar
          src={player?.headshotUrl}
          alt={player?.name ?? "Player"}
          fallback={initials ?? "?"}
          size="md"
        />
        <div>
          <div className="flex items-center gap-2">
            <span className="font-semibold">{player?.name ?? "Loading..."}</span>
            <Badge variant="secondary" className="text-xs">
              {player?.position ?? position}
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>{player?.team ?? "---"}</span>
            <span>•</span>
            <span>vs. OPP</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <div className="text-lg font-bold text-primary">
            {projectedPoints.toFixed(1)}
          </div>
          <div className="text-xs text-muted-foreground">projected</div>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={(e) => {
            e.stopPropagation();
            onRemoveClick();
          }}
          className="text-muted-foreground hover:text-destructive"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}
