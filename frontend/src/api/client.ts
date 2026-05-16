import type {
  ChainCheckTagResult,
  ChainGetFilmsResult,
  ChainGetTagsResult,
  ChainRevealTagResult,
  ChainResultData,
  ChainSetupResponse,
  DashboardStats,
  EnrichmentPreview,
  FilmByCountry,
  FilmDetail,
  FilterState,
  GameCheckResult,
  GameHint,
  GamePoolFilters,
  GameRemainingResponse,
  GameResultData,
  GameSetupResponse,
  GameStats,
  GameTag,
  GameType,
  GeographySearchResult,
  GuessEarlyGuessResult,
  GuessRemoveResult,
  GuessRevealTagResult,
  GuessSetupResponse,
  PaginatedFilms,
  PaginatedGameHistory,
  PersonRole,
  PersonSearchResult,
  PersonTagsResponse,
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
  if (filters.production_country)
    params.set("production_country", filters.production_country);
  if (filters.tmdb_collection_id != null)
    params.set("tmdb_collection_id", String(filters.tmdb_collection_id));
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

export interface TagFrequencies {
  total_films: number;
  dimensions: Record<string, Record<string, number>>;
}

export async function fetchTagFrequencies(): Promise<TagFrequencies> {
  return fetchJson<TagFrequencies>(`${BASE}/taxonomy/tag-frequencies`);
}

export type TagDescriptions = Record<string, Record<string, string>>;

export async function fetchTagDescriptions(): Promise<TagDescriptions> {
  return fetchJson<TagDescriptions>(`${BASE}/taxonomy/tag-descriptions`);
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

export async function getDashboardStats(): Promise<DashboardStats> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${BASE}/stats/dashboard`, { headers });
  if (!res.ok) throw new ApiError(res.status, "Failed to load dashboard");
  return res.json();
}

export async function searchPeopleWithFilms(
  role: PersonRole,
  q: string,
): Promise<PersonSearchResult[]> {
  const headers = await getAuthHeaders();
  const params = new URLSearchParams({ role });
  if (q) params.set("q", q);
  const res = await fetch(`${BASE}/stats/people-with-films?${params}`, { headers });
  if (!res.ok) throw new ApiError(res.status, "Failed to search people");
  return res.json();
}

export async function getPersonTags(
  personId: number,
  role: PersonRole,
): Promise<PersonTagsResponse> {
  const headers = await getAuthHeaders();
  const res = await fetch(
    `${BASE}/stats/person-tags?person_id=${personId}&role=${role}`,
    { headers },
  );
  if (!res.ok) throw new ApiError(res.status, "Failed to load person tags");
  return res.json();
}

export async function getFilmsByCountry(
  type: "production" | "set_place",
  iso: string,
  limit = 10,
): Promise<FilmByCountry[]> {
  const headers = await getAuthHeaders();
  const params = new URLSearchParams({ type, iso, limit: String(limit) });
  const url = `${BASE}/stats/films-by-country?${params}`;
  const res = await fetch(url, { headers });
  if (!res.ok) {
    // Surface the backend's detail so we can actually see what failed.
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* not JSON */
    }
    throw new ApiError(res.status, `films-by-country ${res.status}: ${detail}`);
  }
  return res.json();
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

export interface SimilarFilm {
  film_id: number;
  original_title: string;
  first_release_date: string | null;
  duration: number | null;
  poster_url: string | null;
  director: string | null;
  categories: string[];
  score: number;
  score_pct: number;
  shared_tags: Record<string, string[]>;
}

export interface SimilarFilmsResponse {
  items: SimilarFilm[];
}

export async function fetchSimilarFilms(filmId: number, limit = 12): Promise<SimilarFilmsResponse> {
  return fetchJson<SimilarFilmsResponse>(`${BASE}/films/${filmId}/similar?limit=${limit}`);
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

// =============================================================================
// Game mode ("Tag It")
// =============================================================================

export async function fetchDailyChallenge(): Promise<GameSetupResponse> {
  // fetchJson already includes auth headers — backend uses them to detect "already played"
  return fetchJson<GameSetupResponse>(`${BASE}/game/daily`);
}

export async function fetchRandomFilms(
  filters: GamePoolFilters,
): Promise<GameSetupResponse> {
  const sp = new URLSearchParams();
  if (filters.year_min != null) sp.set("year_min", String(filters.year_min));
  if (filters.year_max != null) sp.set("year_max", String(filters.year_max));
  if (filters.language) sp.set("language", filters.language);
  const res = await fetch(`${BASE}/game/random?${sp}`);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export async function checkGameTags(
  filmId: number,
  tags: GameTag[],
  poolFilters?: GamePoolFilters,
): Promise<GameCheckResult> {
  const res = await fetch(`${BASE}/game/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ film_id: filmId, tags, pool_filters: poolFilters ?? null }),
  });
  if (!res.ok) throw new ApiError(res.status, "check failed");
  return res.json();
}

export async function useJokerRemaining(
  tags: GameTag[],
  poolFilters?: GamePoolFilters,
): Promise<GameRemainingResponse> {
  const res = await fetch(`${BASE}/game/joker/remaining`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tags, pool_filters: poolFilters ?? null }),
  });
  if (!res.ok) throw new ApiError(res.status, "remaining failed");
  return res.json();
}

export async function useJokerHint(
  filmId: number,
  tags: GameTag[],
  poolFilters?: GamePoolFilters,
): Promise<GameHint> {
  const res = await fetch(`${BASE}/game/joker/hint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ film_id: filmId, tags, pool_filters: poolFilters ?? null }),
  });
  if (!res.ok) throw new ApiError(res.status, "hint failed");
  return res.json();
}

export async function useJokerSynopsis(filmId: number): Promise<{ synopsis: string | null }> {
  const res = await fetch(`${BASE}/game/joker/synopsis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ film_id: filmId }),
  });
  if (!res.ok) throw new ApiError(res.status, "synopsis failed");
  return res.json();
}

export async function saveGameResult(
  data: GameResultData,
  gameType: GameType = "tag_it",
): Promise<{ saved: boolean; id: number }> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/game/result`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify({ ...data, game_type: gameType }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || "save failed");
  }
  return res.json();
}

export async function fetchGameStats(): Promise<GameStats> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/game/stats`, { headers: auth });
  if (!res.ok) throw new ApiError(res.status, "stats failed");
  return res.json();
}

export async function fetchGameHistory(
  gameType?: GameType,
  page = 1,
  perPage = 20,
): Promise<PaginatedGameHistory> {
  const auth = await getAuthHeaders();
  const sp = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  if (gameType) sp.set("game_type", gameType);
  const res = await fetch(`${BASE}/game/history?${sp}`, { headers: auth });
  if (!res.ok) throw new ApiError(res.status, "history failed");
  return res.json();
}

// -----------------------------------------------------------------------------
// Chain It
// -----------------------------------------------------------------------------

export async function fetchChainDaily(): Promise<ChainSetupResponse> {
  return fetchJson<ChainSetupResponse>(`${BASE}/game/chain/daily`);
}

export async function fetchChainRandom(
  filters: GamePoolFilters,
  difficulty: "easy" | "medium" | "hard" = "medium",
): Promise<ChainSetupResponse> {
  const sp = new URLSearchParams();
  if (filters.year_min != null) sp.set("year_min", String(filters.year_min));
  if (filters.year_max != null) sp.set("year_max", String(filters.year_max));
  if (filters.language) sp.set("language", filters.language);
  sp.set("difficulty", difficulty);
  const res = await fetch(`${BASE}/game/chain/random?${sp}`);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export async function chainCheckTag(
  targetFilmId: number,
  dimension: string,
  value: string,
): Promise<ChainCheckTagResult> {
  const res = await fetch(`${BASE}/game/chain/check-tag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_film_id: targetFilmId, dimension, value }),
  });
  if (!res.ok) throw new ApiError(res.status, "check-tag failed");
  return res.json();
}

export async function chainGetFilms(
  tags: GameTag[],
  excludeFilmIds: number[],
  targetFilmId: number,
  poolFilters?: GamePoolFilters,
  randomize = false,
  difficulty: "easy" | "medium" | "hard" = "medium",
): Promise<ChainGetFilmsResult> {
  const res = await fetch(`${BASE}/game/chain/get-films`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tags,
      exclude_film_ids: excludeFilmIds,
      target_film_id: targetFilmId,
      pool_filters: poolFilters ?? null,
      random: randomize,
      difficulty,
    }),
  });
  if (!res.ok) throw new ApiError(res.status, "get-films failed");
  return res.json();
}

export async function chainGetTags(filmId: number): Promise<ChainGetTagsResult> {
  const res = await fetch(`${BASE}/game/chain/get-tags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ film_id: filmId }),
  });
  if (!res.ok) throw new ApiError(res.status, "get-tags failed");
  return res.json();
}

export async function chainJokerSynopsis(targetFilmId: number): Promise<{ synopsis: string | null }> {
  const res = await fetch(`${BASE}/game/chain/joker/synopsis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_film_id: targetFilmId }),
  });
  if (!res.ok) throw new ApiError(res.status, "synopsis failed");
  return res.json();
}

export async function chainJokerRevealTag(
  targetFilmId: number,
  usedDimensions: string[],
  currentFilmId?: number,
  usedTags?: GameTag[],
): Promise<ChainRevealTagResult> {
  const res = await fetch(`${BASE}/game/chain/joker/reveal-tag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_film_id: targetFilmId,
      current_film_id: currentFilmId,
      used_dimensions: usedDimensions,
      used_tags: usedTags ?? [],
    }),
  });
  if (!res.ok) throw new ApiError(res.status, "reveal-tag failed");
  return res.json();
}

// -----------------------------------------------------------------------------
// Guess It
// -----------------------------------------------------------------------------

export async function fetchGuessDaily(): Promise<GuessSetupResponse> {
  return fetchJson<GuessSetupResponse>(`${BASE}/game/guess/daily`);
}

export async function fetchGuessRandom(
  filters: GamePoolFilters,
  difficulty: "easy" | "medium" | "hard" = "medium",
): Promise<GuessSetupResponse> {
  const sp = new URLSearchParams();
  if (filters.year_min != null) sp.set("year_min", String(filters.year_min));
  if (filters.year_max != null) sp.set("year_max", String(filters.year_max));
  if (filters.language) sp.set("language", filters.language);
  sp.set("difficulty", difficulty);
  const res = await fetch(`${BASE}/game/guess/random?${sp}`);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export async function guessRevealTag(
  targetFilmId: number,
  revealedTags: GameTag[],
  remainingFilmIds: number[],
  difficulty: "easy" | "medium" | "hard" = "medium",
): Promise<GuessRevealTagResult> {
  const res = await fetch(`${BASE}/game/guess/reveal-tag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_film_id: targetFilmId,
      revealed_tags: revealedTags,
      remaining_film_ids: remainingFilmIds,
      difficulty,
    }),
  });
  if (!res.ok) throw new ApiError(res.status, "reveal-tag failed");
  return res.json();
}

export async function guessRemoveFilm(
  targetFilmId: number,
  filmIdToRemove: number,
  revealedTags: GameTag[],
): Promise<GuessRemoveResult> {
  const res = await fetch(`${BASE}/game/guess/remove`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_film_id: targetFilmId,
      film_id_to_remove: filmIdToRemove,
      revealed_tags: revealedTags,
    }),
  });
  if (!res.ok) throw new ApiError(res.status, "remove failed");
  return res.json();
}

export async function guessEarlyGuess(
  targetFilmId: number,
  guessedFilmId: number,
): Promise<GuessEarlyGuessResult> {
  const res = await fetch(`${BASE}/game/guess/early-guess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_film_id: targetFilmId, guessed_film_id: guessedFilmId }),
  });
  if (!res.ok) throw new ApiError(res.status, "early-guess failed");
  return res.json();
}

export async function guessJokerSynopsis(
  remainingFilmIds: number[],
  usedFilmIds: number[] = [],
): Promise<{ film_id: number | null; synopsis: string | null }> {
  const res = await fetch(`${BASE}/game/guess/joker/synopsis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ remaining_film_ids: remainingFilmIds, used_film_ids: usedFilmIds }),
  });
  if (!res.ok) throw new ApiError(res.status, "synopsis failed");
  return res.json();
}

export async function guessJokerDecade(targetFilmId: number): Promise<{ decade: string | null }> {
  const res = await fetch(`${BASE}/game/guess/joker/decade`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_film_id: targetFilmId }),
  });
  if (!res.ok) throw new ApiError(res.status, "decade failed");
  return res.json();
}

export async function saveChainResult(
  data: ChainResultData,
): Promise<{ saved: boolean; id: number }> {
  const auth = await getAuthHeaders();
  const payload: Record<string, unknown> = {
    ...data,
    game_type: "chain_it",
    film_id: data.target_film_id,
    tags_used: data.chain_length,
  };
  const res = await fetch(`${BASE}/game/result`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || "save failed");
  }
  return res.json();
}

// Tag review
export { getAuthHeaders as getAuthHeadersRaw };

export async function fetchPendingReviews(): Promise<{
  pending: { dimension: string; tag: string; file: string }[];
}> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/tag-review/pending`, { headers: auth });
  if (!res.ok) throw new ApiError(res.status, "Failed to fetch pending reviews");
  return res.json();
}

export async function fetchReviewResults(
  dimension: string,
  tag: string,
): Promise<{
  total_reviewed: number;
  currently_tagged: number;
  should_be_tagged: number;
  to_add: { film_id: number; title: string; year: number | null }[];
  to_remove: { film_id: number; title: string; year: number | null }[];
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
}> {
  const auth = await getAuthHeaders();
  const res = await fetch(
    `${BASE}/tag-review/results?dimension=${encodeURIComponent(dimension)}&tag=${encodeURIComponent(tag)}`,
    { headers: auth },
  );
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || `Failed to load results (${res.status})`);
  }
  return res.json();
}

export async function applyTagReview(
  dimension: string,
  tag: string,
): Promise<{ added: number; removed: number }> {
  const auth = await getAuthHeaders();
  const res = await fetch(`${BASE}/tag-review/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify({ dimension, tag }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || "Apply failed");
  }
  return res.json();
}
