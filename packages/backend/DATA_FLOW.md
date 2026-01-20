# Data Flow & Freshness

This document explains how LineupIQ keeps predictions current even with bi-weekly model retraining.

## TL;DR

✅ **Models retrain bi-weekly** (historical patterns)
✅ **Features update every prediction** (current stats)
✅ **Data fetched on-demand** (always fresh)
✅ **No manual sync needed**

## The Key Insight

**Models learn patterns, features provide current data.**

A 2-week-old model with fresh features is nearly as accurate as a freshly trained model because:
- The model knows: "QB with 300+ yard rolling average vs weak defense → expect 280 yards"
- The features provide: "This QB has 320 yard rolling average this week"
- Pattern + fresh data = accurate prediction

## Complete Data Flow

### 1. Model Training (Bi-Weekly)

```
Every 2 weeks during season:
┌─────────────────────────────────────┐
│ GitHub Actions Workflow             │
├─────────────────────────────────────┤
│ 1. Fetch historical data            │
│    └─ 2023, 2024, 2025, 2026 seasons│
│                                     │
│ 2. Compute features                 │
│    └─ Rolling stats, opponent ranks │
│                                     │
│ 3. Train 32 models                  │
│    └─ Learn patterns in data        │
│                                     │
│ 4. Save models as .joblib           │
│    └─ packages/backend/models/      │
└─────────────────────────────────────┘
         ↓
    [Models deployed to production]
```

**What models learn:**
- Historical patterns (e.g., "RBs struggle vs top-5 defenses")
- Feature importance (e.g., "last 5 games > last season average")
- Non-linear relationships (e.g., "weather + dome interaction")

**What models DON'T know:**
- This week's actual stats
- Current player form
- Recent injuries/trades

### 2. Prediction Request (Real-time)

```
User requests: "Predict Patrick Mahomes week 7"
┌─────────────────────────────────────┐
│ API Request                         │
├─────────────────────────────────────┤
│ Player: Patrick Mahomes             │
│ Week: 7                             │
│ Season: 2026                        │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ Feature Pipeline                    │
├─────────────────────────────────────┤
│ 1. Check nflreadpy cache            │
│    └─ Is 2026 data < 24h old?      │
│                                     │
│ IF cache stale:                     │
│   2. Fetch latest NFL data (~5 sec) │
│      └─ All 2026 games through week 6│
│   3. Update cache                   │
│                                     │
│ 4. Compute FRESH features           │
│    ├─ Last 5 games for Mahomes      │
│    ├─ Opponent defense rank (week 7)│
│    ├─ KC Chiefs rolling stats       │
│    └─ Weather for week 7 matchup    │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ Model Prediction                    │
├─────────────────────────────────────┤
│ Load QB passing_yards model         │
│ └─ Trained 2 weeks ago              │
│                                     │
│ Apply model to FRESH features       │
│ └─ Model: "Given these features..." │
│ └─ Predict: 285 yards               │
└─────────────────────────────────────┘
         ↓
    [Return prediction to user]
```

**Feature freshness:**
- ✅ Rolling stats: Last 5 games (through week 6)
- ✅ Opponent rank: Current standings
- ✅ Team stats: Latest results
- ✅ Player form: Most recent games

## Data Caching

### nflreadpy Cache Structure

```
packages/backend/data/raw/
├── player_stats/
│   ├── 2022.parquet  [Static - season complete]
│   ├── 2023.parquet  [Static - season complete]
│   ├── 2024.parquet  [Static - season complete]
│   ├── 2025.parquet  [Static - season complete]
│   └── 2026.parquet  [Dynamic - updates weekly]
└── schedules/
    └── 2022_2023_2024_2025_2026.parquet
```

### Cache Behavior

**Complete seasons (2022-2025):**
- Fetched once
- Cached forever (data doesn't change)
- Only re-fetched if cache file deleted

**Current season (2026):**
- Fetched on first request
- Cached for 24 hours
- Auto-refreshes if > 24 hours old
- Contains all games played so far

**Cache check (on every prediction):**
```python
def fetch_player_stats(season: int):
    cache_file = f"data/raw/player_stats/{season}.parquet"

    if os.path.exists(cache_file):
        # Check if cache is fresh
        age = time.time() - os.path.getmtime(cache_file)

        if age < 24 * 3600:  # Less than 24 hours old
            return load_cache(cache_file)  # Fast! ~100ms

    # Cache stale or missing - fetch fresh data
    data = nflreadpy.load_player_stats(season)  # Slow! ~5 sec
    save_cache(data, cache_file)
    return data
```

## Example Timeline

### Week 6 of 2026 Season

**Monday, Oct 14:**
- MNF game completes
- nflreadpy has week 6 data available

**Tuesday, Oct 15 (1 AM EST):**
- Bi-weekly training workflow runs
- Fetches 2023-2026 data (includes week 6)
- Trains models with weeks 1-6 data
- Deploys updated models

**Wednesday, Oct 16:**
- User A requests prediction for week 7
  - Cache has week 6 data (< 24h old)
  - Features use week 6 stats
  - Oct 15 models make prediction
  - **Total time: 500ms** ✅

**Thursday, Oct 17:**
- User B requests prediction for week 7
  - Cache still has week 6 data (< 24h old)
  - Same fresh features
  - Same models
  - **Total time: 300ms** ✅ (feature computation cached)

**Wednesday, Oct 23:**
- User C requests prediction for week 8
  - Cache is > 24 hours old
  - Auto-fetches week 7 data from nflreadpy
  - Features use week 7 stats
  - Oct 15 models still used (bi-weekly schedule)
  - **Total time: 5 seconds first request, then 300ms** ✅

**Tuesday, Oct 29 (1 AM EST):**
- Next bi-weekly training workflow runs
- Fetches 2023-2026 data (now includes weeks 1-7)
- Trains models with weeks 1-7 data
- Deploys updated models

## Why Bi-Weekly Training Works

**Pattern stability:** QB performance patterns don't change week-to-week
- "Strong arm QB vs weak secondary = yards" ← Learned from 3+ years
- One week of new data barely shifts these patterns

**Feature recency:** Fresh features capture current form
- Mahomes averaging 300 yards/game → rolling_avg_5 = 300
- This number updates every week automatically
- Model applies same learned pattern to updated number

**Math example:**
```
Model trained Oct 15 (weeks 1-6):
  Pattern: QB with roll_avg_5 > 280 → Predict +15 yards

Oct 22 prediction (week 7, using Oct 15 model):
  Fresh feature: Mahomes roll_avg_5 = 295 (includes week 6)
  Model applies: 295 + 15 = 310 yards
  ✅ Prediction uses latest data even with week-old model

Oct 29 prediction (week 8, using Oct 15 model):
  Fresh feature: Mahomes roll_avg_5 = 288 (includes week 7)
  Model applies: 288 + 15 = 303 yards
  ✅ Still accurate! Week 7 data included in features

Oct 29 retrain (new models):
  Pattern learned: QB with roll_avg_5 > 280 → Predict +16 yards
  Improvement: +1 yard adjustment from weeks 1-8 data
  Impact: Minimal (models already very accurate)
```

## When Features Update

| Event | Feature Update | Model Update |
|-------|----------------|--------------|
| New game played | ✅ Next prediction | ❌ Wait for bi-weekly |
| Injury/trade | ✅ Next prediction | ❌ Wait for bi-weekly |
| Weather changes | ✅ Next prediction | ❌ N/A (weather is input) |
| Opponent matchup | ✅ Next prediction | ❌ N/A (matchup is input) |
| 2 weeks pass | ✅ Next prediction | ✅ Scheduled retrain |

## FAQ

**Q: Won't predictions get stale with week-old models?**
A: No! Features stay current. The 2-week-old model receives this week's rolling averages, opponent rankings, etc. Pattern learning is cumulative - it doesn't forget or decay.

**Q: What if a player gets injured?**
A: Features reflect it automatically. If player misses week 6, their week 7 rolling average won't include week 6. Model sees lower average → predicts accordingly.

**Q: What about completely new patterns (e.g., rule change)?**
A: Retrain immediately with manual trigger. Bi-weekly catches most meta shifts. Major changes → manual retrain same day.

**Q: How do I verify features are fresh?**
A: Check cache timestamp:
```bash
ls -lh packages/backend/data/raw/player_stats/2026.parquet
# Should be < 24 hours old during season
```

**Q: Can I force a cache refresh?**
A: Yes, delete the cache file:
```bash
rm packages/backend/data/raw/player_stats/2026.parquet
# Next prediction will fetch fresh data
```

**Q: What if nflreadpy is down?**
A: API returns error. Consider adding fallback:
- Retry with exponential backoff
- Use stale cache if exists (better than no prediction)
- Alert user "Using data from [cache date]"

## Monitoring Data Freshness

Add to your monitoring dashboard:

```python
# Check cache age
cache_file = "data/raw/player_stats/2026.parquet"
age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600

if age_hours > 48:
    alert("Cache very stale - possible nflreadpy issue")
```

## Summary

**You don't need to do anything special!**

- ✅ Models train bi-weekly automatically
- ✅ Features update on every prediction
- ✅ Data fetches when cache expires
- ✅ Everything stays current without manual intervention

The system is designed to be maintenance-free while keeping predictions accurate with the latest data.
