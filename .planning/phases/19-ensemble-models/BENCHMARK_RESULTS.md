# Ensemble Benchmark Results

**Date:** 2026-01-20
**Holdout Season:** 2024
**Total Stats Benchmarked:** 21

## Executive Summary

This benchmark evaluates 5 strategies (lgbm_solo, xgb_solo, voting_simple, voting_weighted, stacking) across all skill position stats on 2024 holdout data.

### Key Findings

1. **Model Diversity:** Average correlation between LightGBM and XGBoost predictions: 0.890
   - <0.7: Good diversity (ensemble likely helps)
   - 0.7-0.9: Moderate diversity
   - >0.9: Low diversity (ensemble unlikely to help)

2. **Ensemble Performance:** Ensembles beat best single model in 1/21 stats (4.8%)

3. **Winning Strategies:**
   - lgbm_solo: 17/21 (81.0%)
   - xgb_solo: 3/21 (14.3%)
   - voting_weighted: 1/21 (4.8%)

## Summary Table

| Position | Stat | Best Strategy | Best MAE | Best R² | Correlation | Optimal Weights |
|----------|------|---------------|----------|---------|-------------|-----------------|
| QB | passing_yards | lgbm_solo | 4.73 | 0.993 | 0.950 | 0.20/0.80 |
| QB | passing_tds | lgbm_solo | 0.44 | 0.760 | 0.981 | 0.00/1.00 |
| QB | interceptions | lgbm_solo | 0.40 | 0.617 | 0.875 | 0.80/0.20 |
| QB | rushing_yards | lgbm_solo | 4.98 | 0.865 | 0.966 | 0.50/0.50 |
| QB | rushing_tds | lgbm_solo | 0.11 | 0.756 | 0.928 | 0.30/0.70 |
| QB | fumbles_lost | lgbm_solo | 0.13 | 0.780 | 0.582 | 0.55/0.45 |
| RB | rushing_yards | lgbm_solo | 6.16 | 0.949 | 0.990 | 0.95/0.05 |
| RB | rushing_tds | lgbm_solo | 0.15 | 0.738 | 0.980 | 0.80/0.20 |
| RB | carries | xgb_solo | 1.71 | 0.894 | 0.998 | 0.70/0.30 |
| RB | receiving_yards | lgbm_solo | 1.91 | 0.966 | 0.989 | 0.30/0.70 |
| RB | receptions | lgbm_solo | 0.35 | 0.918 | 0.989 | 0.60/0.40 |
| RB | receiving_tds | xgb_solo | 0.05 | 0.675 | 0.980 | 0.15/0.85 |
| RB | fumbles_lost | lgbm_solo | 0.08 | 0.055 | 0.885 | 1.00/0.00 |
| WR | receiving_yards | lgbm_solo | 5.90 | 0.936 | 0.979 | 0.55/0.45 |
| WR | receiving_tds | lgbm_solo | 0.17 | 0.665 | 0.956 | 0.05/0.95 |
| WR | receptions | xgb_solo | 0.63 | 0.885 | 0.992 | 0.20/0.80 |
| WR | fumbles_lost | lgbm_solo | 0.02 | 0.404 | 0.412 | 0.00/1.00 |
| TE | receiving_yards | lgbm_solo | 3.68 | 0.964 | 0.984 | 0.40/0.60 |
| TE | receiving_tds | lgbm_solo | 0.13 | 0.689 | 0.864 | 0.00/1.00 |
| TE | receptions | lgbm_solo | 0.47 | 0.911 | 0.984 | 0.40/0.60 |
| TE | fumbles_lost | voting_weighted | 0.03 | 0.004 | 0.434 | 0.00/1.00 |

## Full Results

Detailed breakdown for each position/stat showing all 5 strategies.

### QB_passing_yards

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.950
- **Optimal Weights:** LightGBM=0.20, XGBoost=0.80

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 4.73 | 0.993 ← BEST |
| xgb_solo | 27.78 | 0.881 |
| voting_simple | 42.47 | 0.724 |
| voting_weighted | 42.22 | 0.727 |
| stacking | 42.24 | 0.727 |

### QB_passing_tds

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.981
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.44 | 0.760 ← BEST |
| xgb_solo | 0.48 | 0.719 |
| voting_simple | 0.62 | 0.519 |
| voting_weighted | 0.62 | 0.527 |
| stacking | 0.61 | 0.531 |

### QB_interceptions

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.875
- **Optimal Weights:** LightGBM=0.80, XGBoost=0.20

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.40 | 0.617 ← BEST |
| xgb_solo | 0.51 | 0.418 |
| voting_simple | 0.66 | 0.024 |
| voting_weighted | 0.66 | 0.011 |
| stacking | 0.69 | 0.022 |

### QB_rushing_yards

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.966
- **Optimal Weights:** LightGBM=0.50, XGBoost=0.50

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 4.98 | 0.865 ← BEST |
| xgb_solo | 5.27 | 0.871 |
| voting_simple | 7.75 | 0.693 |
| voting_weighted | 7.75 | 0.693 |
| stacking | 7.75 | 0.692 |

### QB_rushing_tds

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.928
- **Optimal Weights:** LightGBM=0.30, XGBoost=0.70

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.11 | 0.756 ← BEST |
| xgb_solo | 0.15 | 0.584 |
| voting_simple | 0.17 | 0.413 |
| voting_weighted | 0.17 | 0.415 |
| stacking | 0.17 | 0.412 |

### QB_fumbles_lost

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.582
- **Optimal Weights:** LightGBM=0.55, XGBoost=0.45

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.13 | 0.780 ← BEST |
| xgb_solo | 0.28 | 0.078 |
| voting_simple | 0.30 | -0.036 |
| voting_weighted | 0.30 | -0.042 |
| stacking | 0.30 | -0.004 |

### RB_rushing_yards

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.990
- **Optimal Weights:** LightGBM=0.95, XGBoost=0.05

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 6.16 | 0.949 ← BEST |
| xgb_solo | 8.33 | 0.901 |
| voting_simple | 11.34 | 0.791 |
| voting_weighted | 11.23 | 0.791 |
| stacking | 11.46 | 0.787 |

### RB_rushing_tds

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.980
- **Optimal Weights:** LightGBM=0.80, XGBoost=0.20

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.15 | 0.738 ← BEST |
| xgb_solo | 0.18 | 0.668 |
| voting_simple | 0.21 | 0.498 |
| voting_weighted | 0.21 | 0.495 |
| stacking | 0.21 | 0.498 |

### RB_carries

- **Best Strategy:** xgb_solo
- **Correlation:** 0.998
- **Optimal Weights:** LightGBM=0.70, XGBoost=0.30

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 1.74 | 0.890 |
| xgb_solo | 1.71 | 0.894 ← BEST |
| voting_simple | 2.18 | 0.821 |
| voting_weighted | 2.18 | 0.821 |
| stacking | 2.18 | 0.820 |

### RB_receiving_yards

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.989
- **Optimal Weights:** LightGBM=0.30, XGBoost=0.70

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 1.91 | 0.966 ← BEST |
| xgb_solo | 2.97 | 0.911 |
| voting_simple | 4.90 | 0.740 |
| voting_weighted | 4.89 | 0.741 |
| stacking | 4.87 | 0.742 |

### RB_receptions

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.989
- **Optimal Weights:** LightGBM=0.60, XGBoost=0.40

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.35 | 0.918 ← BEST |
| xgb_solo | 0.45 | 0.862 |
| voting_simple | 0.58 | 0.756 |
| voting_weighted | 0.58 | 0.756 |
| stacking | 0.57 | 0.756 |

### RB_receiving_tds

- **Best Strategy:** xgb_solo
- **Correlation:** 0.980
- **Optimal Weights:** LightGBM=0.15, XGBoost=0.85

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.05 | 0.649 |
| xgb_solo | 0.05 | 0.675 ← BEST |
| voting_simple | 0.07 | 0.330 |
| voting_weighted | 0.07 | 0.322 |
| stacking | 0.07 | 0.326 |

### RB_fumbles_lost

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.885
- **Optimal Weights:** LightGBM=1.00, XGBoost=0.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.08 | 0.055 ← BEST |
| xgb_solo | 0.08 | 0.031 |
| voting_simple | 0.08 | 0.013 |
| voting_weighted | 0.08 | 0.012 |
| stacking | 0.08 | 0.012 |

### WR_receiving_yards

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.979
- **Optimal Weights:** LightGBM=0.55, XGBoost=0.45

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 5.90 | 0.936 ← BEST |
| xgb_solo | 9.00 | 0.871 |
| voting_simple | 11.25 | 0.782 |
| voting_weighted | 11.24 | 0.782 |
| stacking | 11.22 | 0.783 |

### WR_receiving_tds

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.956
- **Optimal Weights:** LightGBM=0.05, XGBoost=0.95

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.17 | 0.665 ← BEST |
| xgb_solo | 0.19 | 0.556 |
| voting_simple | 0.22 | 0.439 |
| voting_weighted | 0.21 | 0.446 |
| stacking | 0.21 | 0.445 |

### WR_receptions

- **Best Strategy:** xgb_solo
- **Correlation:** 0.992
- **Optimal Weights:** LightGBM=0.20, XGBoost=0.80

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.64 | 0.886 |
| xgb_solo | 0.63 | 0.885 ← BEST |
| voting_simple | 0.79 | 0.810 |
| voting_weighted | 0.79 | 0.812 |
| stacking | 0.79 | 0.812 |

### WR_fumbles_lost

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.412
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.02 | 0.404 ← BEST |
| xgb_solo | 0.03 | 0.022 |
| voting_simple | 0.03 | -0.027 |
| voting_weighted | 0.03 | -0.001 |
| stacking | 0.03 | -0.003 |

### TE_receiving_yards

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.984
- **Optimal Weights:** LightGBM=0.40, XGBoost=0.60

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 3.68 | 0.964 ← BEST |
| xgb_solo | 5.59 | 0.914 |
| voting_simple | 8.65 | 0.753 |
| voting_weighted | 8.65 | 0.752 |
| stacking | 8.64 | 0.752 |

### TE_receiving_tds

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.864
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.13 | 0.689 ← BEST |
| xgb_solo | 0.15 | 0.454 |
| voting_simple | 0.17 | 0.388 |
| voting_weighted | 0.16 | 0.404 |
| stacking | 0.15 | 0.401 |

### TE_receptions

- **Best Strategy:** lgbm_solo
- **Correlation:** 0.984
- **Optimal Weights:** LightGBM=0.40, XGBoost=0.60

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.47 | 0.911 ← BEST |
| xgb_solo | 0.48 | 0.921 |
| voting_simple | 0.77 | 0.764 |
| voting_weighted | 0.77 | 0.765 |
| stacking | 0.76 | 0.765 |

### TE_fumbles_lost

- **Best Strategy:** voting_weighted
- **Correlation:** 0.434
- **Optimal Weights:** LightGBM=0.00, XGBoost=1.00

| Strategy | MAE | R² |
|----------|-----|----|
| lgbm_solo | 0.03 | 0.359 |
| xgb_solo | 0.03 | 0.025 |
| voting_simple | 0.03 | 0.001 |
| voting_weighted | 0.03 | 0.004 ← BEST |
| stacking | 0.03 | 0.001 |

## Analysis

### Model Diversity

- High diversity (correlation < 0.7): 3/21 stats
- Moderate diversity (0.7-0.9): 3/21 stats
- Low diversity (>= 0.9): 15/21 stats

### Ensemble vs Single Model Performance

**Stats where ensemble wins:** 1/21

Top ensemble improvements:
- TE_fumbles_lost: 6.2% improvement

**Stats where single model wins:** 20/21

Worst ensemble degradations:
- QB_passing_yards: 792.8% worse
- RB_receiving_yards: 154.5% worse
- TE_receiving_yards: 134.5% worse
- QB_fumbles_lost: 128.8% worse
- WR_receiving_yards: 90.1% worse

## Recommendation

**Keep single models** - Ensembles only beat single models on 1/21 (4.8%) stats.

Findings:
- High correlation (0.890) indicates low model diversity
- Single models already performing well, ensemble overhead not justified
- Recommend improving base models or adding more diverse estimators before revisiting ensembles

## Methodology

- **Training Data:** 2022-2023 seasons
- **Holdout Data:** 2024 season (strict holdout, never seen during training)
- **Strategies Tested:**
  1. `lgbm_solo`: LightGBM model alone
  2. `xgb_solo`: XGBoost model alone
  3. `voting_simple`: Simple averaging (equal weights)
  4. `voting_weighted`: Weighted averaging (optimal weights via grid search)
  5. `stacking`: Ridge meta-learner with 5-fold CV
- **Metrics:** MAE (lower is better), R² (higher is better)
- **Best Strategy:** Selected by lowest MAE on holdout data
