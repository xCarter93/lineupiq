"use client";

import { ScoringSettings } from "@/components/settings/ScoringSettings";
import { LineupSettings } from "@/components/settings/LineupSettings";

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure your fantasy scoring and lineup settings
          </p>
        </div>

        {/* Settings Sections */}
        <div className="space-y-8">
          <ScoringSettings />
          <LineupSettings />
        </div>
      </div>
    </div>
  );
}
