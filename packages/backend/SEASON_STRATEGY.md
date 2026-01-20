# 2026 Season Training Strategy

## Pre-Season (Before Week 1)

**August:** Train final pre-season models
```bash
# Train on last 4 complete seasons
uv run python scripts/train_all.py --seasons 2022 2023 2024 2025 --trials 50
```

**Deploy:** These models will be used for weeks 1-4 predictions.

## During Season (Weeks 1-18)

### Weekly Data Refresh (Automated Daily)

**Every Tuesday morning** (after Monday Night Football):
```bash
# Just fetch new data - NO retraining
# nflreadpy automatically caches new week's data
# API will use updated rolling stats with existing models
```

**Cost:** ~10 seconds
**Benefit:** Rolling averages, opponent rankings stay current

### Bi-Weekly Model Retraining (Automated)

**Week 4 (Tuesday, Oct 1):**
```bash
uv run python scripts/train_all.py --seasons 2023 2024 2025 2026 --trials 30
```
- Includes weeks 1-4 of 2026
- Drops 2022 (sliding window: last 3.25 seasons)
- Training time: ~45 minutes

**Week 8 (Tuesday, Oct 29):**
```bash
uv run python scripts/train_all.py --seasons 2023 2024 2025 2026 --trials 30
```
- Includes weeks 1-8 of 2026
- Training time: ~50 minutes

**Week 12 (Tuesday, Nov 26):**
```bash
uv run python scripts/train_all.py --seasons 2023 2024 2025 2026 --trials 30
```
- Includes weeks 1-12 of 2026
- Training time: ~55 minutes

**Week 16 (Tuesday, Dec 24):**
```bash
uv run python scripts/train_all.py --seasons 2024 2025 2026 --trials 30
```
- Includes weeks 1-16 of 2026
- Drops 2023 (sliding window: last 2.9 seasons)
- Training time: ~40 minutes

### Post-Season (After Week 18)

**January:** Final full retrain for playoffs
```bash
uv run python scripts/train_all.py --seasons 2023 2024 2025 2026 --trials 50
```
- Complete 2026 regular season data
- Use for playoff predictions

## GitHub Actions Configuration

### Daily Data Sync (Light)

```yaml
name: Daily Data Sync

on:
  schedule:
    # Every Tuesday at 10 AM EST (after MNF data available)
    - cron: '0 15 * * 2'  # 10 AM EST = 3 PM UTC
  workflow_dispatch:

jobs:
  sync-data:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Sync latest game data
        run: |
          cd packages/backend
          uv sync
          # Data sync happens automatically on next API request
          echo "Data will be fetched on next prediction request"
```

### Bi-Weekly Model Training (Heavy)

```yaml
name: Bi-Weekly Model Training

on:
  schedule:
    # Runs at weeks 4, 8, 12, 16 (adjust dates as needed)
    - cron: '0 6 * * 2'  # Every Tuesday at 6 AM UTC
  workflow_dispatch:

jobs:
  train-models:
    # Only run during season (Sep-Dec)
    if: |
      github.event.schedule == '0 6 * * 2' &&
      (startsWith(github.event.head_commit.timestamp, '2026-09') ||
       startsWith(github.event.head_commit.timestamp, '2026-10') ||
       startsWith(github.event.head_commit.timestamp, '2026-11') ||
       startsWith(github.event.head_commit.timestamp, '2026-12'))

    runs-on: ubuntu-latest
    timeout-minutes: 120  # 2 hours max

    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd packages/backend
          uv sync

      - name: Determine training seasons
        id: seasons
        run: |
          CURRENT_YEAR=$(date +%Y)
          CURRENT_MONTH=$(date +%m)

          # Use sliding 3-season window during season
          if [ "$CURRENT_MONTH" -ge 9 ] && [ "$CURRENT_MONTH" -le 12 ]; then
            SEASONS="$((CURRENT_YEAR-2)) $((CURRENT_YEAR-1)) $CURRENT_YEAR"
          else
            # Pre/post season: use last 3 complete seasons
            SEASONS="$((CURRENT_YEAR-3)) $((CURRENT_YEAR-2)) $((CURRENT_YEAR-1))"
          fi

          echo "seasons=$SEASONS" >> $GITHUB_OUTPUT
          echo "Training on seasons: $SEASONS"

      - name: Train models
        run: |
          cd packages/backend
          uv run python scripts/train_all.py \
            --seasons ${{ steps.seasons.outputs.seasons }} \
            --trials 30 \
            2>&1 | tee training.log

      - name: Upload trained models
        uses: actions/upload-artifact@v3
        with:
          name: models-${{ github.run_number }}
          path: packages/backend/models/*.joblib
          retention-days: 90

      - name: Upload training log
        uses: actions/upload-artifact@v3
        with:
          name: training-log-${{ github.run_number }}
          path: packages/backend/training.log

      - name: Deploy models (optional - add your deployment logic)
        run: |
          # Example: Upload to S3, copy to production server, etc.
          echo "Add deployment logic here"
          # aws s3 sync packages/backend/models/ s3://your-bucket/models/

      - name: Notify on failure
        if: failure()
        run: |
          echo "Training failed! Check logs."
          # Add Slack/email notification
```

## Cost Analysis

### Weekly Retraining (NOT Recommended)
- **Frequency:** 18 times per season
- **Time per train:** 2-3 hours
- **Total compute:** ~45 hours/season
- **GitHub Actions cost:** ~$45-90 (if using paid runners)

### Bi-Weekly Retraining (Recommended)
- **Frequency:** 4-5 times per season
- **Time per train:** 45-60 minutes (with sliding window)
- **Total compute:** ~4 hours/season
- **GitHub Actions cost:** ~$4-8
- **Savings:** 90% less compute, same performance

## Performance Monitoring

After each retraining, check:

1. **Model metrics** (from training log):
   ```
   QB_passing_yards: RMSE = 91.03 (target: <95)
   QB_passing_tds: RMSE = 1.23 (target: <1.5)
   ```

2. **Prediction quality** (spot-check):
   - Pick 3-5 well-known players
   - Compare predictions to recent performance
   - Ensure predictions are reasonable

3. **API performance**:
   - Model loading time should stay under 2 seconds
   - Prediction time should stay under 500ms

## When to Retrain Off-Schedule

**Retrain immediately if:**
- Major rule changes (affects scoring)
- Your predictions are consistently wrong for >1 week
- Large meta shifts (new offensive schemes become dominant)

**Don't retrain for:**
- One bad prediction (variance is normal)
- Missing one week's data (minimal impact)
- Playoffs (regular season models work fine)

## Emergency Manual Training

If automated training fails:

```bash
# SSH to your server or run locally
cd packages/backend

# Check what went wrong
tail -100 training.log

# Manual retrain
uv run python scripts/train_all.py \
  --seasons 2023 2024 2025 2026 \
  --trials 30

# Verify models generated
ls -lh models/*.joblib | wc -l  # Should be 32
```

## Future Optimizations

Once you have a full season of 2026 data:

1. **Analyze retraining benefit:** Compare predictions from:
   - Models trained with 4 weeks of 2026 data
   - Models trained with 8 weeks of 2026 data
   - Models trained with 12 weeks of 2026 data

2. **Optimize schedule:** If performance plateaus after week 8, you might only need:
   - Week 4 retrain (early season adjustment)
   - Week 12 retrain (mid-season update)
   - Post-season retrain (full year data)

3. **Consider position-specific schedules:**
   - QB/RB models: Retrain every 4 weeks (more stable)
   - WR/TE models: Retrain every 2 weeks (more volatile due to matchups)
   - K/DEF models: Retrain every 6 weeks (very stable)

## Summary

**Best Practice for 2026 Season:**
- ✅ **Bi-weekly retraining** (weeks 4, 8, 12, 16)
- ✅ **Sliding 3-season window** for faster training
- ✅ **Automated via GitHub Actions**
- ✅ **Daily data sync** (automatic on API requests)
- ❌ **NOT weekly** (marginal benefit, high cost)
