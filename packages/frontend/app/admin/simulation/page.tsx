"use client";

import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  type ColumnDef,
  type SortingState,
  useTable,
} from "@tanstack/react-table";
import {
  DataGrid,
  DataGridContainer,
  dataGridFeatures,
  type DataGridFeatures,
} from "@/components/reui/data-grid/data-grid";
import { DataGridColumnHeader } from "@/components/reui/data-grid/data-grid-column-header";
import { DataGridScrollArea } from "@/components/reui/data-grid/data-grid-scroll-area";
import { DataGridTableVirtual } from "@/components/reui/data-grid/data-grid-table-virtual";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/reui/alert";
import { AlertTriangle, Loader2 } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { getCurrentSeason, getDefaultTrainingSeasons } from "@/lib/season";

// Backend API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SimulationState {
  name: string;
  target_season: number;
  training_seasons: number[];
  current_week: number;
  status: string;
  last_trained_at: string | null;
}

interface SimulationStatus {
  state: SimulationState | null;
  predictions: Record<string, number> | null;
  message: string;
}

interface Prediction {
  player_id: string;
  player_name: string;
  position: string;
  team: string;
  opponent: string;
  week: number;
  passing_yards?: number;
  rushing_yards?: number;
  receiving_yards?: number;
  passing_tds?: number;
  rushing_tds?: number;
  receiving_tds?: number;
  [key: string]: string | number | undefined;
}

export default function SimulationPage() {
  const targetSeason = getCurrentSeason();
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number>(1);
  const [selectedPosition, setSelectedPosition] = useState<string>("all");
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loadingPredictions, setLoadingPredictions] = useState(false);
  const [predictionSorting, setPredictionSorting] = useState<SortingState>([]);

  // Convex mutations to sync state
  const initializeSimulation = useMutation(api.simulation.initializeSimulation);
  const advanceWeek = useMutation(api.simulation.advanceWeek);
  const resetSimulation = useMutation(api.simulation.resetSimulation);

  // Convex state
  const convexState = useQuery(api.simulation.getSimulationState, {
    targetSeason,
  });

  // Fetch status from backend
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/simulation/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        setError(null);

        // Sync to Convex if state exists
        if (data.state && convexState === null) {
          try {
            await initializeSimulation({
              targetSeason: data.state.target_season,
              trainingSeasons: data.state.training_seasons,
              name: data.state.name,
            });
          } catch {
            // Ignore if already exists
          }
        }
      } else {
        const errorData = await res.json();
        setError(errorData.detail || "Failed to fetch status");
      }
    } catch (e) {
      setError(`Connection error: ${e instanceof Error ? e.message : "Unknown"}`);
    }
  };

  // Fetch predictions for selected week
  const fetchPredictions = async (week: number, position?: string) => {
    setLoadingPredictions(true);
    try {
      const posParam = position && position !== "all" ? `&position=${position}` : "";
      const res = await fetch(
        `${API_BASE}/api/simulation/predictions/${week}?${posParam}`
      );
      if (res.ok) {
        const data = await res.json();
        setPredictions(data.predictions || []);
      } else {
        setPredictions([]);
      }
    } catch {
      setPredictions([]);
    } finally {
      setLoadingPredictions(false);
    }
  };

  // Load status on mount and poll
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Load predictions when week/position changes
  useEffect(() => {
    if (status?.state) {
      fetchPredictions(selectedWeek, selectedPosition);
    }
  }, [selectedWeek, selectedPosition, status?.state?.current_week]);

  // Initialize simulation
  const handleInit = async (quick: boolean = false) => {
    setIsLoading(true);
    setError(null);
    try {
      // Create in Convex first
      await initializeSimulation({
        targetSeason,
        trainingSeasons: getDefaultTrainingSeasons(targetSeason),
      });

      // Then trigger backend
      const res = await fetch(`${API_BASE}/api/simulation/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_season: targetSeason, quick }),
      });
      if (res.ok) {
        await fetchStatus();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to initialize");
      }
    } catch (e) {
      setError(`Error: ${e instanceof Error ? e.message : "Unknown"}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Advance simulation
  const handleAdvance = async (toWeek: number, quick: boolean = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/simulation/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to_week: toWeek, quick }),
      });
      if (res.ok) {
        // Update Convex
        try {
          await advanceWeek({ targetSeason, toWeek });
        } catch {
          // Ignore sync errors
        }
        await fetchStatus();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to advance");
      }
    } catch (e) {
      setError(`Error: ${e instanceof Error ? e.message : "Unknown"}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Reset simulation
  const handleReset = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulation/reset`, {
        method: "POST",
      });
      if (res.ok) {
        try {
          await resetSimulation({ targetSeason });
        } catch {
          // Ignore sync errors
        }
        await fetchStatus();
      }
    } finally {
      setIsLoading(false);
    }
  };

  const state = status?.state;
  // current_week in state = the week we're ON (predicting)
  // completedWeeks = weeks with actual data = current_week - 1
  const currentWeek = state?.current_week ?? 1;
  const completedWeeks = Math.max(0, currentWeek - 1);
  const nextWeek = currentWeek + 1;  // Next week to advance to
  const isBusy = state?.status !== "ready";

  // The "app week" is the current week we're predicting
  const appWeek = currentWeek;

  // Prefer the season/training set the running simulation actually reports
  const simSeason = state?.target_season ?? targetSeason;
  const trainingSeasons =
    state?.training_seasons ?? getDefaultTrainingSeasons(targetSeason);

  // Status badge variant
  const getStatusVariant = (s: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (s) {
      case "ready":
        return "default";
      case "training":
      case "predicting":
      case "advancing":
        return "secondary";
      default:
        return "outline";
    }
  };

  const predictionColumns = useMemo<
    ColumnDef<DataGridFeatures, Prediction>[]
  >(() => {
    const numericMeta = {
      headerClassName: "text-right *:justify-end",
      cellClassName: "text-right",
    };
    return [
      {
        accessorKey: "player_name",
        id: "player_name",
        header: ({ column }) => (
          <DataGridColumnHeader title="Player" column={column} />
        ),
        cell: ({ row }) => (
          <span className="font-medium">{row.original.player_name}</span>
        ),
        minSize: 160,
        meta: { autoSize: true },
      },
      {
        accessorKey: "position",
        id: "position",
        header: ({ column }) => (
          <DataGridColumnHeader title="Pos" column={column} />
        ),
        cell: ({ row }) => row.original.position,
        size: 80,
      },
      {
        accessorKey: "team",
        id: "team",
        header: ({ column }) => (
          <DataGridColumnHeader title="Team" column={column} />
        ),
        cell: ({ row }) => row.original.team,
        size: 80,
      },
      {
        accessorKey: "opponent",
        id: "opponent",
        header: ({ column }) => (
          <DataGridColumnHeader title="Opp" column={column} />
        ),
        cell: ({ row }) => row.original.opponent,
        size: 80,
      },
      {
        accessorKey: "passing_yards",
        id: "passing_yards",
        header: ({ column }) => (
          <DataGridColumnHeader title="Pass Yds" column={column} />
        ),
        cell: ({ row }) => row.original.passing_yards ?? "-",
        size: 100,
        meta: numericMeta,
      },
      {
        accessorKey: "rushing_yards",
        id: "rushing_yards",
        header: ({ column }) => (
          <DataGridColumnHeader title="Rush Yds" column={column} />
        ),
        cell: ({ row }) => row.original.rushing_yards ?? "-",
        size: 100,
        meta: numericMeta,
      },
      {
        accessorKey: "receiving_yards",
        id: "receiving_yards",
        header: ({ column }) => (
          <DataGridColumnHeader title="Rec Yds" column={column} />
        ),
        cell: ({ row }) => row.original.receiving_yards ?? "-",
        size: 100,
        meta: numericMeta,
      },
      {
        id: "total_tds",
        accessorFn: (row: Prediction) =>
          (Number(row.passing_tds) || 0) +
          (Number(row.rushing_tds) || 0) +
          (Number(row.receiving_tds) || 0),
        header: ({ column }) => (
          <DataGridColumnHeader title="TDs" column={column} />
        ),
        cell: ({ row }) => {
          const totalTds =
            (Number(row.original.passing_tds) || 0) +
            (Number(row.original.rushing_tds) || 0) +
            (Number(row.original.receiving_tds) || 0);
          return totalTds > 0 ? totalTds.toFixed(1) : "-";
        },
        size: 80,
        meta: numericMeta,
      },
    ];
  }, []);

  const predictionTable = useTable({
    features: dataGridFeatures,
    // The virtualizer renders every prediction, so opt out of the bundled
    // paginated row model that would otherwise slice to 10 rows.
    manualPagination: true,
    columns: predictionColumns,
    data: predictions,
    getRowId: (row: Prediction) => `${row.player_id}-${row.week}`,
    state: { sorting: predictionSorting },
    onSortingChange: setPredictionSorting,
  });

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertTitle>Simulation backend error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Simulation Status Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Simulation State</CardTitle>
              {state && (
                <Badge variant={getStatusVariant(state.status)}>
                  {state.status}
                </Badge>
              )}
            </div>
            <CardDescription>
              {state ? state.name : "No simulation initialized"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {state ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Predicting</p>
                    <p className="text-2xl font-bold text-primary">
                      Week {currentWeek}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Completed Weeks</p>
                    <p className="text-2xl font-bold">
                      {completedWeeks === 0 ? "None" : `1-${completedWeeks}`}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Training Data</p>
                    <p className="font-medium">
                      {state.training_seasons.join(", ")}
                      {completedWeeks > 0 && (
                        <span className="text-primary"> + {simSeason} W1-{completedWeeks}</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Last Trained</p>
                    <p className="font-medium">
                      {state.last_trained_at
                        ? new Date(state.last_trained_at).toLocaleString()
                        : "Never"}
                    </p>
                  </div>
                </div>

                {/* Week Timeline */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Season Progress</p>
                  <div className="flex gap-0.5">
                    {Array.from({ length: 18 }, (_, i) => i + 1).map((week) => (
                      <div
                        key={week}
                        className={`h-8 flex-1 rounded-sm flex items-center justify-center text-xs font-medium transition-colors ${
                          week <= completedWeeks
                            ? "bg-green-500 text-white"
                            : week === currentWeek
                            ? "bg-blue-500 text-white animate-pulse"
                            : "bg-muted text-muted-foreground"
                        }`}
                        title={`Week ${week}${week <= completedWeeks ? " (completed)" : week === currentWeek ? " (predicting)" : ""}`}
                      >
                        {week}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">
                Initialize a simulation to begin backtesting the {targetSeason} season.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Controls Card */}
        <Card>
          <CardHeader>
            <CardTitle>Controls</CardTitle>
            <CardDescription>
              Manage the simulation lifecycle
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!state ? (
              <div className="space-y-2">
                <Button
                  onClick={() => handleInit(false)}
                  disabled={isLoading}
                  className="w-full"
                  size="lg"
                >
                  {isLoading
                    ? "Initializing..."
                    : `Initialize ${targetSeason} Simulation`}
                </Button>
                <Button
                  onClick={() => handleInit(true)}
                  disabled={isLoading}
                  variant="outline"
                  className="w-full"
                >
                  Quick Init (10 trials, faster)
                </Button>
                <p className="text-xs text-muted-foreground text-center">
                  Full init trains 30 trials per model (~45 min total)
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <Button
                  onClick={() => handleAdvance(nextWeek, false)}
                  disabled={isLoading || isBusy || nextWeek > 18}
                  className="w-full"
                  size="lg"
                >
                  {isBusy
                    ? `${state.status}...`
                    : nextWeek > 18
                    ? "Season Complete"
                    : `Advance to Week ${nextWeek}`}
                </Button>
                <Button
                  onClick={() => handleAdvance(nextWeek, true)}
                  disabled={isLoading || isBusy || nextWeek > 18}
                  variant="outline"
                  className="w-full"
                >
                  Quick Advance (10 trials)
                </Button>

                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      disabled={isLoading || isBusy}
                      variant="destructive"
                      className="w-full"
                    >
                      Reset Simulation
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Reset Simulation?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will reset the simulation to week 0 (pre-season).
                        Prediction files will be kept but the app will show week 1 predictions.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={handleReset}>
                        Reset
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            )}

            {isBusy && (
              <Alert variant="info">
                <Loader2 className="animate-spin" />
                <AlertTitle>Processing — status: {state?.status}</AlertTitle>
                <AlertDescription>
                  This may take several minutes. Page will auto-refresh.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>How Simulation Mode Works</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            <strong>Predicting Week {currentWeek}:</strong> Models are trained on{" "}
            {trainingSeasons[0]}-{trainingSeasons[trainingSeasons.length - 1]}
            {completedWeeks > 0 && ` + weeks 1-${completedWeeks} of ${simSeason}`}.
            The app displays predictions for week {currentWeek}.
          </p>
          <p>
            <strong>Completed Weeks ({completedWeeks}):</strong> These weeks have actual data
            that was used to train the models. You can compare predictions vs actuals for these weeks.
          </p>
          <p>
            <strong>Advancing to Week {nextWeek}:</strong> Week {currentWeek} actuals are added to training,
            models are retrained, and predictions for weeks {nextWeek}-18 are regenerated.
          </p>
        </CardContent>
      </Card>

      {/* Predictions Preview */}
      {state && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Week Predictions Preview</CardTitle>
                <CardDescription>
                  Browse predictions for any week
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Select
                  value={selectedWeek.toString()}
                  onValueChange={(v) => setSelectedWeek(parseInt(v))}
                >
                  <SelectTrigger className="w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.from({ length: 18 }, (_, i) => i + 1).map((week) => (
                      <SelectItem key={week} value={week.toString()}>
                        Week {week}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select
                  value={selectedPosition}
                  onValueChange={setSelectedPosition}
                >
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="QB">QB</SelectItem>
                    <SelectItem value="RB">RB</SelectItem>
                    <SelectItem value="WR">WR</SelectItem>
                    <SelectItem value="TE">TE</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <DataGrid
              table={predictionTable}
              recordCount={predictions.length}
              isLoading={loadingPredictions}
              emptyMessage="No predictions available. Initialize and run the simulation first."
              tableLayout={{ dense: true, headerSticky: true }}
              tableClassNames={{ headerSticky: "sticky top-0 z-10 bg-card" }}
            >
              <DataGridContainer className="rounded-lg border">
                <DataGridScrollArea className="max-h-80" orientation="vertical">
                  <DataGridTableVirtual estimateSize={37} />
                </DataGridScrollArea>
              </DataGridContainer>
            </DataGrid>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
