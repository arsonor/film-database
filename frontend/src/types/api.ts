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
  production_country: string;
  tmdb_collection_id: number | null;
  tmdb_collection_name: string;
  source: string;
  year_min: number | null;
  year_max: number | null;
  seen: boolean | null;
  sort_by: "year" | "title" | "duration" | "popularity" | "random";
  sort_order: "asc" | "desc";
  page: number;
  per_page: number;
}

export const TAXONOMY_DIMENSIONS = [
  "categories",
  "themes",
  "time_periods",
  "place_contexts",
  "atmospheres",
  "characters",
  "motivations",
  "messages",
  "cinema_types",
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
  production_country: "",
  tmdb_collection_id: null,
  tmdb_collection_name: "",
  source: "",
  year_min: null,
  year_max: null,
  seen: null,
  sort_by: "year",
  sort_order: "desc",
  page: 1,
  per_page: 24,
};

// =============================================================================
// Stats Dashboard
// =============================================================================

export type Tier = "anonymous" | "free" | "pro" | "admin";

export interface QuickStatsPayload {
  total_films: number;
  total_directors: number;
  total_actors: number;
  total_composers: number;
  by_decade: { decade: number; count: number }[];
  duration_distribution: { bucket: string; count: number }[];
  color_by_decade: { decade: number; color: number; bw: number }[];
  top_studios: { name: string; count: number }[];
  top_franchises: {
    collection_id: number;
    name: string;
    count: number;
    poster_path: string | null;
    backdrop_path: string | null;
  }[];
  most_awarded_films: {
    film_id: number;
    title: string;
    poster_url: string | null;
    year: number | null;
    wins: number;
    nominations: number;
  }[];
  by_source_type: { source_type: string; count: number }[];
}

export interface FinancialsPayload {
  top_grossing: {
    film_id: number;
    title: string;
    poster_url: string | null;
    year: number | null;
    revenue: number;
  }[];
  top_budgets: {
    film_id: number;
    title: string;
    poster_url: string | null;
    year: number | null;
    budget: number;
  }[];
  most_profitable: {
    film_id: number;
    title: string;
    poster_url: string | null;
    year: number | null;
    budget: number;
    revenue: number;
    ratio: number;
  }[];
  avg_budget_by_decade: { decade: number; avg_budget: number; film_count: number }[];
  budget_revenue_scatter: {
    film_id: number;
    title: string;
    budget: number;
    revenue: number;
    category: string | null;
  }[];
}

export interface PersonRank {
  person_id: number;
  name: string;
  photo_url: string | null;
  nationality: string | null;
  gender: "M" | "F" | null;
  film_count: number;
  first_year: number | null;
  last_year: number | null;
}
export interface GenderCounts { M: number; F: number; unknown: number }
export interface LivingCounts { living: number; deceased: number; unknown: number }

export type PeopleRoleKey = "directors" | "actors" | "composers";
export type PeopleGenderKey = "all" | "male" | "female";

export interface PeoplePayload {
  top_people: Record<PeopleRoleKey, Record<PeopleGenderKey, PersonRank[]>>;
  top_director_nationalities: { nationality: string; count: number }[];
  top_actor_nationalities: { nationality: string; count: number }[];
  gender_split: { all: GenderCounts; directors: GenderCounts; actors: GenderCounts };
  directors_gender_by_decade: { decade: number; M: number; F: number }[];
  living_status: { directors: LivingCounts; actors: LivingCounts };
  directors_by_birth_decade: { birth_decade: number; count: number }[];
}

export interface TaxonomyPayload {
  top_themes: { name: string; count: number }[];
  category_distribution: { name: string; count: number }[];
  top_atmospheres: { name: string; count: number }[];
  category_by_decade_heatmap: { category: string; decade: number; count: number }[];
}

export interface PersonalStatsPayload {
  seen_count: number;
  unseen_count: number;
  seen_pct: number;
  favorite_count: number;
  watchlist_count: number;
  rated_count: number;
  avg_rating: number | null;
  seen_by_decade: { decade: number; count: number }[];
  top_seen_categories: { name: string; count: number }[];
}

export interface DashboardStats {
  tier: Tier;
  quick: QuickStatsPayload;
  geography: null;
  financials: FinancialsPayload | null;
  people: PeoplePayload | null;
  taxonomy: TaxonomyPayload | null;
  personal_stats: PersonalStatsPayload | null;
}

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
