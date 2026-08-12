/**
 * Taxonomy v2 sub-dimension groups.
 *
 * Sub-dimension names are encoded via sort_order blocks: one block of 100 per
 * named group (block = Math.floor(sort_order / 100)). This module is the static
 * label map for those blocks — the database stores the ordering, this stores the
 * names. Mirrors database/seed_taxonomy.sql and scripts/export_taxonomy.py.
 */

/** The 12 main genres — everything else in `categories` is a sub-genre. */
export const MAIN_GENRES = [
  "Drama",
  "Comedy",
  "Romance",
  "Historical",
  "Action",
  "Adventure",
  "Thriller",
  "Science-Fiction",
  "Fantasy",
  "Horror",
  "Musical",
  "Documentary",
] as const;

const MAIN_GENRE_SET = new Set<string>(MAIN_GENRES);

export function isMainGenre(name: string): boolean {
  return MAIN_GENRE_SET.has(name);
}

export interface TaxonomyGroup {
  /** sort_order block, i.e. Math.floor(sort_order / 100) */
  block: number;
  label: string;
  /** Optional umbrella heading shared by several consecutive blocks */
  parent?: string;
}

export const TAXONOMY_GROUPS: Record<string, TaxonomyGroup[]> = {
  categories: [
    { block: 1, label: "Main" },
    { block: 2, label: "Drama / Romance", parent: "Sub-genres" },
    { block: 3, label: "Comedy", parent: "Sub-genres" },
    { block: 4, label: "Thriller / Adventure", parent: "Sub-genres" },
    { block: 5, label: "Historical / Justice", parent: "Sub-genres" },
    { block: 6, label: "Sci-fi / Fantasy", parent: "Sub-genres" },
    { block: 7, label: "Horror", parent: "Sub-genres" },
    { block: 8, label: "Miscellaneous", parent: "Sub-genres" },
  ],
  themes: [
    { block: 1, label: "Society & World" },
    { block: 2, label: "Values & Reflection" },
    { block: 3, label: "Bonds & attachments", parent: "Human Relations" },
    { block: 4, label: "Desire & transgression", parent: "Human Relations" },
    { block: 5, label: "Interpersonal conflict", parent: "Human Relations" },
    { block: 6, label: "Crime & abuse of power", parent: "Human Relations" },
    { block: 7, label: "Wounds & burdens", parent: "Personal / Inner conflict" },
    { block: 8, label: "Drives & arcs", parent: "Personal / Inner conflict" },
    { block: 9, label: "Art", parent: "Art, Sport & Entertainment" },
    { block: 10, label: "Sport", parent: "Art, Sport & Entertainment" },
    { block: 11, label: "Entertainment", parent: "Art, Sport & Entertainment" },
    { block: 12, label: "Face to the unknown" },
  ],
  time_periods: [
    { block: 0, label: "Chronological" },
    { block: 1, label: "Time span" },
    { block: 2, label: "Seasons" },
  ],
  place_contexts: [
    { block: 1, label: "Environments" },
    { block: 2, label: "Buildings & institutions" },
    { block: 3, label: "Narrative settings" },
    { block: 4, label: "Vehicles" },
    { block: 5, label: "" },
  ],
  atmospheres: [
    { block: 1, label: "Light / Joyful" },
    { block: 2, label: "Dark / Extreme" },
    { block: 3, label: "Pace, Tension & Scale" },
    { block: 4, label: "Artistic Directing" },
  ],
  characters: [
    { block: 1, label: "Group structure" },
    { block: 2, label: "Age & identity" },
    { block: 3, label: "Social status & traits" },
    { block: 4, label: "Narrative devices" },
    { block: 5, label: "Archetypes — human" },
    { block: 6, label: "Non-human & creatures" },
  ],
  cinema_types: [
    { block: 1, label: "Visual techniques" },
    { block: 2, label: "Industry & culture" },
    { block: 3, label: "Sequencing", parent: "Narrative techniques" },
    { block: 4, label: "Voice & Dialogue", parent: "Narrative techniques" },
    { block: 5, label: "Movements & eras" },
  ],
};

export function blockOf(sortOrder: number | null | undefined): number | null {
  if (sortOrder === null || sortOrder === undefined) return null;
  return Math.floor(sortOrder / 100);
}

export function groupFor(dimension: string, sortOrder: number | null | undefined): TaxonomyGroup | undefined {
  const block = blockOf(sortOrder);
  if (block === null) return undefined;
  return TAXONOMY_GROUPS[dimension]?.find((g) => g.block === block);
}

/**
 * Split an ordered list into consecutive sub-dimension groups.
 * Items whose block has no label entry fall into an unlabelled group, which
 * callers render as a plain run of tags.
 */
export function groupItems<T>(
  dimension: string,
  items: T[],
  sortOrderOf: (item: T) => number | null | undefined,
): { group?: TaxonomyGroup; block: number | null; items: T[] }[] {
  const out: { group?: TaxonomyGroup; block: number | null; items: T[] }[] = [];
  for (const item of items) {
    const block = blockOf(sortOrderOf(item));
    const last = out[out.length - 1];
    if (last && last.block === block) {
      last.items.push(item);
    } else {
      out.push({ group: groupFor(dimension, sortOrderOf(item)), block, items: [item] });
    }
  }
  return out;
}
