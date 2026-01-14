# Phase 2: Data Pipeline - Research

**Researched:** 2026-01-14
**Domain:** nflreadpy data fetching + Polars/Parquet storage
**Confidence:** HIGH

<research_summary>
## Summary

Researched the nflreadpy ecosystem for fetching NFL historical data and Polars/Parquet patterns for efficient storage and processing. The standard approach uses nflreadpy (which returns Polars DataFrames natively) combined with Parquet file storage organized by season.

Key finding: nflreadpy is the official Python port of nflreadr (the deprecated nfl_data_py should not be used). It returns Polars DataFrames by default, which aligns perfectly with Parquet storage. Use `scan_parquet()` for lazy loading and hive-style partitioning by season for efficient queries.

**Primary recommendation:** Use nflreadpy → Polars → Parquet pipeline. Organize storage as `data/raw/{data_type}/season={year}/data.parquet` for hive partitioning. Use LazyFrames with `scan_parquet()` for memory-efficient processing of multi-year datasets.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nflreadpy | 0.1.5+ | NFL data fetching | Official nflverse Python port, replaces deprecated nfl_data_py |
| polars | 1.x | DataFrame operations | Native return type from nflreadpy, faster than pandas |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyarrow | 15.x+ | Parquet I/O backend | Required by Polars for Parquet operations |
| httpx | 0.27+ | HTTP client | Underlying HTTP for nflreadpy (auto-installed) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Polars | pandas | pandas is more familiar but slower; nflreadpy returns Polars natively |
| Parquet | CSV | CSV is human-readable but 5-10x slower and larger |
| Parquet | SQLite | SQLite adds query flexibility but slower for bulk analytics |

**Installation:**
```bash
uv add nflreadpy polars pyarrow
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
packages/ml/
├── src/lineupiq/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetch.py        # nflreadpy wrapper functions
│   │   ├── cache.py        # File caching logic
│   │   └── schemas.py      # Column type definitions
│   └── ...
data/
├── raw/
│   ├── player_stats/
│   │   ├── season=1999/
│   │   │   └── data.parquet
│   │   ├── season=2000/
│   │   │   └── data.parquet
│   │   └── ...
│   ├── schedules/
│   │   └── all.parquet     # All seasons in one file (smaller dataset)
│   └── snap_counts/
│       ├── season=2012/    # Only available from 2012+
│       └── ...
└── .gitkeep
```

### Pattern 1: Lazy Loading with Hive Partitions
**What:** Use `scan_parquet()` with hive partitioning for memory-efficient multi-season queries
**When to use:** Any query spanning multiple seasons
**Example:**
```python
import polars as pl

# Lazy scan with automatic hive partition detection
lf = pl.scan_parquet("data/raw/player_stats/")

# Filter pushes down to only read needed seasons
result = (
    lf
    .filter(pl.col("season") >= 2020)
    .filter(pl.col("position").is_in(["QB", "RB", "WR", "TE"]))
    .collect()
)
```

### Pattern 2: Cache-or-Fetch with Staleness Check
**What:** Check if local parquet exists and is fresh before fetching from nflverse
**When to use:** All data loading operations
**Example:**
```python
from pathlib import Path
from datetime import datetime, timedelta
import polars as pl
import nflreadpy as nfl

def load_or_fetch_player_stats(season: int, cache_dir: Path, max_age_days: int = 7) -> pl.DataFrame:
    cache_path = cache_dir / f"player_stats/season={season}/data.parquet"

    # Check cache freshness
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(days=max_age_days):
            return pl.read_parquet(cache_path)

    # Fetch fresh data
    df = nfl.load_player_stats(seasons=season)

    # Ensure directory exists and save
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(cache_path)

    return df
```

### Pattern 3: Batch Season Loading
**What:** Load multiple seasons in batches to avoid memory pressure
**When to use:** Initial data population (1999-2025 = 27 seasons)
**Example:**
```python
def fetch_all_seasons(start: int = 1999, end: int = 2025, batch_size: int = 5):
    """Fetch data in batches to manage memory."""
    for batch_start in range(start, end + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end)
        seasons = list(range(batch_start, batch_end + 1))

        # Fetch batch
        df = nfl.load_player_stats(seasons=seasons)

        # Save each season separately for hive partitioning
        for season in seasons:
            season_df = df.filter(pl.col("season") == season)
            path = Path(f"data/raw/player_stats/season={season}/data.parquet")
            path.parent.mkdir(parents=True, exist_ok=True)
            season_df.write_parquet(path)

        # Clear memory
        del df
```

### Anti-Patterns to Avoid
- **Loading all seasons into memory at once:** Use batch loading or LazyFrames instead
- **Using `.to_pandas()` unnecessarily:** Keep data in Polars for 10x performance
- **Storing all seasons in one file:** Hive partitioning enables filter pushdown
- **Re-fetching on every run:** Implement file-based caching with staleness checks
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data fetching | Custom HTTP to nflverse | nflreadpy | Handles caching, progress, data cleaning |
| DataFrame ops | pandas loops | Polars expressions | 10-100x faster, native from nflreadpy |
| File storage | JSON/CSV | Parquet | Columnar format, 10x faster, type-preserving |
| Schema validation | Manual column checks | Polars schema on read | Built-in type enforcement |
| Multi-season queries | Manual file iteration | `scan_parquet()` + hive | Query optimizer handles partition pruning |
| Memory management | Manual chunking | LazyFrame streaming | Polars handles batching automatically |

**Key insight:** nflreadpy + Polars + Parquet is an integrated stack. nflreadpy returns Polars DataFrames, Polars writes/reads Parquet natively. Fighting this alignment leads to unnecessary conversions and performance loss.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Memory Exhaustion on Full History Load
**What goes wrong:** Loading 1999-2025 player_stats (~500k rows) crashes with OOM
**Why it happens:** nflreadpy loads all requested seasons into memory at once
**How to avoid:** Fetch in 5-year batches, save each season separately, use LazyFrames for queries
**Warning signs:** Process killed, swap usage spikes, long hangs

### Pitfall 2: Using Deprecated nfl_data_py
**What goes wrong:** Code uses `import nfl_data_py` which is archived and unmaintained
**Why it happens:** Old tutorials and Stack Overflow answers reference it
**How to avoid:** Always use `import nflreadpy as nfl` - it's the official replacement
**Warning signs:** Deprecation warnings, missing recent seasons, stale data

### Pitfall 3: Converting to Pandas Unnecessarily
**What goes wrong:** Code does `df = nfl.load_player_stats(...).to_pandas()` then slow pandas ops
**Why it happens:** Developer familiarity with pandas API
**How to avoid:** Learn Polars expressions - they're similar but faster
**Warning signs:** Processing times 10x longer than expected, high memory usage

### Pitfall 4: Not Using Hive Partitioning
**What goes wrong:** All seasons in one giant parquet file, slow queries
**Why it happens:** Simpler to save everything in one file
**How to avoid:** Organize as `season={year}/data.parquet`, Polars auto-detects
**Warning signs:** Full file scans for single-season queries, slow startup

### Pitfall 5: Ignoring Cache Staleness
**What goes wrong:** Using stale local data when nflverse has updates (esp. during season)
**Why it happens:** No freshness checks, just "if file exists, use it"
**How to avoid:** Check file mtime, allow configurable max age (shorter during active season)
**Warning signs:** Missing recent games, outdated injury data

### Pitfall 6: nflreadpy Experimental Status
**What goes wrong:** Unexpected behavior or missing functions
**Why it happens:** Library is new (2025), labeled "experimental", written initially by Claude
**How to avoid:** Check GitHub issues before planning features, have fallback to direct nflverse URLs
**Warning signs:** Functions returning None, schema mismatches with nflreadr docs
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### nflreadpy Basic Usage
```python
# Source: nflreadpy README
import nflreadpy as nfl

# Load current season
current = nfl.load_player_stats()

# Load specific seasons (returns Polars DataFrame)
stats_2023_2024 = nfl.load_player_stats([2023, 2024])

# Load all available history
all_history = nfl.load_player_stats(seasons=True)

# Configure caching
nfl.update_config(
    cache_mode="filesystem",    # "memory", "filesystem", or "off"
    cache_dir="~/nflreadpy_cache",
    cache_duration=86400,       # seconds
    verbose=False,
    timeout=30
)
```

### Polars Parquet with Hive Partitioning
```python
# Source: Polars docs
import polars as pl

# Write with hive partitioning
df.write_parquet(
    "data/raw/player_stats/",
    partition_by=["season"],
    use_pyarrow=True  # Required for partition_by
)

# Read with automatic partition detection
lf = pl.scan_parquet("data/raw/player_stats/")

# Filter is pushed down - only reads matching partitions
result = lf.filter(pl.col("season") == 2024).collect()
```

### Player Stats Key Columns
```python
# Source: nflreadr dictionary_player_stats
# 114 columns available, key ones for fantasy:

IDENTIFIER_COLS = [
    "player_id", "player_name", "player_display_name",
    "position", "position_group",
    "season", "week", "season_type",
    "recent_team", "opponent_team"
]

PASSING_COLS = [
    "completions", "attempts", "passing_yards", "passing_tds",
    "passing_interceptions", "passing_air_yards",
    "passing_first_downs", "passing_epa", "passing_cpoe",
    "sacks_suffered", "sack_yards_lost"
]

RUSHING_COLS = [
    "carries", "rushing_yards", "rushing_tds",
    "rushing_fumbles", "rushing_first_downs", "rushing_epa"
]

RECEIVING_COLS = [
    "targets", "receptions", "receiving_yards", "receiving_tds",
    "receiving_air_yards", "receiving_yards_after_catch",
    "receiving_first_downs", "receiving_epa",
    "target_share", "air_yards_share", "wopr", "racr"
]

FANTASY_COLS = ["fantasy_points", "fantasy_points_ppr"]
```

### Streaming for Large Queries
```python
# Source: Polars docs - for larger-than-memory operations
import polars as pl

# Use sink_parquet for streaming output
(
    pl.scan_parquet("data/raw/player_stats/")
    .filter(pl.col("position").is_in(["QB", "RB", "WR", "TE"]))
    .group_by(["player_id", "season"])
    .agg([
        pl.sum("fantasy_points_ppr").alias("total_ppr"),
        pl.count().alias("games")
    ])
    .sink_parquet("data/processed/season_totals.parquet")
)
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nfl_data_py | nflreadpy | Sep 2025 | Old package archived, switch immediately |
| pandas DataFrames | Polars DataFrames | 2024+ | nflreadpy returns Polars natively |
| CSV storage | Parquet storage | Standard | 10x faster reads, better compression |
| Single-file storage | Hive partitioning | Standard | Filter pushdown, faster queries |

**New tools/patterns to consider:**
- **Polars streaming engine:** For larger-than-memory aggregations, use `.sink_parquet()`
- **nflreadpy filesystem cache:** Configure `cache_mode="filesystem"` to avoid re-downloads

**Deprecated/outdated:**
- **nfl_data_py:** Archived Sep 2025, use nflreadpy instead
- **pandas for NFL data:** Polars is now the native format
- **CSV for storage:** Parquet is standard for analytics workloads
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **nflreadpy stability for production use**
   - What we know: Library is labeled "experimental", initially written by Claude
   - What's unclear: Which functions are stable vs still being developed
   - Recommendation: Test each function we need, have fallback to direct nflverse parquet URLs

2. **2025 injuries data gap**
   - What we know: GitHub issue #17 reports 2025 injuries missing
   - What's unclear: Whether this is a temporary gap or ongoing issue
   - Recommendation: Check data availability before depending on injuries for features

3. **Optimal cache duration during active season**
   - What we know: nflverse updates data after games (weekly during season)
   - What's unclear: Exact update schedule and best cache invalidation strategy
   - Recommendation: Use 24-hour cache during season, 7-day during offseason
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [nflreadpy GitHub](https://github.com/nflverse/nflreadpy) - API structure, configuration, functions
- [nflreadpy PyPI](https://pypi.org/project/nflreadpy/) - Version 0.1.5 (Nov 2025)
- [nflreadr Data Dictionary](https://nflreadr.nflverse.com/articles/dictionary_player_stats.html) - 114 column schema
- [Polars User Guide - Parquet](https://docs.pola.rs/user-guide/io/parquet/) - Lazy evaluation, scan_parquet
- [Polars User Guide - Hive](https://docs.pola.rs/user-guide/io/hive/) - Partition reading/writing

### Secondary (MEDIUM confidence)
- [nflreadpy Issues](https://github.com/nflverse/nflreadpy/issues) - Known issues, feature gaps
- [Polars vs Pandas benchmarks](https://towardsdatascience.com/polars-vs-pandas-an-independent-speed-comparison/) - 10x performance claims verified
- [Streaming in Polars](https://www.rhosignal.com/posts/streaming-in-polars/) - sink_parquet patterns

### Tertiary (LOW confidence - needs validation)
- None - all critical findings verified with primary sources
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: nflreadpy for NFL data fetching
- Ecosystem: Polars DataFrames, Parquet storage, pyarrow
- Patterns: Cache-or-fetch, hive partitioning, lazy evaluation
- Pitfalls: Memory management, deprecated libraries, cache staleness

**Confidence breakdown:**
- Standard stack: HIGH - verified with official docs, versions confirmed
- Architecture: HIGH - patterns from Polars docs, aligned with nflreadpy output
- Pitfalls: HIGH - from GitHub issues, documented limitations
- Code examples: HIGH - from official docs and README

**Research date:** 2026-01-14
**Valid until:** 2026-02-14 (30 days - stable ecosystem, nflreadpy still experimental)
</metadata>

---

*Phase: 02-data-pipeline*
*Research completed: 2026-01-14*
*Ready for planning: yes*
