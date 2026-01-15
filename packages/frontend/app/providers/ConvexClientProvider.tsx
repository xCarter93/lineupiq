"use client";

import { ConvexProvider, ConvexReactClient, useMutation } from "convex/react";
import { ReactNode, useEffect } from "react";
import { api } from "@/convex/_generated/api";

const convex = new ConvexReactClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

/**
 * Component that seeds default scoring configs on first load.
 * The seedDefaults mutation is idempotent - only creates configs if none exist.
 * Renders null (no UI).
 */
function SeedDefaults() {
  const seedDefaults = useMutation(api.scoringConfigs.seedDefaults);

  useEffect(() => {
    seedDefaults();
  }, [seedDefaults]);

  return null;
}

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  return (
    <ConvexProvider client={convex}>
      <SeedDefaults />
      {children}
    </ConvexProvider>
  );
}
