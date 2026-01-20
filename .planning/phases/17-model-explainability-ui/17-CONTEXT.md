# Phase 17: Model Explainability UI - Context

**Gathered:** 2026-01-19
**Status:** Ready for planning

<vision>
## How This Should Work

When a user runs a prediction, they can click to open a dedicated explainability panel that shows why the model made that prediction. The panel shows both a visual breakdown (SHAP-style bar charts showing which features pushed the prediction up or down) and a plain English summary ("High projection due to weak opponent defense and recent hot streak").

The bar charts are expandable — show the top 3-5 most influential factors by default, with an option to expand and see the full breakdown (~10 features) for users who want to dig in.

Beyond explainability, this phase also overhauls the prediction page layout to make better use of horizontal space. Instead of stacking everything vertically, use a dashboard grid layout with modular panels — players, charts, and explanations as separate tiles that fill the available screen width.

Player headshots should be added throughout the app as compact avatars beside player names — recognizable but not taking up much space.

</vision>

<essential>
## What Must Be Nailed

- **Decision support** — The primary goal is helping users spot when to trust or doubt a projection based on the reasoning. If the model is high on a player because of a weak matchup, users should see that clearly. If it's projecting based on limited data, that should be visible too.
- **Horizontal space utilization** — The current stacked layout wastes screen real estate. Dashboard grid with modular panels should fill the width.
- **Visual + text explanations** — Bar charts alone are cryptic; plain English alone lacks detail. Both together serve different user needs.

</essential>

<specifics>
## Specific Ideas

- Separate explainability panel (click to open, not inline)
- Expandable bar charts: top 3-5 by default → full breakdown on expand
- Dashboard grid layout for the prediction page
- Modular tiles: player info, predicted stats, charts, explanation panels
- Compact player headshots as avatars beside names throughout the app
- Natural language summaries alongside the visual bar charts

</specifics>

<notes>
## Additional Context

This phase expands beyond pure explainability into a broader prediction page redesign. The explainability feature is the marquee addition, but the layout overhaul and headshot integration are part of the same vision for making the app feel more polished and usable.

The user emphasized decision support over education or trust-building — the explanations should help users make better start/sit decisions by understanding the reasoning behind projections.

</notes>

---

*Phase: 17-model-explainability-ui*
*Context gathered: 2026-01-19*
