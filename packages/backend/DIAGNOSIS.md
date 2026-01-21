# Root Cause Analysis: Identical Predictions for Different Players

**Date:** 2026-01-20
**Phase:** 19.2.1
**Severity:** Critical - All players in the same position receive identical predictions

## Executive Summary

Different players in the same position are receiving identical stat predictions because of a **window parameter mismatch** between model training (window=5) and prediction-time feature computation (window=3). This causes all players to receive position-typical default features instead of their player-specific rolling statistics.

## Root Cause

### Timeline of Events

1. **Phase 19.1-02 (2026-01-20):** Rolling window expanded from 3 to 5 games
   - Feature engineering pipeline updated to use `window=5`
   - All models retrained with `roll5` features
   - File: `packages/backend/src/lineupiq/features/pipeline.py` line 33
   - Commit: f432834

2. **Oversight:** API prediction endpoint NOT updated to match
   - File: `packages/backend/src/lineupiq/api/routes/roster.py`
   - Functions still default to `window=3`

### The Bug Mechanism

**Step 1:** Models expect features with `roll5` suffix
```python
# From packages/backend/src/lineupiq/features/pipeline.py:144-155
rolling_features = [
    "passing_yards_roll5",
    "passing_tds_roll5",
    "rushing_yards_roll5",
    "rushing_tds_roll5",
    "carries_roll5",
    "receiving_yards_roll5",
    "receiving_tds_roll5",
    "receptions_roll5",
]
```

**Step 2:** API computes features with `roll3` suffix (DEFAULT WINDOW = 3)
```python
# From packages/backend/src/lineupiq/api/routes/roster.py:122-124
def _compute_rolling_stats_for_player(
    history_df: pl.DataFrame,
    window: int = 3,  # ← BUG: Should be 5 to match models
) -> dict[str, float]:
```

**Step 3:** Default features use `roll5` keys
```python
# From packages/backend/src/lineupiq/api/routes/roster.py:256-275
if position == "QB":
    return {
        **base,
        "passing_yards_roll5": 250.0,  # ← Position default
        "passing_tds_roll5": 1.8,
        "rushing_yards_roll5": 15.0,
        "rushing_tds_roll5": 0.1,
        "carries_roll5": 3.0,
        # ... more defaults
    }
```

**Step 4:** Feature merge doesn't overwrite defaults
```python
# From packages/backend/src/lineupiq/api/routes/roster.py:443-451
if has_sufficient_data:
    # Compute player-specific features from history
    rolling_stats = _compute_rolling_stats_for_player(history_df)  # ← Creates roll3 keys
    volatility = _compute_volatility_for_player(history_df)        # ← Creates std3/cv3 keys

    # ...

    features: dict[str, float | bool] = {
        **rolling_stats,    # ← roll3 keys added
        **volatility,       # ← std3/cv3 keys added
        **opponent_features,
        **team_features,
        # ...
    }
else:
    features = _get_default_features(position, is_home)  # ← roll5 keys

    if games_available > 0:
        rolling_stats = _compute_rolling_stats_for_player(history_df)  # ← roll3 keys
        volatility = _compute_volatility_for_player(history_df)        # ← std3/cv3 keys
        features.update(rolling_stats)  # ← LINE 450: roll3 keys DON'T overwrite roll5 defaults!
        features.update(volatility)
```

**Result:** When features dict is sent to the model:
- Has both `passing_yards_roll3` (player-specific, ignored) AND `passing_yards_roll5` (default, used)
- Model only reads `passing_yards_roll5` → gets default value of 250.0
- Same for all players in the position → identical predictions!

## Evidence from Diagnostic Script

Running `scripts/diagnose_player_features.py` demonstrates the bug:

```
Player-specific values (window=5, what models expect):
  Jalen Hurts:     passing_yards_roll5: 175.6, passing_tds_roll5: 1.4
  Patrick Mahomes: passing_yards_roll5: 247.6, passing_tds_roll5: 1.0
  Joe Burrow:      passing_yards_roll5: 271.8, passing_tds_roll5: 2.6

What API actually computes (window=3):
  Jalen Hurts:     passing_yards_roll3: 154.33, passing_tds_roll3: 1.33
  Patrick Mahomes: passing_yards_roll3: 203.33, passing_tds_roll3: 1.33
  Joe Burrow:      passing_yards_roll3: 283.33, passing_tds_roll3: 3.0

What models receive (all players get same defaults):
  Jalen Hurts:     passing_yards_roll5: 250.0 (default!)
  Patrick Mahomes: passing_yards_roll5: 250.0 (default!)
  Joe Burrow:      passing_yards_roll5: 250.0 (default!)
```

All three QBs with vastly different performance profiles receive the same feature values → same predictions.

## Code References

### Files Affected

1. **packages/backend/src/lineupiq/api/routes/roster.py**
   - Line 124: `def _compute_rolling_stats_for_player(history_df, window: int = 3)`
   - Line 172: `def _compute_volatility_for_player(history_df, window: int = 3)`
   - Line 424: Call to `_compute_rolling_stats_for_player(history_df)` with default window=3
   - Line 425: Call to `_compute_volatility_for_player(history_df)` with default window=3
   - Line 448: Call to `_compute_rolling_stats_for_player(history_df)` with default window=3
   - Line 449: Call to `_compute_volatility_for_player(history_df)` with default window=3
   - Line 450: `features.update(rolling_stats)` - roll3 keys don't overwrite roll5 defaults

2. **packages/backend/src/lineupiq/features/pipeline.py**
   - Line 33: `def build_features(seasons, rolling_window: int = 5)` - Models trained with window=5
   - Line 144-155: Feature column definitions use `roll5` suffix

### Functions Requiring Changes

```python
# BEFORE (bug):
def _compute_rolling_stats_for_player(history_df: pl.DataFrame, window: int = 3):
    # Creates roll3 keys that models don't recognize

def _compute_volatility_for_player(history_df: pl.DataFrame, window: int = 3):
    # Creates std3/cv3 keys that models don't recognize

# Calls with implicit default:
rolling_stats = _compute_rolling_stats_for_player(history_df)
volatility = _compute_volatility_for_player(history_df)
```

```python
# AFTER (fix):
def _compute_rolling_stats_for_player(history_df: pl.DataFrame, window: int = 5):
    # Creates roll5 keys that match model expectations

def _compute_volatility_for_player(history_df: pl.DataFrame, window: int = 5):
    # Creates std5/cv5 keys that match model expectations

# Calls can remain the same (use new default):
rolling_stats = _compute_rolling_stats_for_player(history_df)
volatility = _compute_volatility_for_player(history_df)
```

## Fix Summary

**Single-line changes required:**
1. Line 124: Change `window: int = 3` to `window: int = 5`
2. Line 172: Change `window: int = 3` to `window: int = 5`

**No changes required to function calls** - They will automatically use the new default.

**Impact:**
- Immediately fixes player-specific predictions
- All players will receive features based on their actual rolling stats
- Predictions will differentiate between players based on performance

## Testing the Fix

After applying the fix, re-run the diagnostic script:
```bash
uv run python scripts/diagnose_player_features.py
```

Expected output should show:
- API computes window=5 features (matching models)
- Player-specific roll5 values replace defaults
- Each player receives unique feature values → unique predictions

## Related Documentation

- **Phase 19.1-02 Summary:** `.planning/phases/19.1-re-evaluate-recent-performance-metrics/19.1-02-SUMMARY.md`
- **Feature Pipeline:** `packages/backend/src/lineupiq/features/pipeline.py`
- **Diagnostic Script:** `packages/backend/scripts/diagnose_player_features.py`
