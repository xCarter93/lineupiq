# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-15)

**Core value:** Accurate stat-level predictions from well-engineered features and properly trained models.
**Current focus:** v1.1 Model Confidence

## Current Position

Phase: 13 of 17 (K/DEF Models + Training Improvements)
Plan: 4 of 8 in current phase
Status: In progress
Last activity: 2026-01-15 — Completed 13-04-PLAN.md (Complete Fantasy Scoring Config)

Progress: █████░░░░░ 50% (Phase 13 in progress)

## Performance Metrics

**Velocity (v1.0 MVP):**
- Total plans completed: 30
- Average duration: 8.4 min
- Total execution time: 4.2 hours

**By Phase (v1.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 3/3 | 15.5 min | 5.2 min |
| 02-data-pipeline | 2/2 | 5 min | 2.5 min |
| 03-data-processing | 3/3 | 10 min | 3.3 min |
| 04-feature-engineering | 3/3 | 6 min | 2.0 min |
| 05-model-development | 4/4 | 79 min | 19.8 min |
| 06-model-evaluation | 3/3 | 49 min | 16.3 min |
| 07-prediction-api | 3/3 | 30 min | 10.0 min |
| 08-convex-backend | 3/3 | 20 min | 6.7 min |
| 09-matchup-ui | 3/3 | 25 min | 8.3 min |
| 10-integration-polish | 3/3 | 32 min | 10.7 min |

## Accumulated Context

### Decisions

**v1.1 Decisions:**

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 11 | Prediction intervals highest priority | MAPIE CQR provides guarantees with ~100 LOC |
| 11 | LightGBM before ensembles | 7x speedup enables experimentation first |
| 11 | Defer KNN imputation | A/B test after baseline improvements |
| 12 | Separate modelMetrics/overallMetrics tables | Efficient queries for different access patterns |
| 12 | Split conformal over MAPIE wrapper | Works with existing trained models without retraining |
| 12 | 90% confidence intervals (alpha=0.1) | Informative bounds without excessive uncertainty |
| 12 | Accuracy % formula: 100*(1-MAE/mean) | Intuitive 0-100% scale for user trust |
| 12 | Three-tier confidence (High/Med/Low) | Simple user-facing metric based on R2 + accuracy |
| 12 | Convex-first with API fallback | Hook checks Convex cache first, fetches from API if null |
| 12 | ModelConfidence in page.tsx not form | MatchupForm is input-only, results render in page |
| 13 | LightGBM as default, keep XGBoost option | 7x speed + flexibility for comparison |
| 13 | Team-level defense (not individual) | Fantasy uses team DST, not individual defenders |
| 13 | Kicker predictions: FG by distance + XP | Match ESPN scoring granularity |
| 13 | Bundle audit improvements with K/DEF | Train everything together for consistency |
| 13-03 | Team defense uses schedule for points_allowed | nflreadpy team_stats lacks this field |
| 13-03 | FG buckets match ESPN scoring (0-39, 40-49, 50+) | Aligns with fantasy point tiers |
| 13-04 | ESPN Standard as default scoring | Industry standard, widely recognized |
| 13-04 | Expected value for kicker scoring | Accounts for success probability in predictions |
| 13-04 | 75% success rate for 50+ yard FGs | NFL average lower for long-distance attempts |
| 13-02 | Shift(1) for rolling feature leakage prevention | Only prior games used, never current game |
| 13-02 | CV (coeff of variation) for normalized volatility | Identifies boom/bust players across stat scales |

**v1.0 Decisions:** See .planning/milestones/v1.0-ROADMAP.md

### Roadmap Evolution

- v1.0 MVP shipped: Foundation through polish, 10 phases (2026-01-15)
- Milestone v1.1 created: Model Confidence, 7 phases (Phase 11-17)

### Pending Todos

None — milestone just created.

### Blockers/Concerns

None — ready to begin planning.

## Session Continuity

Last session: 2026-01-15
Stopped at: Completed 13-02-PLAN.md (Team Strength & Volatility Features)
Resume file: None
Next action: Continue Wave 2 plans (13-05, 13-06, 13-07) or Wave 3 (13-08)
