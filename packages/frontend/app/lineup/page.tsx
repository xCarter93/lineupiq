"use client";

import { LineupEditor } from "@/components/lineup/LineupEditor";

export default function LineupPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold">My Lineup</h1>
          <p className="text-muted-foreground mt-1">
            Build and manage your fantasy lineup
          </p>
        </div>

        {/* Lineup Editor */}
        <LineupEditor week={1} season={2025} />
      </div>
    </div>
  );
}
