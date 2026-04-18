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
  UserFilmStatus,
} from "@/types/api";
import { ARRAY_FILTER_KEYS } from "@/types/api";
import { supabase } from "@/lib/supabase";

const BASE = import.meta.env.VITE_API_URL || "/api";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function fetchJson<T>(url: string): Promise<T> {
  const headers = await getAuthHeaders();
  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new ApiError(res.status, `API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function buildFilmParams(filters: FilterState): string {
  const params = new URLSearchParams();

  // Tag filters: include, exclude, and mode per dimension
  for (const key of ARRAY_FILTER_KEYS) {
    const tf = filters[key];
    for (const v of tf.include) {
      params.append(key, v);
    }
    for (const v of tf.exclude) {
      params.append(`${key}_not`, v);
    }
    if (tf.include.length >= 2 && tf.mode === "and") {
      params.set(`${key}_mode`, "and");
    }
  }

  // String filters
  if (filters.q) params.set("q", filters.q);
  if (filters.location) params.set("location", filters.location);
  if (filters.language) params.set("language", filters.language);
  if (filters.source) params.set("source", filters.source);

  // Number filters
  if (filters.year_min !== null) params.set("year_min", String(filters.year_min));
  if (filters.year_max !== null) params.set("year_max", String(filters.year_max));

  // Boolean filter
  if (filters.seen !== null) params.set("seen", String(filters.seen));

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
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/taxonomy/${dimension}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
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
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/taxonomy/${dimension}/${itemId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...auth },
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
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/taxonomy/${dimension}/merge`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
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
  const auth = await getAuthHeaders();
  const res = await fetch(url, { method: "DELETE", headers: { ...auth } });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail);
  }
}

export interface CollectionFilters {
  filter: "seen" | "favorite" | "watchlist";
  page?: number;
  perPage?: number;
  sortBy?: string;
  sortOrder?: string;
  yearMin?: number | null;
  yearMax?: number | null;
  language?: string;
  categories?: string[];
  ratingMin?: number | null;
  ratingMax?: number | null;
}

export async function fetchUserFilms(opts: CollectionFilters): Promise<PaginatedFilms> {
  const auth = await getAuthHeaders();
  const sp = new URLSearchParams();
  sp.set("filter", opts.filter);
  sp.set("page", String(opts.page ?? 1));
  sp.set("per_page", String(opts.perPage ?? 24));
  sp.set("sort_by", opts.sortBy ?? "recent");
  sp.set("sort_order", opts.sortOrder ?? "desc");
  if (opts.yearMin != null) sp.set("year_min", String(opts.yearMin));
  if (opts.yearMax != null) sp.set("year_max", String(opts.yearMax));
  if (opts.language) sp.set("language", opts.language);
  if (opts.categories?.length) opts.categories.forEach((c) => sp.append("categories", c));
  if (opts.ratingMin != null) sp.set("rating_min", String(opts.ratingMin));
  if (opts.ratingMax != null) sp.set("rating_max", String(opts.ratingMax));
  const res = await fetch(`${BASE}/users/me/films?${sp}`, { headers: auth });
  if (!res.ok) throw new ApiError(res.status, `Failed to fetch collection: ${res.statusText}`);
  return res.json();
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
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/films/${filmId}`, { method: "DELETE", headers: { ...auth } });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || "Delete failed");
  }
}

export async function updateFilm(filmId: number, data: Record<string, unknown>): Promise<void> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/films/${filmId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new ApiError(res.status, `Update failed: ${res.statusText}`);
}

export async function fetchUserFilmStatus(filmId: number): Promise<UserFilmStatus> {
  return fetchJson<UserFilmStatus>(`${BASE}/users/me/films/${filmId}/status`);
}

export async function updateUserFilmStatus(
  filmId: number,
  status: Partial<UserFilmStatus>,
): Promise<void> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/films/${filmId}/status`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify(status),
  });
  if (!res.ok) throw new ApiError(res.status, `Status update failed: ${res.statusText}`);
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
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/add-film/search?${params}`, {
    headers: { ...auth },
  });
  if (!res.ok) throw new ApiError(res.status, `Search failed: ${res.statusText}`);
  const data = await res.json();
  return data.results;
}

export async function enrichFilm(tmdbId: number): Promise<EnrichmentPreview> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/add-film/enrich`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
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
  const auth = await getAuthHeaders();
  await fetch(`${BASE}/films/${filmId}/relations`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify({ related_film_id: relatedFilmId, relation_type: relationType }),
  });
}

export async function deleteFilmRelation(
  filmId: number,
  relatedFilmId: number,
): Promise<void> {
  const auth = await getAuthHeaders();
  await fetch(`${BASE}/films/${filmId}/relations/${relatedFilmId}`, {
    method: "DELETE",
    headers: { ...auth },
  });
}

export async function saveFilm(
  data: EnrichmentPreview,
): Promise<{ film_id: number }> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/films`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || `Save failed: ${res.statusText}`);
  }
  return res.json();
}

// =============================================================================
// Auth
// =============================================================================

// =============================================================================
// User Lists
// =============================================================================

export interface UserList {
  list_id: number;
  list_name: string;
  film_count: number;
}

export async function fetchUserLists(): Promise<UserList[]> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/lists`, { headers: auth });
  if (!res.ok) throw new ApiError(res.status, "Failed to fetch lists");
  return res.json();
}

export async function createUserList(name: string): Promise<UserList> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/lists`, {
    method: "POST",
    headers: { ...auth, "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new ApiError(res.status, "Failed to create list");
  return res.json();
}

export async function deleteUserList(listId: number): Promise<void> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/lists/${listId}`, {
    method: "DELETE",
    headers: auth,
  });
  if (!res.ok) throw new ApiError(res.status, "Failed to delete list");
}

export async function fetchListFilms(
  listId: number,
  page = 1,
  sortBy = "recent",
  sortOrder = "desc",
): Promise<PaginatedFilms> {
  const auth = await getAuthHeaders();
  const sp = new URLSearchParams({
    page: String(page),
    sort_by: sortBy,
    sort_order: sortOrder,
  });
  const res = await fetch(`${BASE}/users/me/lists/${listId}/films?${sp}`, { headers: auth });
  if (!res.ok) throw new ApiError(res.status, "Failed to fetch list films");
  return res.json();
}

export async function addFilmToList(listId: number, filmId: number): Promise<void> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/lists/${listId}/films/${filmId}`, {
    method: "POST",
    headers: auth,
  });
  if (!res.ok) throw new ApiError(res.status, "Failed to add film to list");
}

export async function removeFilmFromList(listId: number, filmId: number): Promise<void> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/lists/${listId}/films/${filmId}`, {
    method: "DELETE",
    headers: auth,
  });
  if (!res.ok) throw new ApiError(res.status, "Failed to remove film from list");
}

export async function fetchFilmListMemberships(filmId: number): Promise<number[]> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/users/me/films/${filmId}/lists`, { headers: auth });
  if (!res.ok) throw new ApiError(res.status, "Failed to fetch film list memberships");
  return res.json();
}

export async function fetchAuthMe(): Promise<{ id: string; email: string; tier: string } | null> {
  try {
    const auth = await getAuthHeaders();
    if (!auth.Authorization) return null;
    const res = await fetch(`${BASE}/auth/me`, { headers: auth });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
