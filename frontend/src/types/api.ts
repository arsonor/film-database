// =============================================================================
// Add Film workflow types
// =============================================================================

export interface TMDBSearchResult {
  tmdb_id: number;
  title: string;
  original_title: string;
  release_date: string | null;
  overview: string | null;
  poster_url: string | null;
  already_in_db: boolean;
}

export interface EnrichmentPreview {
  film: Record<string, unknown>;
  titles: Record<string, unknown>[];
  categories: string[];
  historic_subcategories: string[];
  crew: Record<string, unknown>[];
  cast: Record<string, unknown>[];
  studios: Record<string, unknown>[];
  streaming_platforms: string[];
  enrichment: Record<string, unknown>;
  keywords: string[];
  production_countries: string[];
  languages: Record<string, unknown>[];
  enrichment_failed: boolean;
}

// =============================================================================
// Film Detail types
// =============================================================================

export interface FilmTitle {
  language_code: string;
  language_name: string;
  title: string;
  is_original: boolean;
}

export interface CrewMember {
  person_id: number;
  firstname: string | null;
  lastname: string;
  role: string;
  photo_url: string | null;
}

export interface CastMember {
  person_id: number;
  firstname: string | null;
  lastname: string;
  character_name: string | null;
  cast_order: number | null;
  photo_url: string | null;
}

export interface FilmSetPlace {
  continent: string | null;
  country: string | null;
  state_city: string | null;
  place_type: string;
}

export interface SourceOut {
  source_type: string;
  source_title: string | null;
  author: string | null;
}

export interface AwardOut {
  festival_name: string;
  category: string | null;
  year: number | null;
  result: string | null;
}

export interface FilmRelation {
  related_film_id: number;
  related_film_title: string;
  relation_type: string;
  poster_url: string | null;
}

export interface UserFilmStatus {
  seen: boolean;
  favorite: boolean;
  watchlist: boolean;
  rating: number | null;
  notes?: string;
}

export interface FilmDetail {
  film_id: number;
  original_title: string;
  duration: number | null;
  color: boolean;
  first_release_date: string | null;
  summary: string | null;
  user_status: UserFilmStatus | null;
  poster_url: string | null;
  backdrop_url: string | null;
  imdb_id: string | null;
  tmdb_id: number | null;
  budget: number | null;
  revenue: number | null;
  titles: FilmTitle[];
  categories: string[];
  cinema_types: string[];
  themes: string[];
  characters: string[];
  motivations: string[];
  atmospheres: string[];
  messages: string[];
  time_periods: string[];
  place_contexts: string[];
  set_places: FilmSetPlace[];
  crew: CrewMember[];
  cast: CastMember[];
  studios: string[];
  sources: SourceOut[];
  awards: AwardOut[];
  streaming_platforms: string[];
  sequels: FilmRelation[];
}

// =============================================================================
// Film List types
// =============================================================================

export interface FilmListItem {
  film_id: number;
  original_title: string;
  first_release_date: string | null;
  duration: number | null;
  poster_url: string | null;
  user_status: UserFilmStatus | null;
  categories: string[];
  director: string | null;
}

export interface PaginatedFilms {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  items: FilmListItem[];
}

export interface TaxonomyItem {
  id: number;
  name: string;
  film_count: number | null;
  sort_order: number | null;
}

export interface TaxonomyList {
  dimension: string;
  items: TaxonomyItem[];
}

export interface GeographySearchResult {
  geography_id: number;
  label: string;
  continent: string | null;
  country: string | null;
  state_city: string | null;
  film_count: number;
}

export interface CountryItem {
  country: string;
  film_count: number;
}

export interface StatsResponse {
  total_films: number;
  seen: number;
  unseen: number;
  by_decade: { decade: number; count: number }[];
  top_categories: { name: string; count: number }[];
  top_countries: { name: string; count: number }[];
}

export interface TagFilter {
  include: string[];
  exclude: string[];
  mode: "or" | "and";
}

export const EMPTY_TAG_FILTER: TagFilter = { include: [], exclude: [], mode: "or" };

export interface FilterState {
  q: string;
  categories: TagFilter;
  themes: TagFilter;
  atmospheres: TagFilter;
  characters: TagFilter;
  motivations: TagFilter;
  messages: TagFilter;
  cinema_types: TagFilter;
  time_periods: TagFilter;
  place_contexts: TagFilter;
  studios: TagFilter;
  location: string;
  language: string;
  source: string;
  year_min: number | null;
  year_max: number | null;
  seen: boolean | null;
  sort_by: "year" | "title" | "duration";
  sort_order: "asc" | "desc";
  page: number;
  per_page: number;
}

export const TAXONOMY_DIMENSIONS = [
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

export type TaxonomyDimension = (typeof TAXONOMY_DIMENSIONS)[number];

export const DEFAULT_FILTER_STATE: FilterState = {
  q: "",
  categories: { ...EMPTY_TAG_FILTER },
  themes: { ...EMPTY_TAG_FILTER },
  atmospheres: { ...EMPTY_TAG_FILTER },
  characters: { ...EMPTY_TAG_FILTER },
  motivations: { ...EMPTY_TAG_FILTER },
  messages: { ...EMPTY_TAG_FILTER },
  cinema_types: { ...EMPTY_TAG_FILTER },
  time_periods: { ...EMPTY_TAG_FILTER },
  place_contexts: { ...EMPTY_TAG_FILTER },
  studios: { ...EMPTY_TAG_FILTER },
  location: "",
  language: "",
  source: "",
  year_min: null,
  year_max: null,
  seen: null,
  sort_by: "year",
  sort_order: "desc",
  page: 1,
  per_page: 24,
};

export const ARRAY_FILTER_KEYS = [
  "categories",
  "themes",
  "atmospheres",
  "characters",
  "motivations",
  "messages",
  "cinema_types",
  "time_periods",
  "place_contexts",
  "studios",
] as const;

export type ArrayFilterKey = (typeof ARRAY_FILTER_KEYS)[number];
