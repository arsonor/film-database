// Dimensions usable in the game and their display/share metadata.

export const GAME_DIMENSIONS = [
  "categories",
  "themes",
  "atmospheres",
  "characters",
  "motivations",
  "messages",
  "cinema_types",
  "time_periods",
  "place_contexts",
] as const;

export type GameDimension = (typeof GAME_DIMENSIONS)[number];

export const DIMENSION_LABELS: Record<GameDimension, string> = {
  categories: "Genres",
  themes: "Themes",
  atmospheres: "Atmosphere",
  characters: "Characters",
  motivations: "Motivations",
  messages: "Message",
  cinema_types: "Cinema type",
  time_periods: "Time period",
  place_contexts: "Place",
};

// Color squares for shareable Wordle-style result
export const DIMENSION_SQUARES: Record<GameDimension, string> = {
  categories: "🟥",
  themes: "🟧",
  atmospheres: "🟨",
  characters: "🟩",
  motivations: "🟦",
  messages: "🟪",
  cinema_types: "🟫",
  time_periods: "⬜",
  place_contexts: "🟦",
};

// Group titles per dimension, keyed by `Math.floor(sort_order / 100)` (the "bucket").
// Mirrors the section labels in database/seed_taxonomy.sql.
export const GROUP_TITLES: Partial<Record<GameDimension, Record<number, string>>> = {
  cinema_types: {
    1: "Visual & aesthetics",
    2: "Movements & eras",
    3: "Industry & culture",
    4: "Narrative techniques",
    5: "Sub-genres & archetypes",
  },
  place_contexts: {
    1: "Natural environments",
    2: "Buildings & institutions",
    3: "Narrative settings",
    4: "None",
  },
  themes: {
    1: "Society",
    2: "Personal & psychological",
    3: "Crime & thriller",
    4: "Sci-fi & fantasy",
    5: "Art, sport & entertainment",
    6: "Miscellaneous",
  },
  characters: {
    1: "Group structure",
    2: "Age & identity",
    3: "Social status & traits",
    4: "Narrative devices",
    5: "Archetypes — human",
    6: "Non-human & creatures",
  },
  atmospheres: {
    1: "Light & joyful",
    2: "Tension",
    3: "Attention & immersion",
    4: "Dark & extreme",
    5: "Scale & tone",
  },
  motivations: {
    1: "Positive bonds",
    2: "Inner conflict",
    3: "Desire & transgression",
    4: "Conflict & struggle",
    5: "Epic quests",
  },
  messages: {
    1: "Values & ideology",
    2: "Comedy & satire",
    3: "Reflection",
    4: "Artistic expression",
  },
};

// time_periods uses a different scheme: sort_order 1–15 = chronological, 100+ = seasons
export function timePeriodBucket(sortOrder: number | null | undefined): number {
  if (sortOrder == null) return 0;
  return sortOrder < 100 ? 1 : 2;
}
export const TIME_PERIOD_GROUPS: Record<number, string> = {
  1: "Historical periods",
  2: "Seasons",
};
