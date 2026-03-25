import type {
  FilterState,
  GeographySearchResult,
  PaginatedFilms,
  StatsResponse,
  TaxonomyList,
} from "@/types/api";
import { ARRAY_FILTER_KEYS } from "@/types/api";

const BASE = "/api";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new ApiError(res.status, `API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function buildFilmParams(filters: FilterState): string {
  const params = new URLSearchParams();

  // Array filters: repeat key for each value
  for (const key of ARRAY_FILTER_KEYS) {
    const values = filters[key];
    if (values.length > 0) {
      for (const v of values) {
        params.append(key, v);
      }
    }
  }

  // String filters
  if (filters.q) params.set("q", filters.q);
  if (filters.location) params.set("location", filters.location);
  if (filters.language) params.set("language", filters.language);

  // Number filters
  if (filters.year_min !== null) params.set("year_min", String(filters.year_min));
  if (filters.year_max !== null) params.set("year_max", String(filters.year_max));

  // Boolean filter
  if (filters.vu !== null) params.set("vu", String(filters.vu));

  // Pagination & sorting
  params.set("page", String(filters.page));
  params.set("per_page", String(filters.per_page));
  params.set("sort_by", filters.sort_by);
  params.set("sort_order", filters.sort_order);

  return params.toString();
}

export async function fetchFilms(filters: FilterState): Promise<PaginatedFilms> {
  const qs = buildFilmParams(filters);
  return fetchJson<PaginatedFilms>(`${BASE}/films?${qs}`);
}

export async function fetchTaxonomy(dimension: string): Promise<TaxonomyList> {
  return fetchJson<TaxonomyList>(`${BASE}/taxonomy/${dimension}`);
}

export async function fetchStats(): Promise<StatsResponse> {
  return fetchJson<StatsResponse>(`${BASE}/films/stats`);
}

export async function searchGeography(q: string): Promise<GeographySearchResult[]> {
  if (!q || q.length < 1) return [];
  return fetchJson<GeographySearchResult[]>(
    `${BASE}/geography/search?q=${encodeURIComponent(q)}`,
  );
}
