import { httpRouter, type FunctionArgs } from "convex/server";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

type PredictionRows = FunctionArgs<
  typeof internal.predictions.upsertBatch
>["rows"];

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

function secretMatches(provided: string, expected: string): boolean {
  if (provided.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < provided.length; i++) {
    diff |= provided.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return diff === 0;
}

// Ingest endpoint for the weekly Python prediction job.
// Auth: `Authorization: Bearer <PREDICTIONS_INGEST_SECRET>`.
// Body: {"rows": [...]} — see internal.predictions.upsertBatch for the row shape.
// Unlike /api/mutation (which returns 200 even on function error), the status
// code here is authoritative: any failure is non-2xx.
const ingestPredictions = httpAction(async (ctx, request) => {
  const expected = process.env.PREDICTIONS_INGEST_SECRET;
  if (!expected) {
    return json({ error: "PREDICTIONS_INGEST_SECRET is not configured" }, 500);
  }

  const authorization = request.headers.get("Authorization") ?? "";
  const provided = authorization.startsWith("Bearer ")
    ? authorization.slice("Bearer ".length)
    : "";
  if (!secretMatches(provided, expected)) {
    return json({ error: "Unauthorized" }, 401);
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Body is not valid JSON" }, 400);
  }

  const rows = (body as { rows?: unknown })?.rows;
  if (!Array.isArray(rows)) {
    return json({ error: "Expected body {\"rows\": [...]}" }, 400);
  }

  try {
    // The mutation's argument validator is what actually vets each row; a bad
    // row throws here and surfaces as a 500 rather than a silent success.
    const counts = await ctx.runMutation(internal.predictions.upsertBatch, {
      rows: rows as PredictionRows,
    });
    return json(counts, 200);
  } catch (error) {
    return json({ error: String(error) }, 500);
  }
});

const http = httpRouter();

http.route({
  path: "/ingest-predictions",
  method: "POST",
  handler: ingestPredictions,
});

export default http;
