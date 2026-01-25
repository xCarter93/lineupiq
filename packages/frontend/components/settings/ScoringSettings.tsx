"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { StatInput } from "./StatInput";
import {
  ScoringPresetSelector,
  type ScoringPreset,
} from "./ScoringPresetSelector";
import { RotateCcw, Save, Loader2 } from "lucide-react";

interface ScoringConfig {
  preset: ScoringPreset;
  passing: {
    yardsPerPoint: number;
    tdPoints: number;
    intPoints: number;
    twoPtConversion: number;
  };
  rushing: {
    yardsPerPoint: number;
    tdPoints: number;
    twoPtConversion: number;
  };
  receiving: {
    yardsPerPoint: number;
    tdPoints: number;
    receptionPoints: number;
    twoPtConversion: number;
  };
  kicking: {
    fgPoints: number;
    fg40_49Points: number;
    fg50PlusPoints: number;
    patPoints: number;
    missPoints: number;
  };
  defense: {
    sackPoints: number;
    intPoints: number;
    fumbleRecPoints: number;
    tdPoints: number;
    safetyPoints: number;
  };
}

const defaultPresets: Record<Exclude<ScoringPreset, "custom">, ScoringConfig> = {
  standard: {
    preset: "standard",
    passing: { yardsPerPoint: 25, tdPoints: 4, intPoints: -2, twoPtConversion: 2 },
    rushing: { yardsPerPoint: 10, tdPoints: 6, twoPtConversion: 2 },
    receiving: { yardsPerPoint: 10, tdPoints: 6, receptionPoints: 0, twoPtConversion: 2 },
    kicking: { fgPoints: 3, fg40_49Points: 4, fg50PlusPoints: 5, patPoints: 1, missPoints: -1 },
    defense: { sackPoints: 1, intPoints: 2, fumbleRecPoints: 2, tdPoints: 6, safetyPoints: 2 },
  },
  half_ppr: {
    preset: "half_ppr",
    passing: { yardsPerPoint: 25, tdPoints: 4, intPoints: -2, twoPtConversion: 2 },
    rushing: { yardsPerPoint: 10, tdPoints: 6, twoPtConversion: 2 },
    receiving: { yardsPerPoint: 10, tdPoints: 6, receptionPoints: 0.5, twoPtConversion: 2 },
    kicking: { fgPoints: 3, fg40_49Points: 4, fg50PlusPoints: 5, patPoints: 1, missPoints: -1 },
    defense: { sackPoints: 1, intPoints: 2, fumbleRecPoints: 2, tdPoints: 6, safetyPoints: 2 },
  },
  full_ppr: {
    preset: "full_ppr",
    passing: { yardsPerPoint: 25, tdPoints: 4, intPoints: -2, twoPtConversion: 2 },
    rushing: { yardsPerPoint: 10, tdPoints: 6, twoPtConversion: 2 },
    receiving: { yardsPerPoint: 10, tdPoints: 6, receptionPoints: 1, twoPtConversion: 2 },
    kicking: { fgPoints: 3, fg40_49Points: 4, fg50PlusPoints: 5, patPoints: 1, missPoints: -1 },
    defense: { sackPoints: 1, intPoints: 2, fumbleRecPoints: 2, tdPoints: 6, safetyPoints: 2 },
  },
};

export function ScoringSettings() {
  const defaultConfig = useQuery(api.scoringConfigs.getDefault);
  const updateConfig = useMutation(api.scoringConfigs.update);
  const seedDefaults = useMutation(api.scoringConfigs.seedDefaults);

  const [config, setConfig] = useState<ScoringConfig>(defaultPresets.standard);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize from database
  useEffect(() => {
    if (defaultConfig) {
      setConfig({
        preset: (defaultConfig.preset as ScoringPreset) ?? "standard",
        passing: {
          yardsPerPoint: defaultConfig.passing.yardsPerPoint,
          tdPoints: defaultConfig.passing.tdPoints,
          intPoints: defaultConfig.passing.intPoints,
          twoPtConversion: defaultConfig.passing.twoPtConversion ?? 2,
        },
        rushing: {
          yardsPerPoint: defaultConfig.rushing.yardsPerPoint,
          tdPoints: defaultConfig.rushing.tdPoints,
          twoPtConversion: defaultConfig.rushing.twoPtConversion ?? 2,
        },
        receiving: {
          yardsPerPoint: defaultConfig.receiving.yardsPerPoint,
          tdPoints: defaultConfig.receiving.tdPoints,
          receptionPoints: defaultConfig.receiving.receptionPoints,
          twoPtConversion: defaultConfig.receiving.twoPtConversion ?? 2,
        },
        kicking: defaultConfig.kicking ?? defaultPresets.standard.kicking,
        defense: defaultConfig.defense ?? defaultPresets.standard.defense,
      });
      setHasChanges(false);
    }
  }, [defaultConfig]);

  // Seed defaults if none exist
  useEffect(() => {
    if (defaultConfig === null) {
      seedDefaults();
    }
  }, [defaultConfig, seedDefaults]);

  const handlePresetChange = useCallback((preset: ScoringPreset) => {
    if (preset === "custom") {
      setConfig((prev) => ({ ...prev, preset: "custom" }));
    } else {
      setConfig({ ...defaultPresets[preset], preset });
    }
    setHasChanges(true);
  }, []);

  const updateField = useCallback(
    <K extends keyof ScoringConfig>(
      category: K,
      field: keyof ScoringConfig[K],
      value: number
    ) => {
      setConfig((prev) => ({
        ...prev,
        preset: "custom" as ScoringPreset,
        [category]: {
          ...(prev[category] as object),
          [field]: value,
        },
      }));
      setHasChanges(true);
    },
    []
  );

  const handleSave = async () => {
    if (!defaultConfig) return;

    setIsSaving(true);
    try {
      await updateConfig({
        id: defaultConfig._id,
        passing: {
          yardsPerPoint: config.passing.yardsPerPoint,
          tdPoints: config.passing.tdPoints,
          intPoints: config.passing.intPoints,
        },
        rushing: {
          yardsPerPoint: config.rushing.yardsPerPoint,
          tdPoints: config.rushing.tdPoints,
        },
        receiving: {
          yardsPerPoint: config.receiving.yardsPerPoint,
          tdPoints: config.receiving.tdPoints,
          receptionPoints: config.receiving.receptionPoints,
        },
      });
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save scoring config:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setConfig(defaultPresets.standard);
    setHasChanges(true);
  };

  const isLoading = defaultConfig === undefined;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Scoring Settings</CardTitle>
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
      <CardContent className="space-y-6">
        {/* Preset Selector */}
        <div>
          <h4 className="text-sm font-medium mb-3">Scoring Format</h4>
          <ScoringPresetSelector
            value={config.preset}
            onChange={handlePresetChange}
            disabled={isSaving}
          />
        </div>

        <Separator />

        {/* Passing */}
        <div>
          <h4 className="text-sm font-medium mb-3">Passing</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatInput
              label="Yards per Point"
              value={config.passing.yardsPerPoint}
              onChange={(v) => updateField("passing", "yardsPerPoint", v)}
              suffix="yds"
              min={1}
              disabled={isSaving}
            />
            <StatInput
              label="Passing TD"
              value={config.passing.tdPoints}
              onChange={(v) => updateField("passing", "tdPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="Interception"
              value={config.passing.intPoints}
              onChange={(v) => updateField("passing", "intPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="2PT Conversion"
              value={config.passing.twoPtConversion}
              onChange={(v) => updateField("passing", "twoPtConversion", v)}
              suffix="pts"
              disabled={isSaving}
            />
          </div>
        </div>

        <Separator />

        {/* Rushing */}
        <div>
          <h4 className="text-sm font-medium mb-3">Rushing</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <StatInput
              label="Yards per Point"
              value={config.rushing.yardsPerPoint}
              onChange={(v) => updateField("rushing", "yardsPerPoint", v)}
              suffix="yds"
              min={1}
              disabled={isSaving}
            />
            <StatInput
              label="Rushing TD"
              value={config.rushing.tdPoints}
              onChange={(v) => updateField("rushing", "tdPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="2PT Conversion"
              value={config.rushing.twoPtConversion}
              onChange={(v) => updateField("rushing", "twoPtConversion", v)}
              suffix="pts"
              disabled={isSaving}
            />
          </div>
        </div>

        <Separator />

        {/* Receiving */}
        <div>
          <h4 className="text-sm font-medium mb-3">Receiving</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatInput
              label="Yards per Point"
              value={config.receiving.yardsPerPoint}
              onChange={(v) => updateField("receiving", "yardsPerPoint", v)}
              suffix="yds"
              min={1}
              disabled={isSaving}
            />
            <StatInput
              label="Receiving TD"
              value={config.receiving.tdPoints}
              onChange={(v) => updateField("receiving", "tdPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="Reception"
              value={config.receiving.receptionPoints}
              onChange={(v) => updateField("receiving", "receptionPoints", v)}
              suffix="pts"
              step={0.5}
              disabled={isSaving}
            />
            <StatInput
              label="2PT Conversion"
              value={config.receiving.twoPtConversion}
              onChange={(v) => updateField("receiving", "twoPtConversion", v)}
              suffix="pts"
              disabled={isSaving}
            />
          </div>
        </div>

        <Separator />

        {/* Kicking */}
        <div>
          <h4 className="text-sm font-medium mb-3">Kicking</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <StatInput
              label="FG (0-39 yds)"
              value={config.kicking.fgPoints}
              onChange={(v) => updateField("kicking", "fgPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="FG (40-49 yds)"
              value={config.kicking.fg40_49Points}
              onChange={(v) => updateField("kicking", "fg40_49Points", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="FG (50+ yds)"
              value={config.kicking.fg50PlusPoints}
              onChange={(v) => updateField("kicking", "fg50PlusPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="PAT"
              value={config.kicking.patPoints}
              onChange={(v) => updateField("kicking", "patPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="Miss"
              value={config.kicking.missPoints}
              onChange={(v) => updateField("kicking", "missPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
          </div>
        </div>

        <Separator />

        {/* Defense */}
        <div>
          <h4 className="text-sm font-medium mb-3">Defense</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <StatInput
              label="Sack"
              value={config.defense.sackPoints}
              onChange={(v) => updateField("defense", "sackPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="Interception"
              value={config.defense.intPoints}
              onChange={(v) => updateField("defense", "intPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="Fumble Recovery"
              value={config.defense.fumbleRecPoints}
              onChange={(v) => updateField("defense", "fumbleRecPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="Defensive TD"
              value={config.defense.tdPoints}
              onChange={(v) => updateField("defense", "tdPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
            <StatInput
              label="Safety"
              value={config.defense.safetyPoints}
              onChange={(v) => updateField("defense", "safetyPoints", v)}
              suffix="pts"
              disabled={isSaving}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
