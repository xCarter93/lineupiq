"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Plus, Trash2, RotateCcw, Save, Loader2, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

interface Slot {
  position: string;
  eligiblePositions: string[];
}

const POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"];
const FLEX_POSITIONS = ["RB", "WR", "TE"];

const DEFAULT_SLOTS: Slot[] = [
  { position: "QB", eligiblePositions: ["QB"] },
  { position: "RB", eligiblePositions: ["RB"] },
  { position: "RB", eligiblePositions: ["RB"] },
  { position: "WR", eligiblePositions: ["WR"] },
  { position: "WR", eligiblePositions: ["WR"] },
  { position: "TE", eligiblePositions: ["TE"] },
  { position: "FLEX", eligiblePositions: ["RB", "WR", "TE"] },
  { position: "K", eligiblePositions: ["K"] },
  { position: "DEF", eligiblePositions: ["DEF"] },
];

interface SlotRowProps {
  slot: Slot;
  index: number;
  onUpdate: (index: number, slot: Slot) => void;
  onRemove: (index: number) => void;
  disabled?: boolean;
}

function SlotRow({ slot, index, onUpdate, onRemove, disabled }: SlotRowProps) {
  const isFlex = slot.position === "FLEX";

  const handlePositionChange = (newPosition: string) => {
    if (newPosition === "FLEX") {
      onUpdate(index, { position: "FLEX", eligiblePositions: FLEX_POSITIONS });
    } else {
      onUpdate(index, { position: newPosition, eligiblePositions: [newPosition] });
    }
  };

  const handleFlexToggle = (pos: string) => {
    if (!isFlex) return;
    const newEligible = slot.eligiblePositions.includes(pos)
      ? slot.eligiblePositions.filter((p) => p !== pos)
      : [...slot.eligiblePositions, pos];
    if (newEligible.length > 0) {
      onUpdate(index, { ...slot, eligiblePositions: newEligible });
    }
  };

  return (
    <div className="flex items-center gap-3 py-2 px-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
      <GripVertical className="h-4 w-4 text-muted-foreground/50 cursor-grab" />

      <div className="w-8 text-center text-xs text-muted-foreground font-medium">
        {index + 1}
      </div>

      <Select
        value={slot.position}
        onValueChange={handlePositionChange}
        disabled={disabled}
      >
        <SelectTrigger className="w-24 h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {POSITIONS.map((pos) => (
            <SelectItem key={pos} value={pos}>
              {pos}
            </SelectItem>
          ))}
          <SelectItem value="FLEX">FLEX</SelectItem>
        </SelectContent>
      </Select>

      {isFlex ? (
        <div className="flex-1 flex items-center gap-1.5">
          {FLEX_POSITIONS.map((pos) => (
            <Badge
              key={pos}
              variant={slot.eligiblePositions.includes(pos) ? "default" : "outline"}
              className={cn(
                "cursor-pointer transition-colors",
                slot.eligiblePositions.includes(pos)
                  ? "bg-primary/80 hover:bg-primary"
                  : "hover:bg-muted"
              )}
              onClick={() => !disabled && handleFlexToggle(pos)}
            >
              {pos}
            </Badge>
          ))}
        </div>
      ) : (
        <div className="flex-1">
          <Badge variant="secondary">{slot.eligiblePositions.join(", ")}</Badge>
        </div>
      )}

      <Button
        variant="ghost"
        size="icon-sm"
        onClick={() => onRemove(index)}
        disabled={disabled}
        className="text-muted-foreground hover:text-destructive"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}

export function LineupSettings() {
  const settings = useQuery(api.lineupSettings.get);
  const updateSettings = useMutation(api.lineupSettings.update);
  const resetSettings = useMutation(api.lineupSettings.resetToDefaults);

  const [slots, setSlots] = useState<Slot[]>(DEFAULT_SLOTS);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize from database
  useEffect(() => {
    if (settings?.slots) {
      setSlots(settings.slots);
      setHasChanges(false);
    }
  }, [settings]);

  const handleUpdate = (index: number, slot: Slot) => {
    const newSlots = [...slots];
    newSlots[index] = slot;
    setSlots(newSlots);
    setHasChanges(true);
  };

  const handleRemove = (index: number) => {
    setSlots(slots.filter((_, i) => i !== index));
    setHasChanges(true);
  };

  const handleAdd = () => {
    setSlots([...slots, { position: "FLEX", eligiblePositions: FLEX_POSITIONS }]);
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateSettings({ slots });
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save lineup settings:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    setIsSaving(true);
    try {
      await resetSettings();
      setSlots(DEFAULT_SLOTS);
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to reset lineup settings:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const isLoading = settings === undefined;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  // Count positions
  const positionCounts = slots.reduce(
    (acc, slot) => {
      acc[slot.position] = (acc[slot.position] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Lineup Configuration</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Configure your starting lineup slots
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={isSaving}
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
              Reset
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
            >
              {isSaving ? (
                <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
              ) : (
                <Save className="h-3.5 w-3.5 mr-1.5" />
              )}
              Save
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Position Summary */}
        <div className="flex flex-wrap gap-2 pb-2">
          {Object.entries(positionCounts).map(([pos, count]) => (
            <Badge key={pos} variant="secondary" className="text-xs">
              {count} {pos}
            </Badge>
          ))}
          <Badge variant="outline" className="text-xs">
            {slots.length} Total
          </Badge>
        </div>

        {/* Slot List */}
        <div className="space-y-2">
          {slots.map((slot, index) => (
            <SlotRow
              key={index}
              slot={slot}
              index={index}
              onUpdate={handleUpdate}
              onRemove={handleRemove}
              disabled={isSaving}
            />
          ))}
        </div>

        {/* Add Slot Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleAdd}
          disabled={isSaving}
          className="w-full"
        >
          <Plus className="h-3.5 w-3.5 mr-1.5" />
          Add Slot
        </Button>
      </CardContent>
    </Card>
  );
}
