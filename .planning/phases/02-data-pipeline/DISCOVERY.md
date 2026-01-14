# Phase 2 Discovery: nflreadpy API Patterns

**Level:** 2 (Standard Research)
**Date:** 2026-01-14
**Phase:** 02-data-pipeline

## Research Questions

1. What is the nflreadpy API structure?
2. What data columns are available in player_stats?
3. How should we handle large dataset loading?
4. What's the schedule data schema for weather/venue?

## Findings

### nflreadpy API

nflreadpy is a Python port of the R nflreadr package. Key characteristics:

**Return Type:** Polars DataFrames (not pandas) - convert with `.to_pandas()` if needed.

**Seasons Parameter:**
- `None`: Current season
- `True`: All available history
- `int`: Specific season
- `list[int]`: Multiple seasons

**Key Functions for this project:**
| Function | Data | Years | Use Case |
|----------|------|-------|----------|
| `load_player_stats()` | Weekly stats (114 cols) | 1999+ | Primary training data |
| `load_schedules()` | Games, weather, venues | All | Weather/opponent features |
| `load_pbp()` | Play-by-play (372+ cols) | 1999+ | Advanced feature extraction |
| `load_snap_counts()` | Snap participation | 2012+ | Opportunity metrics |

### Player Stats Schema (114 columns)

**Verified via live test (2024 data):**

**Identifiers:**
- `player_id`, `player_name`, `player_display_name`
- `position`, `position_group`
- `season`, `week`, `season_type`
- `team`, `opponent_team`

**Passing (QB stats):**
- `completions`, `attempts`, `passing_yards`, `passing_tds`
- `passing_interceptions`, `passing_2pt_conversions`
- `passing_air_yards`, `passing_yards_after_catch`
- `passing_first_downs`, `passing_epa`, `passing_cpoe`
- `sacks_suffered`, `sack_yards_lost`, `sack_fumbles`, `sack_fumbles_lost`

**Rushing (RB/QB stats):**
- `carries`, `rushing_yards`, `rushing_tds`
- `rushing_fumbles`, `rushing_fumbles_lost`
- `rushing_first_downs`, `rushing_epa`, `rushing_2pt_conversions`

**Receiving (WR/TE/RB stats):**
- `receptions`, `targets`, `receiving_yards`, `receiving_tds`
- `receiving_fumbles`, `receiving_fumbles_lost`
- `receiving_air_yards`, `receiving_yards_after_catch`
- `receiving_first_downs`, `receiving_epa`, `receiving_2pt_conversions`
- `target_share`, `air_yards_share`, `wopr`, `racr`

**Fantasy (pre-calculated):**
- `fantasy_points` (standard scoring)
- `fantasy_points_ppr` (PPR scoring)

### Schedules Schema (46 columns)

**Weather/Venue Fields:**
- `roof`: dome/outdoors/open/closed
- `surface`: grass/fieldturf/etc
- `temp`: temperature (integer)
- `wind`: wind speed (integer)
- `stadium`, `stadium_id`

**Game Context:**
- `game_id`, `season`, `game_type`, `week`
- `home_team`, `away_team`
- `home_score`, `away_score`

### Data Volume Estimates

From live testing:
- 1 year of player_stats: ~18,981 rows
- 3 years of player_stats: ~56,443 rows
- Full history (1999-2024 = 26 years): ~400,000-500,000 rows estimated

**Recommendation:** Load in batches (5-year chunks) to avoid memory issues.

### Positions Available

26 unique positions including: QB, RB, WR, TE, FB, K, and defensive positions.

**Skill positions to focus on:** QB, RB, WR, TE (per PROJECT.md)

## Data Storage Strategy

**Recommended approach:**
1. Store raw data as Parquet files (efficient, preserves types)
2. Organize by data type: `data/raw/{data_type}/{season}.parquet`
3. Implement file-based caching with staleness checks
4. Load from Parquet on subsequent runs

**Directory structure:**
```
data/
  raw/
    player_stats/
      2024.parquet
      2023.parquet
      ...
    schedules/
      all.parquet
```

## Decisions for Phase 2

1. **Use Polars DataFrames internally** - nflreadpy returns Polars, keep for performance
2. **Parquet for storage** - efficient, type-preserving, fast reads
3. **Batch loading** - 5-year chunks to manage memory
4. **File-based cache** - check file existence and staleness before re-fetching

## Sources

- [nflreadpy Documentation](https://nflreadpy.nflverse.com/)
- [nflreadpy Load Functions](https://nflreadpy.nflverse.com/api/load_functions/)
- [GitHub: nflverse/nflreadpy](https://github.com/nflverse/nflreadpy)
- [nflreadr Data Dictionary](https://nflreadr.nflverse.com/)
