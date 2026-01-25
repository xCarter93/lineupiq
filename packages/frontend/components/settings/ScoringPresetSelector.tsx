"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type ScoringPreset = "standard" | "half_ppr" | "full_ppr" | "custom";

interface ScoringPresetSelectorProps {
  value: ScoringPreset;
  onChange: (preset: ScoringPreset) => void;
  disabled?: boolean;
}

const presetLabels: Record<ScoringPreset, string> = {
  standard: "Standard",
  half_ppr: "Half PPR",
  full_ppr: "Full PPR",
  custom: "Custom",
};

const presetDescriptions: Record<ScoringPreset, string> = {
  standard: "No points per reception",
  half_ppr: "0.5 points per reception",
  full_ppr: "1 point per reception",
  custom: "Custom scoring settings",
};

export function ScoringPresetSelector({
  value,
  onChange,
  disabled = false,
}: ScoringPresetSelectorProps) {
  return (
    <div className="space-y-2">
      <Select
        value={value}
        onValueChange={(v) => onChange(v as ScoringPreset)}
        disabled={disabled}
      >
        <SelectTrigger className="w-full max-w-xs">
          <SelectValue placeholder="Select scoring format" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="standard">
            <div className="flex flex-col items-start">
              <span>{presetLabels.standard}</span>
              <span className="text-xs text-muted-foreground">
                {presetDescriptions.standard}
              </span>
            </div>
          </SelectItem>
          <SelectItem value="half_ppr">
            <div className="flex flex-col items-start">
              <span>{presetLabels.half_ppr}</span>
              <span className="text-xs text-muted-foreground">
                {presetDescriptions.half_ppr}
              </span>
            </div>
          </SelectItem>
          <SelectItem value="full_ppr">
            <div className="flex flex-col items-start">
              <span>{presetLabels.full_ppr}</span>
              <span className="text-xs text-muted-foreground">
                {presetDescriptions.full_ppr}
              </span>
            </div>
          </SelectItem>
          <SelectItem value="custom">
            <div className="flex flex-col items-start">
              <span>{presetLabels.custom}</span>
              <span className="text-xs text-muted-foreground">
                {presetDescriptions.custom}
              </span>
            </div>
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

export { presetLabels, presetDescriptions };
