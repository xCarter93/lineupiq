# GitHub Actions Workflows

This directory contains automated workflows for LineupIQ model training and maintenance.

## Workflows

### 1. Bi-Weekly Model Training (`biweekly-model-training.yml`) [Required]

**Purpose:** Automatically retrain all ML models with the latest NFL data.

**Schedule:**
- Runs every **other Tuesday** at 6 AM UTC (1 AM EST)
- Only during NFL season (September - January)
- Automatically skips off-season weeks

**What it does:**
1. Determines optimal training window (sliding 3-season window)
2. Trains 32 models (QB, RB, WR, TE, K, DEF) with 30 Optuna trials each
3. Uploads trained models as artifacts (retained for 90 days)
4. Creates training summary with performance metrics
5. Opens GitHub issue if training fails

**Manual Triggering:**

You can manually trigger training anytime from the GitHub UI:

1. Go to **Actions** tab in GitHub
2. Select **"Bi-Weekly Model Training"**
3. Click **"Run workflow"**
4. (Optional) Customize parameters:
   - **Seasons:** e.g., `2023 2024 2025 2026` (or leave as `auto`)
   - **Trials:** e.g., `10` for quick test, `50` for thorough training
   - **Positions:** e.g., `QB RB` to train only specific positions

**Expected Duration:**
- Full training: 45-60 minutes (with 3-season window)
- Quick test: 10-15 minutes (with `--trials 10`)

**Artifacts Generated:**
- `models-{run-number}.zip` - All 32 trained .joblib files (90 days retention)
- `training-log-{run-number}.txt` - Full training logs (30 days retention)
- `training-summary-{run-number}.md` - Performance summary (90 days retention)

### 2. Weekly Data Sync (`weekly-data-sync.yml`) [Optional]

**Purpose:** Pre-fetch and cache latest NFL data before predictions are requested.

**Schedule:**
- Runs every **Wednesday** at 8 AM UTC (3 AM EST)
- After Tuesday night games, before most prediction requests

**Is this needed?**
**No!** Data is fetched automatically on-demand. This workflow is optional and only provides:
- Slightly faster first prediction after new games (data already cached)
- Verification that data sources are working

**How data works WITHOUT this workflow:**
1. User requests prediction for week 7
2. Feature pipeline runs: `build_features([2023, 2024, 2025, 2026])`
3. nflreadpy checks cache, fetches new week 7 data if needed (~5 seconds)
4. Fresh features computed with week 7 data
5. Model makes prediction with current data

**With this workflow:**
1. Wednesday morning: Workflow pre-fetches week 7 data
2. User requests prediction for week 7
3. Feature pipeline uses cached week 7 data (~instant)
4. Fresh features computed with week 7 data
5. Model makes prediction with current data

**Recommendation:** Start without this workflow. Add it later if first prediction latency becomes an issue.

## 2026 Season Schedule

Based on the bi-weekly strategy, training will automatically run:

| Week | Date | Includes |
|------|------|----------|
| Pre-season | Aug 27 | 2022-2025 data |
| Week 4 | Oct 1 | 2023-2025 + 2026 weeks 1-4 |
| Week 8 | Oct 29 | 2023-2025 + 2026 weeks 1-8 |
| Week 12 | Nov 26 | 2023-2025 + 2026 weeks 1-12 |
| Week 16 | Dec 24 | 2024-2025 + 2026 weeks 1-16 |
| Post-season | Jan 7 | 2024-2025 + 2026 full season |

## Monitoring

### Check Workflow Status

View all training runs:
```bash
# Via GitHub UI: Actions tab -> Bi-Weekly Model Training
```

### Download Trained Models

1. Go to completed workflow run
2. Scroll to "Artifacts" section
3. Download `models-{run-number}.zip`
4. Extract to `packages/backend/models/`

### View Training Logs

Either:
- Download `training-log-{run-number}.txt` artifact
- Or view inline logs in the workflow run

## Deployment

After successful training, models need to be deployed to production.

### Option 1: Manual Deployment

1. Download models artifact from successful run
2. Extract and copy to production server:
   ```bash
   scp models/*.joblib user@server:/path/to/lineupiq/packages/backend/models/
   ```

### Option 2: Automated Deployment

Add deployment step to the workflow (uncomment and customize):

```yaml
- name: Deploy models to production
  if: success()
  run: |
    # Example: S3 upload
    aws s3 sync packages/backend/models/ s3://lineupiq-models/production/

    # Example: SCP to server
    scp packages/backend/models/*.joblib deploy@server:/opt/lineupiq/models/

    # Example: Trigger API reload
    curl -X POST https://api.lineupiq.com/admin/reload-models
```

## Troubleshooting

### Training Failed

1. **Check the GitHub issue** created automatically
2. **Download training-log artifact** for full error context
3. **Common issues:**
   - nflreadpy API rate limits → Wait 1 hour and retry
   - Out of memory → Reduce trials or positions
   - Missing 2026 data → Manually trigger with `2023 2024 2025` seasons

### Manual Recovery

If automated training fails, run locally:

```bash
cd packages/backend

# Full training
uv run python scripts/train_all.py --seasons 2023 2024 2025 2026 --trials 30

# Quick test
uv run python scripts/train_all.py --quick --positions QB RB
```

### Skip a Scheduled Run

If you need to skip an automated run:

1. **Disable workflow temporarily:**
   - Go to Actions tab
   - Click on "Bi-Weekly Model Training"
   - Click "..." menu → "Disable workflow"
   - Re-enable after the scheduled time passes

2. **Or let it run but don't deploy:**
   - Workflow will complete
   - Simply don't deploy the generated models

## Cost Estimation

### GitHub Actions Free Tier
- 2,000 minutes/month for private repos
- Each training run: ~60 minutes
- **Bi-weekly schedule:** ~4 runs/month = 240 minutes (~12% of free tier)

### Paid Plans
If you exceed free tier:
- $0.008/minute = ~$0.48 per training run
- ~$2-3 per month for bi-weekly schedule

## Notifications

### Email Notifications

GitHub sends email by default for:
- ✅ Workflow success (optional, can disable)
- ❌ Workflow failure (recommended to keep enabled)

Configure in: GitHub Settings → Notifications → Actions

### Slack/Discord Integration

Add webhook notification step:

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
    text: |
      Training ${{ job.status }}
      Models: ${{ steps.verify.outputs.model_count }}/32
```

## Best Practices

1. **Monitor first few runs** - Check logs to ensure everything works
2. **Test manually first** - Run workflow manually before relying on schedule
3. **Keep artifacts** - 90-day retention gives you rollback options
4. **Version control models** - Consider storing models in Git LFS or S3 with versioning
5. **Validate predictions** - Spot-check predictions after each retrain
6. **Set up alerts** - Get notified on failures via email/Slack

## FAQ

**Q: Can I train more frequently than bi-weekly?**
A: Yes, edit the cron schedule in the workflow file. But bi-weekly is recommended for cost/benefit.

**Q: What if I want to train only QB models?**
A: Manually trigger the workflow with `positions: QB`

**Q: How do I rollback to previous models?**
A: Download models from an earlier successful run's artifacts

**Q: Can I run this locally instead?**
A: Yes: `cd packages/backend && uv run python scripts/train_all.py`

**Q: What if 2026 season hasn't started yet?**
A: The workflow automatically adjusts seasons. Before week 1, it uses 2022-2025.

## Support

For issues with:
- **Workflow configuration:** Check this README or open an issue
- **Training failures:** Check training logs and TRAINING.md
- **Model performance:** See SEASON_STRATEGY.md for monitoring guidelines
