import type {
  EnrichmentPreview,
  FilmDetail,
  FilterState,
  GeographySearchResult,
  PaginatedFilms,
  StatsResponse,
  TMDBSearchResult,
  TaxonomyItem,
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

export async function addTaxonomyValue(
  dimension: string,
  name: string,
  sortOrder?: number,
): Promise<TaxonomyItem> {
  const res = await fetch(`${BASE}/taxonomy/${dimension}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, sort_order: sortOrder }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export async function renameTaxonomyValue(
  dimension: string,
  itemId: number,
  name: string,
  sortOrder?: number,
): Promise<TaxonomyItem> {
  const res = await fetch(`${BASE}/taxonomy/${dimension}/${itemId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, sort_order: sortOrder }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export async function mergeTaxonomyValues(
  dimension: string,
  sourceId: number,
  targetId: number,
): Promise<{ merged: boolean; films_affected: number }> {
  const res = await fetch(`${BASE}/taxonomy/${dimension}/merge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id: sourceId, target_id: targetId }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export async function deleteTaxonomyValue(
  dimension: string,
  itemId: number,
  force = false,
): Promise<void> {
  const url = `${BASE}/taxonomy/${dimension}/${itemId}${force ? "?force=true" : ""}`;
  const res = await fetch(url, { method: "DELETE" });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail);
  }
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

export async function fetchFilmDetail(filmId: number): Promise<FilmDetail> {
  return fetchJson<FilmDetail>(`${BASE}/films/${filmId}`);
}

export async function deleteFilm(filmId: number): Promise<void> {
  const res = await fetch(`${BASE}/films/${filmId}`, { method: "DELETE" });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || "Delete failed");
  }
}

export async function updateFilm(filmId: number, data: Record<string, unknown>): Promise<void> {
  const res = await fetch(`${BASE}/films/${filmId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, `Update failed: ${res.statusText}`);
}

export async function toggleVu(filmId: number, vu: boolean): Promise<void> {
  const res = await fetch(`${BASE}/films/${filmId}/vu?vu=${vu}`, {
    method: "PATCH",
  });
  if (!res.ok) throw new ApiError(res.status, `Toggle failed: ${res.statusText}`);
}

// =============================================================================
// Add Film workflow
// =============================================================================

export async function searchTMDB(
  title: string,
  year?: number,
): Promise<TMDBSearchResult[]> {
  const params = new URLSearchParams({ title });
  if (year) params.set("year", String(year));
  const data = await fetchJson<{ results: TMDBSearchResult[] }>(
    `${BASE}/add-film/search?${params}`,
  );
  return data.results;
}

export async function enrichFilm(tmdbId: number): Promise<EnrichmentPreview> {
  const res = await fetch(`${BASE}/add-film/enrich`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tmdb_id: tmdbId }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || `Enrich failed: ${res.statusText}`);
  }
  return res.json();
}

export async function searchLocalFilms(
  q: string,
): Promise<{ film_id: number; original_title: string; year: number | null }[]> {
  const res = await fetch(`${BASE}/films/search-local?q=${encodeURIComponent(q)}`);
  if (!res.ok) return [];
  return res.json();
}

export async function addFilmRelation(
  filmId: number,
  relatedFilmId: number,
  relationType: string,
): Promise<void> {
  await fetch(`${BASE}/films/${filmId}/relations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ related_film_id: relatedFilmId, relation_type: relationType }),
  });
}

export async function deleteFilmRelation(
  filmId: number,
  relatedFilmId: number,
): Promise<void> {
  await fetch(`${BASE}/films/${filmId}/relations/${relatedFilmId}`, {
    method: "DELETE",
  });
}

export async function saveFilm(
  data: EnrichmentPreview,
): Promise<{ film_id: number }> {
  const res = await fetch(`${BASE}/films`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || `Save failed: ${res.statusText}`);
  }
  return res.json();
}
