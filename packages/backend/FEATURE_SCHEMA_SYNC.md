# Feature Schema Synchronization Guide

**CRITICAL:** When adding/removing ML features, ALL of these locations must be updated to avoid schema mismatch errors.

## Problem

The ML models, API schemas, and frontend interfaces all define the exact features expected for predictions. If they get out of sync, you'll see errors like:
- `AttributeError: 'PredictionRequest' object has no attribute 'extreme_cold'`
- `422 Unprocessable Entity: Field required`
- Missing or incorrect feature values

## When to Use This Guide

Update ALL locations below when:
- ✅ Adding new features (weather, matchup, injury, etc.)
- ✅ Removing features
- ✅ Renaming features
- ✅ Changing feature types (int → bool, etc.)

## Required Updates (All 4 Files)

### 1. Backend API - Prediction Request Schema
**File:** `packages/backend/src/lineupiq/api/schemas/prediction.py`

Update the `PredictionRequest` class:
```python
class PredictionRequest(BaseModel):
    # Add new features here with Field() definitions
    extreme_cold: bool = Field(..., description="Temperature below 25°F")
    # ... etc
```

### 2. Backend API - Explainability Request Schema
**File:** `packages/backend/src/lineupiq/api/schemas/explainability.py`

Update TWO places:
1. **ExplainabilityRequest class** (must match PredictionRequest exactly)
2. **FEATURE_DISPLAY_NAMES dict** (for human-readable labels in UI)

```python
FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "extreme_cold": "Extreme Cold (<25°F)",  # Add human-readable name
    # ... etc
}

class ExplainabilityRequest(BaseModel):
    extreme_cold: bool = Field(..., description="Temperature below 25°F")
    # ... etc
```

### 3. Backend API - Roster Endpoint (Player Features)
**File:** `packages/backend/src/lineupiq/api/routes/roster.py`

Update TWO functions:
1. **`get_player_features()`** - The main computation function
2. **`_get_default_features()`** - Default values for players without data

```python
def get_player_features(...):
    features: dict[str, float | bool] = {
        # ... existing features
        # Add Phase X features with neutral defaults
        "extreme_cold": False,
        "home_spread": 0.0,
        # ... etc
    }

def _get_default_features(position: str, is_home: bool):
    base = {
        # ... existing features
        # Add Phase X features
        "extreme_cold": False,
        "home_spread": 0.0,
        # ... etc
    }
```

### 4. Frontend - TypeScript Interface
**File:** `packages/frontend/lib/prediction-api.ts`

Update TWO places:
1. **PredictionFeatures interface** (TypeScript types)
2. **createDefaultFeatures() function** (default values)

```typescript
export interface PredictionFeatures {
  // ... existing features
  // Phase X features
  extreme_cold: boolean;
  home_spread: number;
  // ... etc
}

export function createDefaultFeatures(position: string, isHome: boolean) {
  const base = {
    // ... existing features
    // Phase X features - neutral defaults
    extreme_cold: false,
    home_spread: 0.0,
    // ... etc
  };
}
```

## Feature Count Reference

| Phase | Feature Count | Added Features |
|-------|---------------|----------------|
| Pre-20 | 28 | Original baseline features |
| 20 | 40 (+12) | Weather (7) + Matchup (5) |
| 21 | 40 | Position-specific tuning (no new features) |

## Validation Checklist

After updating schemas, verify:

- [ ] Backend starts without import errors
- [ ] Frontend TypeScript compiles without errors
- [ ] `/api/player/{id}/features` returns all features
- [ ] `/predict/{position}` accepts requests without 422 errors
- [ ] `/explain/{position}/{target}` works for SHAP explanations
- [ ] Feature count matches across all 4 files
- [ ] Default values are consistent (neutral for matchup/weather)

## Testing the Changes

```bash
# 1. Restart backend
cd packages/backend
uv run uvicorn src.lineupiq.api.main:app --reload

# 2. Restart frontend
cd packages/frontend
pnpm dev

# 3. Test prediction in UI
# - Select a player
# - Click "Get Prediction"
# - Verify predictions load
# - Verify explainability panel loads

# 4. Check backend logs for errors
# - No 422 Unprocessable Entity
# - No AttributeError messages
```

## Common Pitfalls

1. **Forgetting explainability endpoint** - Most common! Remember to update both prediction AND explainability schemas.

2. **Mismatched default values** - Use neutral defaults consistently:
   - Booleans: `false` (not `true`)
   - Numeric spreads: `0.0` (pick'em)
   - Totals: `45.0` (NFL average)

3. **Not restarting servers** - FastAPI caches schemas. Must restart backend after schema changes.

4. **Frontend caching** - Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R) after frontend updates.

## Phase 20 Example

When we added Phase 20 features (weather + matchup), we had to update:
1. `prediction.py` - Added 12 new fields to PredictionRequest
2. `explainability.py` - Added 12 new fields + display names
3. `roster.py` - Added 12 neutral defaults in 2 functions
4. `prediction-api.ts` - Added 12 TypeScript fields + defaults

Result: 4 files × ~15 lines each = ~60 lines of schema updates

## See Also

- `packages/backend/src/lineupiq/features/pipeline.py` - Source of truth for feature list (`get_feature_columns()`)
- `.planning/phases/20-advanced-features/` - Phase 20 plans where weather/matchup features were added
- `packages/backend/TRAINING.md` - Model training with new features

---

**Last Updated:** 2026-01-22 (Phase 21)
**Current Feature Count:** 40
