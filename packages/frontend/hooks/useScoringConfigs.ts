"use client";

import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";

/**
 * Hook returning all scoring configs
 *
 * @example
 * const { configs, isLoading } = useScoringConfigs();
 */
export function useScoringConfigs() {
  const configs = useQuery(api.scoringConfigs.list);
  return {
    configs,
    isLoading: configs === undefined,
  };
}

/**
 * Hook returning the default scoring config
 *
 * @example
 * const { config, isLoading } = useDefaultScoringConfig();
 */
export function useDefaultScoringConfig() {
  const config = useQuery(api.scoringConfigs.getDefault);
  return {
    config,
    isLoading: config === undefined,
  };
}

/**
 * Hook returning mutation functions for scoring config CRUD operations
 *
 * @example
 * const { create, update, remove, setDefault, seedDefaults } = useScoringConfigMutations();
 *
 * // Create a new config
 * await create({
 *   name: "Custom",
 *   passing: { yardsPerPoint: 25, tdPoints: 4, intPoints: -2 },
 *   rushing: { yardsPerPoint: 10, tdPoints: 6 },
 *   receiving: { yardsPerPoint: 10, tdPoints: 6, receptionPoints: 0.5 },
 *   isDefault: false,
 * });
 *
 * // Update an existing config
 * await update({ id: configId, name: "Updated Name" });
 *
 * // Set a config as default
 * await setDefault({ id: configId });
 *
 * // Remove a config (cannot remove default)
 * await remove({ id: configId });
 */
export function useScoringConfigMutations() {
  const create = useMutation(api.scoringConfigs.create);
  const update = useMutation(api.scoringConfigs.update);
  const remove = useMutation(api.scoringConfigs.remove);
  const setDefault = useMutation(api.scoringConfigs.setDefault);
  const seedDefaults = useMutation(api.scoringConfigs.seedDefaults);

  return {
    create,
    update,
    remove,
    setDefault,
    seedDefaults,
  };
}
