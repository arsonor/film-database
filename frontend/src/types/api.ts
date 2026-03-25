export interface FilmListItem {
  film_id: number;
  original_title: string;
  first_release_date: string | null;
  duration: number | null;
  poster_url: string | null;
  vu: boolean;
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

export interface FilterState {
  q: string;
  categories: string[];
  themes: string[];
  atmospheres: string[];
  characters: string[];
  character_contexts: string[];
  motivations: string[];
  messages: string[];
  cinema_types: string[];
  cultural_movements: string[];
  time_periods: string[];
  place_contexts: string[];
  studios: string[];
  location: string;
  language: string;
  year_min: number | null;
  year_max: number | null;
  vu: boolean | null;
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
  "character_contexts",
  "motivations",
  "messages",
  "cinema_types",
  "cultural_movements",
  "time_periods",
  "place_contexts",
] as const;

export type TaxonomyDimension = (typeof TAXONOMY_DIMENSIONS)[number];

export const DEFAULT_FILTER_STATE: FilterState = {
  q: "",
  categories: [],
  themes: [],
  atmospheres: [],
  characters: [],
  character_contexts: [],
  motivations: [],
  messages: [],
  cinema_types: [],
  cultural_movements: [],
  time_periods: [],
  place_contexts: [],
  studios: [],
  location: "",
  language: "",
  year_min: null,
  year_max: null,
  vu: null,
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
  "character_contexts",
  "motivations",
  "messages",
  "cinema_types",
  "cultural_movements",
  "time_periods",
  "place_contexts",
  "studios",
] as const;

export type ArrayFilterKey = (typeof ARRAY_FILTER_KEYS)[number];
