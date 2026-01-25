"use client";

import { useState, useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Search, Plus, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface AddPlayerSheetProps {
  isOpen: boolean;
  onClose: () => void;
  eligiblePositions: string[];
  slotPosition: string;
  rosteredPlayerIds: string[];
  onSelectPlayer: (playerId: string) => void;
}

export function AddPlayerSheet({
  isOpen,
  onClose,
  eligiblePositions,
  slotPosition,
  rosteredPlayerIds,
  onSelectPlayer,
}: AddPlayerSheetProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const allPlayers = useQuery(api.players.list) ?? [];

  // Filter to eligible positions
  const eligiblePlayers = useMemo(() => {
    let filtered = allPlayers.filter((p) =>
      eligiblePositions.includes(p.position)
    );

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.team?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [allPlayers, eligiblePositions, searchQuery]);

  const handleSelect = (playerId: string) => {
    onSelectPlayer(playerId);
    onClose();
    setSearchQuery("");
  };

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-lg overflow-y-auto"
      >
        <SheetHeader className="pb-4">
          <SheetTitle>Add Player to {slotPosition}</SheetTitle>
          <SheetDescription>
            Select from eligible {eligiblePositions.join("/")} players
          </SheetDescription>
        </SheetHeader>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search players..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Player List */}
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead>Player</TableHead>
                <TableHead className="w-[80px] text-right">Proj</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {eligiblePlayers.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={3}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No eligible players found
                  </TableCell>
                </TableRow>
              ) : (
                eligiblePlayers.map((player) => {
                  const isRostered = rosteredPlayerIds.includes(player.playerId);
                  const initials = player.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("");
                  // Mock projected points - would come from real data
                  const positionPts: Record<string, number> = {
                    QB: 20.5,
                    RB: 14.5,
                    WR: 15.0,
                    TE: 11.5,
                    K: 8.0,
                    DEF: 7.5,
                  };
                  const projected = positionPts[player.position] ?? 12;

                  return (
                    <TableRow
                      key={player.playerId}
                      className={cn(
                        isRostered && "opacity-50 bg-muted/30"
                      )}
                    >
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar
                            src={player.headshotUrl}
                            alt={player.name}
                            fallback={initials}
                            size="sm"
                          />
                          <div>
                            <div className="font-medium">{player.name}</div>
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Badge
                                variant="secondary"
                                className="text-[10px] px-1"
                              >
                                {player.position}
                              </Badge>
                              <span>{player.team}</span>
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="font-medium">
                          {projected.toFixed(1)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {isRostered ? (
                          <Badge variant="secondary" className="text-xs">
                            <Check className="h-3 w-3 mr-1" />
                            In Lineup
                          </Badge>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleSelect(player.playerId)}
                          >
                            <Plus className="h-3.5 w-3.5" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </SheetContent>
    </Sheet>
  );
}
