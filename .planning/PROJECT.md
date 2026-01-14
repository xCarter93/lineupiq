# LineupIQ

## What This Is

A fantasy football prediction web app that trains custom ML models on historical NFL data to predict individual player statistics (passing yards, rushing yards, TDs, etc.) which then feed into configurable fantasy point calculations. The app enables users to simulate matchups by selecting a player and opponent, incorporating factors like weather and historical matchup data.

## Core Value

Accurate stat-level predictions from well-engineered features and properly trained models. Everything else serves this goal. Previous attempts failed due to feature overload, overfitting, and training convergence issues — this iteration prioritizes getting the model fundamentals right over UI polish.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Monorepo structure with Python ML backend and Next.js/TypeScript frontend
- [ ] Data pipeline using nflreadpy to fetch and process historical NFL data (1999-2025)
- [ ] Feature engineering for ML models (opponent strength, weather, home/away, rolling stats)
- [ ] ML models to predict individual stats for skill positions (QB, RB, WR, TE)
- [ ] Stat predictions: passing yards/TDs/INTs, rushing yards/TDs, receiving yards/TDs/receptions
- [ ] Matchup simulation UI: select player + opponent → view projected stats
- [ ] Configurable fantasy scoring (standard scoring default)
- [ ] Weather factor integration for predictions
- [ ] Convex backend for app state, scoring configs, and cached predictions
- [ ] Training pipeline that can retrain models as new season data becomes available

### Out of Scope

- User authentication/accounts — not needed for v1, will add later
- Real-time game data updates — historical + predictions only
- Multiple scoring format support — standard scoring only for MVP
- Kicker (K) and Defense (DEF) predictions — skill positions first, add later
- Monte Carlo/distribution-based predictions — single point estimates for MVP
- Play-by-play game simulation — just stat predictions per matchup
- Mobile-first design — desktop-first for v1

## Context

### Data Sources (nflreadpy)

| Function | Data | Years | Use Case |
|----------|------|-------|----------|
| `load_pbp()` | Play-by-play (372+ cols) | 1999+ | Feature extraction |
| `load_player_stats()` | Weekly stats (52 cols) | All | Primary training data |
| `load_nextgen_stats()` | Advanced tracking | 2016+ | Separation, YAC, air yards |
| `load_schedules()` | Games, roof, weather | All | Opponent/venue features |
| `load_snap_counts()` | Snap participation | 2012+ | Opportunity metrics |
| `load_injuries()` | Injury reports | 2009+ | Availability features |
| `load_depth_charts()` | Position depth | 2001+ | Role context |
| `load_ff_opportunity()` | Expected fantasy pts | 2006+ | Baseline comparisons |

### Fantasy Stats to Predict

**Passing (QB):** yards, TDs, INTs, 2pt conversions
**Rushing (RB primarily):** yards, TDs, fumbles lost, 2pt conversions
**Receiving (WR/TE/RB):** receptions, yards, TDs, fumbles lost, 2pt conversions

**Standard Scoring Reference:**
- Passing: 1pt/25 yards, 4pt/TD, -2pt/INT
- Rushing: 1pt/10 yards, 6pt/TD
- Receiving: 1pt/10 yards, 6pt/TD
- All: 2pt/2pt conversion, -2pt/fumble lost

### Previous Attempt Lessons

1. **Feature overload** — too many inputs caused overfitting and noise
2. **Training convergence** — models wouldn't converge properly
3. **Inaccurate predictions** — outputs were unrealistic

**Solution approach:**
- Start with minimal, high-signal features
- Use feature importance analysis to prune
- Validate with cross-validation before adding complexity
- Focus on per-stat prediction (more accurate than direct fantasy points)

### ML Research Insights

- Rolling 3-week lookback windows often optimal
- Ensemble methods (XGBoost, Random Forest) outperform single models
- Weather/opponent correlate but weakly; historical matchup data more valuable
- Predicting individual stats more accurate than direct fantasy point prediction
- Feature selection is critical — start minimal and add selectively

## Constraints

- **Package managers**: pnpm (TypeScript), uv (Python) — no exceptions
- **Frontend framework**: Next.js with Shadcn UI preset (Radix, Mira style, Zinc/Emerald theme)
- **Backend**: Convex for app services (not for large training datasets)
- **Data source**: nflreadpy only for NFL data
- **Deployment**: Local development only for v1
- **ML libraries**: PyTorch, TensorFlow, Scikit-learn as needed
- **Position priority**: Skill positions (QB, RB, WR, TE) before K/DEF

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Predict individual stats, not fantasy points | More accurate, allows custom scoring | — Pending |
| Skill positions first (QB/RB/WR/TE) | More data, higher fantasy impact | — Pending |
| Monorepo with Python + Next.js | Clean separation of ML and UI concerns | — Pending |
| nflreadpy over nfl_data_py | nfl_data_py deprecated, nflreadpy actively maintained | — Pending |
| Standard scoring only for MVP | Reduces complexity, can add formats later | — Pending |
| Start with minimal features | Avoid previous overfitting issues | — Pending |

---
*Last updated: 2026-01-14 after initialization*
