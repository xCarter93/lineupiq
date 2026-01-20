# Model Training Guide

This document explains the different ways to train LineupIQ models, from manual CLI training to fully automated weekly retraining.

## Quick Start (CLI)

Train all models manually from the command line:

```bash
cd packages/backend
uv run python scripts/train_all.py
```

## Training Options

### 1. Command Line Interface (Manual)

Best for: Manual retraining, testing, development

```bash
# Train all positions with defaults (2022-2025, 30 trials)
uv run python scripts/train_all.py

# Quick training for testing (10 trials)
uv run python scripts/train_all.py --quick

# Train specific positions
uv run python scripts/train_all.py --positions QB RB

# Custom configuration
uv run python scripts/train_all.py \
  --positions QB RB WR TE \
  --seasons 2020 2021 2022 2023 2024 2025 \
  --trials 50 \
  --rolling-window 5
```

### 2. Python Module (Programmatic)

Best for: Integration with other Python scripts, Jupyter notebooks

```python
from scripts.train_all import train_all_models

# Train all models
results = train_all_models()

# Train specific positions with custom settings
results = train_all_models(
    positions=["QB", "RB"],
    seasons=[2022, 2023, 2024, 2025],
    n_trials=30,
    rolling_window=5
)

# Check results
print(f"Trained {len(results)} models")
for model_name, (model, metrics) in results.items():
    print(f"{model_name}: RMSE = {metrics['cv_rmse_mean']:.2f}")
```

### 3. REST API (Async/Background)

Best for: Triggering training from web UI, scheduled jobs, webhooks

**Start Training:**
```bash
curl -X POST http://localhost:8000/api/training/start \
  -H "Content-Type: application/json" \
  -d '{
    "positions": ["QB", "RB", "WR", "TE"],
    "seasons": [2022, 2023, 2024, 2025],
    "n_trials": 30,
    "rolling_window": 5
  }'
```

**Check Status:**
```bash
curl http://localhost:8000/api/training/status
```

**Response:**
```json
{
  "status": "running",
  "is_running": true,
  "started_at": "2025-01-20T16:30:00",
  "progress": {
    "completed": 12,
    "total": 32
  }
}
```

**Setup (add to your FastAPI app):**
```python
# In your main FastAPI app (e.g., src/lineupiq/api/main.py)
from lineupiq.api.training import router as training_router

app = FastAPI()
app.include_router(training_router, prefix="/api")
```

### 4. Scheduled Training (Cron)

Best for: Weekly automated retraining during the season

**Create a weekly training script:**

```bash
#!/bin/bash
# scripts/weekly_retrain.sh

# Load environment
cd /path/to/lineupiq/packages/backend
source .venv/bin/activate

# Get current season
CURRENT_SEASON=$(date +%Y)

# Calculate training window (last 4 seasons)
SEASONS="$((CURRENT_SEASON-3)) $((CURRENT_SEASON-2)) $((CURRENT_SEASON-1)) $CURRENT_SEASON"

# Run training
python scripts/train_all.py \
  --seasons $SEASONS \
  --trials 30 \
  2>&1 | tee logs/training_$(date +%Y%m%d).log

# Send notification (optional)
if [ $? -eq 0 ]; then
  echo "Training completed successfully" | mail -s "LineupIQ Training Success" you@example.com
else
  echo "Training failed! Check logs." | mail -s "LineupIQ Training FAILED" you@example.com
fi
```

**Add to crontab (runs every Tuesday at 3 AM):**
```bash
# Edit crontab
crontab -e

# Add this line:
0 3 * * 2 /path/to/lineupiq/packages/backend/scripts/weekly_retrain.sh
```

### 5. GitHub Actions (CI/CD)

Best for: Automated training in the cloud, scheduled runs without local server

**Create `.github/workflows/weekly-training.yml`:**

```yaml
name: Weekly Model Training

on:
  schedule:
    # Run every Tuesday at 3 AM UTC
    - cron: '0 3 * * 2'
  workflow_dispatch:  # Allow manual trigger

jobs:
  train-models:
    runs-on: ubuntu-latest
    timeout-minutes: 360  # 6 hours max

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

      - name: Train models
        run: |
          cd packages/backend
          uv run python scripts/train_all.py --trials 30

      - name: Upload models
        uses: actions/upload-artifact@v3
        with:
          name: trained-models
          path: packages/backend/models/*.joblib

      - name: Notify on failure
        if: failure()
        run: |
          echo "Training failed!"
          # Add notification logic (Slack, email, etc.)
```

## Weekly Retraining Workflow

For production use during the NFL season:

1. **Tuesday Morning (3 AM):**
   - New game data from Monday Night Football is available
   - Automated cron job triggers retraining
   - Uses last 4 seasons of data (e.g., 2022-2025)

2. **Training Process:**
   - Fetches latest data from nflreadpy
   - Trains 32 models (QB, RB, WR, TE, K, DEF)
   - Takes 2-3 hours with 30 trials per model

3. **Validation:**
   - Check training logs for errors
   - Verify all 32 models generated
   - Spot-check model performance metrics

4. **Deployment:**
   - Models automatically used by API (loads latest .joblib files)
   - No downtime - API picks up new models on next request

## Monitoring

### Check Training Progress

```bash
# View live logs
tail -f packages/backend/training.log

# Count completed models
ls -1 packages/backend/models/*.joblib | wc -l

# Check model timestamps
ls -lht packages/backend/models/*.joblib | head -10
```

### Performance Metrics

After training completes, check the summary:

```bash
tail -100 packages/backend/training.log
```

Look for the summary table:
```
MODEL PERFORMANCE SUMMARY
Position_Target                      RMSE Mean    RMSE Std    Samples
--------------------------------------------------------------------------------
QB_passing_yards                         91.03        2.48       2499
QB_passing_tds                            1.23        0.05       2499
...
```

## Troubleshooting

### Training Fails with "Memory Error"

Reduce batch size or number of concurrent trials:
```bash
# Reduce trials
uv run python scripts/train_all.py --trials 10
```

### API Training Times Out

Increase timeout in your API config or use a task queue like Celery/RQ for long-running jobs.

### Old Models Not Being Replaced

Check file permissions on `models/` directory:
```bash
ls -la packages/backend/models/
chmod 755 packages/backend/models/
```

## Advanced: Task Queue (Celery)

For production systems with high reliability requirements, use Celery:

```python
# tasks.py
from celery import Celery
from scripts.train_all import train_all_models

app = Celery('training', broker='redis://localhost:6379')

@app.task
def train_models_async(positions=None, seasons=None, n_trials=30):
    """Train models as a Celery task."""
    return train_all_models(positions, seasons, n_trials)

# Trigger from API
from tasks import train_models_async

@app.post("/api/training/start")
def start_training():
    task = train_models_async.delay()
    return {"task_id": task.id}
```

## Best Practices

1. **Keep 4 seasons of data** - Balance recency with sufficient training data
2. **Train weekly during season** - Incorporate latest game results
3. **Use 30 trials in production** - Good balance of speed and optimization
4. **Monitor training time** - Should complete in 2-3 hours
5. **Archive old models** - Keep backups before overwriting
6. **Validate after training** - Spot-check model predictions before deploying
7. **Log everything** - Training logs help debug issues
8. **Set up alerts** - Get notified if automated training fails

## Example: Complete Weekly Pipeline

```python
# weekly_training_pipeline.py
"""
Complete weekly training pipeline with data fetch, training, and validation.
"""

import logging
from datetime import datetime
from pathlib import Path
from scripts.train_all import train_all_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def weekly_training_pipeline():
    """Run complete weekly training pipeline."""

    logger.info("Starting weekly training pipeline")
    start_time = datetime.now()

    # 1. Fetch latest data (already cached by nflreadpy)
    logger.info("Step 1: Data already cached")

    # 2. Train models with last 4 seasons
    current_year = datetime.now().year
    seasons = [current_year - 3, current_year - 2, current_year - 1, current_year]

    logger.info(f"Step 2: Training models for seasons {seasons}")
    results = train_all_models(
        positions=["QB", "RB", "WR", "TE", "K", "DEF"],
        seasons=seasons,
        n_trials=30,
        rolling_window=5
    )

    # 3. Validate results
    if results and len(results) == 32:
        logger.info(f"✓ Step 3: All {len(results)} models trained successfully")
    else:
        logger.error(f"✗ Step 3: Only {len(results) if results else 0}/32 models trained")
        return False

    # 4. Archive old models (optional)
    # ... archiving logic ...

    elapsed = (datetime.now() - start_time).total_seconds() / 60
    logger.info(f"Pipeline complete in {elapsed:.1f} minutes")

    return True

if __name__ == "__main__":
    success = weekly_training_pipeline()
    exit(0 if success else 1)
```

Run weekly:
```bash
0 3 * * 2 cd /path/to/lineupiq/packages/backend && uv run python weekly_training_pipeline.py
```
