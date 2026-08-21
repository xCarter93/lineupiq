/**
 * NFL season/week derivation.
 *
 * A season is named for the calendar year it kicks off in, but runs into
 * February of the next year — so anything before March belongs to the
 * previous season.
 */

const FIRST_TRAINING_SEASON = 2016;
const COVID_SEASON = 2020; // excluded from training: no crowds, broken schedule
const REGULAR_SEASON_WEEKS = 18;

/** The season the NFL is currently in (2026 season = Sept 2026 through Feb 2027). */
export function getCurrentSeason(): number {
  const now = new Date();
  return now.getMonth() >= 2 ? now.getFullYear() : now.getFullYear() - 1;
}

/** The most recent season with a full slate of results — what models validate against. */
export function getLastCompletedSeason(): number {
  return getCurrentSeason() - 1;
}

/**
 * Week 1 kicks off the Thursday after Labor Day (first Monday in September),
 * and each subsequent week rolls over on Thursday.
 */
function getSeasonStart(season: number): Date {
  const september1 = new Date(season, 8, 1);
  const daysToLaborDay = (8 - september1.getDay()) % 7;
  return new Date(season, 8, 1 + daysToLaborDay + 3);
}

/**
 * Current NFL week, clamped to the 1-18 regular season.
 * Used when simulation mode is not active.
 */
export function getCurrentNFLWeek(season: number = getCurrentSeason()): number {
  const now = new Date();
  const seasonStart = getSeasonStart(season);

  if (now < seasonStart) {
    return 1;
  }

  const daysSinceStart = Math.floor(
    (now.getTime() - seasonStart.getTime()) / (1000 * 60 * 60 * 24)
  );
  const week = Math.floor(daysSinceStart / 7) + 1;

  return Math.min(Math.max(week, 1), REGULAR_SEASON_WEEKS);
}

/** Seasons available to train on for a given target season (2016 onward, minus 2020). */
export function getDefaultTrainingSeasons(
  targetSeason: number = getCurrentSeason()
): number[] {
  const seasons: number[] = [];
  for (let season = FIRST_TRAINING_SEASON; season < targetSeason; season++) {
    if (season !== COVID_SEASON) {
      seasons.push(season);
    }
  }
  return seasons;
}
