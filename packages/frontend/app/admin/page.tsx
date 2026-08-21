"use client";

import { useState } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useRosterSync } from "@/hooks/useRosterSync";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCurrentSeason } from "@/lib/season";

export default function AdminPage() {
  const { status, syncRoster } = useRosterSync();
  const currentSeason = getCurrentSeason();
  const players = useQuery(api.players.list);
  const [lastResult, setLastResult] = useState<string | null>(null);

  const handleSyncRoster = async () => {
    try {
      const result = await syncRoster();
      setLastResult(`Imported ${result.playersImported} players. Errors: ${result.errors.length}`);
    } catch (e) {
      setLastResult(`Error: ${e instanceof Error ? e.message : "Unknown"}`);
    }
  };

  const playerCount = players?.length ?? 0;
  const positions = players?.reduce((acc, p) => {
    acc[p.position] = (acc[p.position] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) ?? {};

  return (
    <div className="grid gap-6">
        {/* Current State */}
        <Card>
          <CardHeader>
            <CardTitle>Current Roster</CardTitle>
            <CardDescription>Players currently stored in Convex</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold mb-4">{playerCount}</div>
            <div className="grid grid-cols-5 gap-2 text-sm text-muted-foreground">
              {Object.entries(positions).map(([pos, count]) => (
                <div key={pos}>
                  {pos}: {count}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Sync Controls */}
        <Card>
          <CardHeader>
            <CardTitle>Roster Sync</CardTitle>
            <CardDescription>
              Import current NFL roster from nflreadpy via API
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleSyncRoster}
              disabled={status.isLoading}
              className="w-full"
            >
              {status.isLoading ? "Syncing..." : `Sync ${currentSeason} Roster`}
            </Button>

            {status.isLoading && (
              <div className="space-y-2">
                <div className="w-full bg-secondary rounded-full h-2.5">
                  <div
                    className="bg-primary h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${status.progress}%` }}
                  />
                </div>
                <p className="text-sm text-muted-foreground">{status.message}</p>
              </div>
            )}

            {status.error && (
              <p className="text-sm text-red-600">{status.error}</p>
            )}

            {lastResult && !status.isLoading && (
              <p className="text-sm text-green-600">{lastResult}</p>
            )}
          </CardContent>
        </Card>

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>Usage</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none">
            <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
              <li>Ensure Python API is running: <code className="bg-muted px-1 py-0.5 rounded">cd packages/backend && uv run uvicorn lineupiq.api.main:app</code></li>
              <li>Click &quot;Sync {currentSeason} Roster&quot; to import ~500 fantasy-relevant players</li>
              <li>Players will be available in the matchup player selector</li>
              <li>Historical stats are synced on-demand when viewing player details</li>
            </ol>
          </CardContent>
        </Card>
    </div>
  );
}
