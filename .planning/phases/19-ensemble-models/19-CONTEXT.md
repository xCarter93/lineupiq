# Phase 19: Ensemble Models - Context

**Gathered:** 2026-01-20
**Status:** Ready for research

<vision>
## How This Should Work

Ensemble models should combine LightGBM + XGBoost predictions to deliver the most accurate predictions possible. The key is proving that the ensemble actually beats single models through rigorous backtesting — not just assuming it's better.

If the ensemble wins in backtesting (lower MAE, higher R2 on holdout data), it becomes the default prediction engine. The user doesn't want to guess or assume ensembles are better — they want clear metrics showing improvement.

The approach should be evidence-based: benchmark multiple ensemble strategies (simple averaging, weighted blending, stacking) and choose based on performance, not preference.

</vision>

<essential>
## What Must Be Nailed

- **Prove ensemble beats single models** - Clear backtesting results showing ensemble improves accuracy on holdout data. No guessing, just measurable improvement in MAE/R2 metrics.

If ensemble doesn't beat single models on the data, don't force it. The goal is better predictions, not ensembles for their own sake.

</essential>

<specifics>
## Specific Ideas

- Benchmark all ensemble approaches: simple averaging, weighted blending, and stacking with meta-learner
- Compare against existing LightGBM and XGBoost single models on holdout data
- Use same backtesting methodology from Phase 13-08 (2024 as holdout season)
- If ensemble wins, make it the new default; if not, document why and keep single models

No preference for which ensemble technique — let the data decide.

</specifics>

<notes>
## Additional Context

The user is open-minded but data-driven. They'd prefer ensemble as the default if it genuinely improves accuracy, but they're not committed to ensembles if the metrics don't support it.

This phase is about validation first, implementation second. Prove value before changing the production pipeline.

</notes>

---

*Phase: 19-ensemble-models*
*Context gathered: 2026-01-20*
