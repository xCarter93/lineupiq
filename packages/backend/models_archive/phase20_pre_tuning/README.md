# Phase 20 Pre-Tuning Model Archive

**Created:** 2026-01-22
**Purpose:** Backup of models before Phase 21 position-specific tuning

## Contents

31 models trained with 28-feature set (before Phase 20 weather/matchup additions):
- 6 QB models (passing_yards, passing_tds, interceptions, rushing_yards, rushing_tds, fumbles_lost)
- 7 RB models (carries, rushing_yards, rushing_tds, receptions, receiving_yards, receiving_tds, fumbles_lost)
- 4 WR models (receptions, receiving_yards, receiving_tds, fumbles_lost)
- 4 TE models (receptions, receiving_yards, receiving_tds, fumbles_lost)
- 5 K models (fg_att, fg_att_0_39, fg_att_40_49, fg_att_50_plus, pat_att)
- 5 DEF models (def_sacks, def_interceptions, def_fumbles, points_allowed, total_def_tds)

## Training Configuration

- **Training data:** 2022-2025 (4 seasons)
- **Rolling window:** 5 games (Phase 19.1)
- **Optuna trials:** 30 per model
- **Model type:** LightGBM
- **Feature count:** 28 (pre-Phase 20)

## Rollback Instructions

To rollback Phase 21 changes:
```bash
cp models_archive/phase20_pre_tuning/*.joblib models/
```

## Related Phases

- Phase 19.1: 4-year training window, 5-game rolling window
- Phase 20: Added weather, injury, matchup features (40 total features)
- Phase 21: Position-specific tuning with expanded feature set
