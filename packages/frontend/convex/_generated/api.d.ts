/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as modelMetrics from "../modelMetrics.js";
import type * as playerHistory from "../playerHistory.js";
import type * as players from "../players.js";
import type * as predictions from "../predictions.js";
import type * as scoringConfigs from "../scoringConfigs.js";
import type * as seedPlayers from "../seedPlayers.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  modelMetrics: typeof modelMetrics;
  playerHistory: typeof playerHistory;
  players: typeof players;
  predictions: typeof predictions;
  scoringConfigs: typeof scoringConfigs;
  seedPlayers: typeof seedPlayers;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
