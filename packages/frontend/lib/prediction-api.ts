/**
 * Prediction API client for calling the Python ML backend.
 * Provides typed functions for fetching stat predictions by position.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_PREDICTION_API_URL || "http://localhost:8000";

// Feature types required by the prediction models (28 features)
export interface PredictionFeatures {
  // Rolling stats (8 features)
  passing_yards_roll3: number;
  passing_tds_roll3: number;
  rushing_yards_roll3: number;
  rushing_tds_roll3: number;
  carries_roll3: number;
  receiving_yards_roll3: number;
  receiving_tds_roll3: number;
  receptions_roll3: number;
  // Opponent features (5 features)
  opp_pass_defense_strength: number;
  opp_rush_defense_strength: number;
  opp_pass_yards_allowed_rank: number;
  opp_rush_yards_allowed_rank: number;
  opp_total_yards_allowed_rank: number;
  // Team strength features (3 features)
  team_points_roll3: number;
  team_yards_roll3: number;
  team_plays_roll3: number;
  // Volatility features (8 features)
  passing_yards_std3: number;
  passing_yards_cv3: number;
  rushing_yards_std3: number;
  rushing_yards_cv3: number;
  receiving_yards_std3: number;
  receiving_yards_cv3: number;
  receptions_std3: number;
  receptions_cv3: number;
  // Weather features (2 features)
  temp_normalized: number;
  wind_normalized: number;
  // Context features (2 features)
  is_home: boolean;
  is_dome: boolean;
}

// Position-specific prediction response types
export interface QBPrediction {
  passing_yards: number;
  passing_tds: number;
  interceptions: number;
  rushing_yards: number;
  rushing_tds: number;
  fumbles_lost: number;
}

export interface RBPrediction {
  rushing_yards: number;
  rushing_tds: number;
  carries: number;
  receiving_yards: number;
  receptions: number;
  receiving_tds: number;
  fumbles_lost: number;
}

export interface ReceiverPrediction {
  receiving_yards: number;
  receiving_tds: number;
  receptions: number;
  fumbles_lost: number;
}

export type Prediction = QBPrediction | RBPrediction | ReceiverPrediction;

/**
 * Create default features with position-typical rolling stats.
 * Uses neutral opponent values and configurable home/away setting.
 */
export function createDefaultFeatures(
  position: string,
  isHome: boolean
): PredictionFeatures {
  const base = {
    // Opponent features (neutral/average values)
    opp_pass_defense_strength: 1.0,
    opp_rush_defense_strength: 1.0,
    opp_pass_yards_allowed_rank: 16,
    opp_rush_yards_allowed_rank: 16,
    opp_total_yards_allowed_rank: 16,
    // Team strength (league average)
    team_points_roll3: 22.0,
    team_yards_roll3: 340.0,
    team_plays_roll3: 65.0,
    // Weather
    temp_normalized: 0.6,
    wind_normalized: 0.2,
    // Context
    is_home: isHome,
    is_dome: false,
  };

  // Position-typical rolling stats and volatility
  if (position === "QB") {
    return {
      ...base,
      passing_yards_roll3: 250,
      passing_tds_roll3: 1.8,
      rushing_yards_roll3: 15,
      rushing_tds_roll3: 0.1,
      carries_roll3: 3,
      receiving_yards_roll3: 0,
      receiving_tds_roll3: 0,
      receptions_roll3: 0,
      // QB volatility (moderate passing, low rushing)
      passing_yards_std3: 50,
      passing_yards_cv3: 0.2,
      rushing_yards_std3: 10,
      rushing_yards_cv3: 0.5,
      receiving_yards_std3: 0,
      receiving_yards_cv3: 0,
      receptions_std3: 0,
      receptions_cv3: 0,
    };
  }

  if (position === "RB") {
    return {
      ...base,
      passing_yards_roll3: 0,
      passing_tds_roll3: 0,
      rushing_yards_roll3: 65,
      rushing_tds_roll3: 0.5,
      carries_roll3: 15,
      receiving_yards_roll3: 20,
      receiving_tds_roll3: 0.1,
      receptions_roll3: 2.5,
      // RB volatility (moderate rushing, low receiving)
      passing_yards_std3: 0,
      passing_yards_cv3: 0,
      rushing_yards_std3: 25,
      rushing_yards_cv3: 0.4,
      receiving_yards_std3: 15,
      receiving_yards_cv3: 0.6,
      receptions_std3: 1.5,
      receptions_cv3: 0.5,
    };
  }

  // WR/TE default
  return {
    ...base,
    passing_yards_roll3: 0,
    passing_tds_roll3: 0,
    rushing_yards_roll3: 2,
    rushing_tds_roll3: 0,
    carries_roll3: 0.3,
    receiving_yards_roll3: 55,
    receiving_tds_roll3: 0.4,
    receptions_roll3: 4,
    // WR/TE volatility (high receiving variance)
    passing_yards_std3: 0,
    passing_yards_cv3: 0,
    rushing_yards_std3: 5,
    rushing_yards_cv3: 0.5,
    receiving_yards_std3: 30,
    receiving_yards_cv3: 0.5,
    receptions_std3: 2,
    receptions_cv3: 0.4,
  };
}

/**
 * Make a prediction request to the Python API.
 * Handles network errors, API errors, and timeouts with specific error messages.
 */
async function makePredictionRequest<T>(
  position: string,
  features: PredictionFeatures
): Promise<T> {
  // Set up 10 second timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/predict/${position.toLowerCase()}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(features),
        signal: controller.signal,
      }
    );
  } catch (error) {
    clearTimeout(timeoutId);
    // Check if it was a timeout (AbortError)
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Prediction request timed out");
    }
    // Network error (fetch failed)
    throw new Error("Could not connect to prediction API");
  } finally {
    clearTimeout(timeoutId);
  }

  // Handle HTTP errors
  if (!response.ok) {
    const errorText = await response.text();

    // 5xx server errors
    if (response.status >= 500) {
      throw new Error("Prediction service error");
    }

    // 4xx client errors - include response body
    throw new Error(
      `Prediction API error (${response.status}): ${errorText || response.statusText}`
    );
  }

  return response.json();
}

/**
 * Get QB passing stat predictions.
 */
export async function predictQB(
  features: PredictionFeatures
): Promise<QBPrediction> {
  return makePredictionRequest<QBPrediction>("qb", features);
}

/**
 * Get RB rushing/receiving stat predictions.
 */
export async function predictRB(
  features: PredictionFeatures
): Promise<RBPrediction> {
  return makePredictionRequest<RBPrediction>("rb", features);
}

/**
 * Get WR receiving stat predictions.
 */
export async function predictWR(
  features: PredictionFeatures
): Promise<ReceiverPrediction> {
  return makePredictionRequest<ReceiverPrediction>("wr", features);
}

/**
 * Get TE receiving stat predictions.
 */
export async function predictTE(
  features: PredictionFeatures
): Promise<ReceiverPrediction> {
  return makePredictionRequest<ReceiverPrediction>("te", features);
}

/**
 * Generic predict function that routes to the correct position endpoint.
 */
export async function predict(
  position: string,
  features: PredictionFeatures
): Promise<Prediction> {
  const pos = position.toUpperCase();

  switch (pos) {
    case "QB":
      return predictQB(features);
    case "RB":
      return predictRB(features);
    case "WR":
      return predictWR(features);
    case "TE":
      return predictTE(features);
    default:
      throw new Error(`Unsupported position: ${position}`);
  }
}

// =============================================================================
// Player Features API
// =============================================================================

/**
 * Response from the player features endpoint.
 * Contains computed feature values based on player's historical performance.
 */
export interface PlayerFeaturesResponse {
  player_id: string;
  player_name: string;
  position: string;
  team: string;
  games_available: number;
  features: Record<string, number | boolean>;
  has_sufficient_data: boolean;
}

/**
 * Fetch player-specific features for prediction.
 * Returns computed rolling stats and volatility based on player's actual history.
 */
export async function fetchPlayerFeatures(
  playerId: string,
  opponentTeam?: string,
  isHome: boolean = true
): Promise<PlayerFeaturesResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  const params = new URLSearchParams();
  if (opponentTeam) params.append("opponent_team", opponentTeam);
  params.append("is_home", String(isHome));

  const queryString = params.toString();
  const url = `${API_BASE_URL}/api/player/${playerId}/features${queryString ? `?${queryString}` : ""}`;

  let response: Response;

  try {
    response = await fetch(url, { signal: controller.signal });
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Player features request timed out");
    }
    throw new Error("Could not connect to player features API");
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Player not found: ${playerId}`);
    }
    throw new Error(`Player features fetch failed: ${response.statusText}`);
  }

  return response.json();
}

// =============================================================================
// Validation Metrics API
// =============================================================================

/**
 * Per-model validation metrics.
 */
export interface ModelMetrics {
  position: string;
  target: string;
  accuracy_pct: number;
  confidence: string;
  mae: number;
  rmse: number;
  r2: number;
  sample_count: number;
}

/**
 * Aggregate metrics across all models.
 */
export interface OverallMetrics {
  overall_accuracy_pct: number;
  overall_confidence: string;
  model_count: number;
}

/**
 * Response from the validation metrics endpoint.
 */
export interface ValidationResponse {
  overall: OverallMetrics;
  by_model: ModelMetrics[];
  validation_season: number;
}

/**
 * Fetch model validation metrics from the backend.
 * Used to display model confidence indicators in the UI.
 */
export async function fetchValidationMetrics(
  season: number = 2025
): Promise<ValidationResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/api/validation/metrics?season=${season}`,
      { signal: controller.signal }
    );
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Validation metrics request timed out");
    }
    throw new Error("Could not connect to validation API");
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    throw new Error(`Validation fetch failed: ${response.statusText}`);
  }

  return response.json();
}
