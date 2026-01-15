# Phase 12: ML Pipeline Improvements - Context

**Gathered:** 2026-01-15
**Status:** Ready for planning

<vision>
## How This Should Work

The core of Phase 12 is building a validation/backtesting system that compares what we predicted to what actually happened. Using 2025 season data (which wasn't trained on), we can see how accurate our models really are.

When the system is running, after each game you'd be able to compare predictions vs actuals - building up confidence in the models over time. This isn't just for one-time validation; it's infrastructure for ongoing model assessment.

The results should work at two levels:
1. **Model-level** - Each model (QB passing yards, RB rushing yards, etc.) gets an overall accuracy/confidence percentage
2. **Player-level** - Ability to drill into specific players and see how predictions tracked across games

</vision>

<essential>
## What Must Be Nailed

All three aspects are equally important:

- **Confidence display in UI** - Users need to see how confident the model is in each prediction they're viewing
- **Model improvement insights** - Identify which models/stats have the most error so we know where to focus tuning
- **Historical tracking** - Build up a history of prediction accuracy over time, not just a one-shot validation

</essential>

<specifics>
## Specific Ideas

- Use 2025 season data as holdout (wasn't trained on) for initial validation
- Don't train on 2025 and then predict on it - that would be cheating
- Set up infrastructure so future predictions can be compared to actuals after games
- Model-level confidence percentage visible somewhere in the UI
- Ability to see per-player prediction accuracy for power users

</specifics>

<notes>
## Additional Context

This came up during Phase 11 discussion - user wants to see real validation of model accuracy, not just CV metrics. The goal is building user trust through transparency about how well predictions actually perform.

This complements the Phase 11 audit findings about adding prediction intervals (MAPIE) - intervals show uncertainty per-prediction, while this validation system shows overall model accuracy.

</notes>

---

*Phase: 12-ml-pipeline-improvements*
*Context gathered: 2026-01-15*
