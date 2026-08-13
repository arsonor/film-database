// Dimensions usable in the game and their display/share metadata.
//
// Taxonomy v2 (step 22): the 7 live dimensions, in the app-wide display order.
// Sub-dimension group titles are NOT duplicated here — they come from the
// single source of truth in `@/lib/taxonomyGroups`.

import { TAXONOMY_GROUPS, blockOf } from "@/lib/taxonomyGroups";

export const GAME_DIMENSIONS = [
  "categories",
  "themes",
  "time_periods",
  "place_contexts",
  "atmospheres",
  "characters",
  "cinema_types",
] as const;

export type GameDimension = (typeof GAME_DIMENSIONS)[number];

export const DIMENSION_LABELS: Record<GameDimension, string> = {
  categories: "Genre",
  themes: "Theme",
  time_periods: "Time Period",
  place_contexts: "Place",
  atmospheres: "Atmosphere",
  characters: "Character",
  cinema_types: "Cinema Type",
};

// Color squares for shareable Wordle-style result
export const DIMENSION_SQUARES: Record<GameDimension, string> = {
  categories: "🟥",
  themes: "🟧",
  time_periods: "⬜",
  place_contexts: "🟦",
  atmospheres: "🟨",
  characters: "🟩",
  cinema_types: "🟫",
};

/**
 * Sub-dimension title for a tag, keyed by its sort_order block.
 * Returns undefined for blocks with no label (e.g. place_contexts "no particular").
 */
export function groupTitleFor(
  dimension: string,
  sortOrder: number | null | undefined,
): string | undefined {
  const block = blockOf(sortOrder);
  if (block === null) return undefined;
  const group = TAXONOMY_GROUPS[dimension]?.find((g) => g.block === block);
  return group?.label || undefined;
}

/** The sort_order block a tag belongs to — group headers change when this changes. */
export function groupBucket(sortOrder: number | null | undefined): number {
  return blockOf(sortOrder) ?? 0;
}
