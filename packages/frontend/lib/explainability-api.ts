/**
 * Explainability API client for fetching SHAP-based prediction explanations.
 * Provides typed functions for retrieving feature contributions from the Python ML backend.
 */

import type { PredictionFeatures } from "./prediction-api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_PREDICTION_API_URL || "http://localhost:8000";

// Types for explainability responses
export interface FeatureContribution {
  feature: string;
  displayName: string;
  value: number;
  contribution: number;
  direction: "up" | "down";
}

export interface ExplainabilityResponse {
  position: string;
  target: string;
  prediction: number;
  baseValue: number;
  contributions: FeatureContribution[];
  summary: string;
}

/**
 * Fetch SHAP-based explanation for a prediction.
 *
 * @param position - Player position (QB, RB, WR, TE)
 * @param target - Prediction target (e.g., passing_yards, rushing_yards)
 * @param features - The same features used for prediction
 * @returns ExplainabilityResponse with contributions and summary, or null on error
 */
export async function fetchExplanation(
  position: string,
  target: string,
  features: PredictionFeatures
): Promise<ExplainabilityResponse | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/api/explain/${position.toLowerCase()}/${target}`,
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
      console.warn("Explainability request timed out");
      return null;
    }
    // Network error (fetch failed)
    console.warn("Could not connect to explainability API:", error);
    return null;
  } finally {
    clearTimeout(timeoutId);
  }

  // Handle HTTP errors gracefully
  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    console.warn(
      `Explainability API error (${response.status}): ${errorText}`
    );
    return null;
  }

  try {
    const data = await response.json();
    // Map snake_case response to camelCase interface
    return {
      position: data.position,
      target: data.target,
      prediction: data.prediction,
      baseValue: data.base_value,
      contributions: data.contributions.map(
        (c: {
          feature: string;
          display_name: string;
          value: number;
          contribution: number;
          direction: "up" | "down";
        }) => ({
          feature: c.feature,
          displayName: c.display_name,
          value: c.value,
          contribution: c.contribution,
          direction: c.direction,
        })
      ),
      summary: data.summary,
    };
  } catch (parseError) {
    console.warn("Failed to parse explainability response:", parseError);
    return null;
  }
}

/**
 * Get the primary prediction target for a position.
 * Used to determine which stat to explain for each position.
 */
export function getPrimaryTarget(position: string): string {
  const pos = position.toUpperCase();
  switch (pos) {
    case "QB":
      return "passing_yards";
    case "RB":
      return "rushing_yards";
    case "WR":
    case "TE":
      return "receiving_yards";
    default:
      return "passing_yards";
  }
}
