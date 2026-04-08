import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import {
  ARRAY_FILTER_KEYS,
  DEFAULT_FILTER_STATE,
  EMPTY_TAG_FILTER,
  type ArrayFilterKey,
  type FilterState,
  type TagFilter,
} from "@/types/api";

function parseSearchParams(sp: URLSearchParams): FilterState {
  const state = structuredClone(DEFAULT_FILTER_STATE);

  // Tag filters
  for (const key of ARRAY_FILTER_KEYS) {
    const include = sp.getAll(key);
    const exclude = sp.getAll(`${key}_not`);
    const mode = sp.get(`${key}_mode`) === "and" ? "and" : "or";
    if (include.length > 0 || exclude.length > 0) {
      state[key] = { include, exclude, mode };
    }
  }

  // String filters
  const q = sp.get("q");
  if (q) state.q = q;
  const location = sp.get("location");
  if (location) state.location = location;
  const language = sp.get("language");
  if (language) state.language = language;
  const source = sp.get("source");
  if (source) state.source = source;

  // Number filters
  const yearMin = sp.get("year_min");
  if (yearMin) state.year_min = parseInt(yearMin, 10);
  const yearMax = sp.get("year_max");
  if (yearMax) state.year_max = parseInt(yearMax, 10);

  // Boolean filter
  const vu = sp.get("vu");
  if (vu === "true") state.vu = true;
  else if (vu === "false") state.vu = false;

  // Sort
  const sortBy = sp.get("sort_by");
  if (sortBy === "year" || sortBy === "title" || sortBy === "duration") {
    state.sort_by = sortBy;
  }
  const sortOrder = sp.get("sort_order");
  if (sortOrder === "asc" || sortOrder === "desc") {
    state.sort_order = sortOrder;
  }

  // Pagination
  const page = sp.get("page");
  if (page) state.page = Math.max(1, parseInt(page, 10));
  const perPage = sp.get("per_page");
  if (perPage) state.per_page = Math.max(1, Math.min(100, parseInt(perPage, 10)));

  return state;
}

function stateToSearchParams(state: FilterState): URLSearchParams {
  const sp = new URLSearchParams();

  for (const key of ARRAY_FILTER_KEYS) {
    const tf = state[key];
    for (const v of tf.include) {
      sp.append(key, v);
    }
    for (const v of tf.exclude) {
      sp.append(`${key}_not`, v);
    }
    if (tf.include.length >= 2 && tf.mode === "and") {
      sp.set(`${key}_mode`, "and");
    }
  }

  if (state.q) sp.set("q", state.q);
  if (state.location) sp.set("location", state.location);
  if (state.language) sp.set("language", state.language);
  if (state.source) sp.set("source", state.source);
  if (state.year_min !== null) sp.set("year_min", String(state.year_min));
  if (state.year_max !== null) sp.set("year_max", String(state.year_max));
  if (state.vu !== null) sp.set("vu", String(state.vu));

  if (state.sort_by !== "year") sp.set("sort_by", state.sort_by);
  if (state.sort_order !== "desc") sp.set("sort_order", state.sort_order);
  if (state.page > 1) sp.set("page", String(state.page));
  if (state.per_page !== 24) sp.set("per_page", String(state.per_page));

  return sp;
}

export function useFilterState() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo(() => parseSearchParams(searchParams), [searchParams]);

  const updateFilters = useCallback(
    (updates: Partial<FilterState>, resetPage = true) => {
      const next = { ...filters, ...updates };
      if (resetPage && !("page" in updates)) {
        next.page = 1;
      }
      setSearchParams(stateToSearchParams(next), { replace: true });
    },
    [filters, setSearchParams],
  );

  const toggleFilter = useCallback(
    (dimension: ArrayFilterKey, value: string) => {
      const tf = filters[dimension];
      const inInclude = tf.include.includes(value);
      const next: TagFilter = inInclude
        ? { ...tf, include: tf.include.filter((v) => v !== value) }
        : { ...tf, include: [...tf.include, value], exclude: tf.exclude.filter((v) => v !== value) };
      updateFilters({ [dimension]: next });
    },
    [filters, updateFilters],
  );

  const excludeFilter = useCallback(
    (dimension: ArrayFilterKey, value: string) => {
      const tf = filters[dimension];
      const inExclude = tf.exclude.includes(value);
      const next: TagFilter = inExclude
        ? { ...tf, exclude: tf.exclude.filter((v) => v !== value) }
        : { ...tf, exclude: [...tf.exclude, value], include: tf.include.filter((v) => v !== value) };
      updateFilters({ [dimension]: next });
    },
    [filters, updateFilters],
  );

  const setFilterMode = useCallback(
    (dimension: ArrayFilterKey, mode: "or" | "and") => {
      const tf = filters[dimension];
      updateFilters({ [dimension]: { ...tf, mode } }, false);
    },
    [filters, updateFilters],
  );

  const removeFilter = useCallback(
    (dimension: ArrayFilterKey, value: string) => {
      const tf = filters[dimension];
      updateFilters({
        [dimension]: {
          ...tf,
          include: tf.include.filter((v) => v !== value),
          exclude: tf.exclude.filter((v) => v !== value),
        },
      });
    },
    [filters, updateFilters],
  );

  const clearAllFilters = useCallback(() => {
    setSearchParams(new URLSearchParams(), { replace: true });
  }, [setSearchParams]);

  const setSearch = useCallback(
    (q: string) => updateFilters({ q }),
    [updateFilters],
  );

  const setSort = useCallback(
    (sort_by: FilterState["sort_by"], sort_order: FilterState["sort_order"]) =>
      updateFilters({ sort_by, sort_order }, false),
    [updateFilters],
  );

  const setPage = useCallback(
    (page: number) => updateFilters({ page }, false),
    [updateFilters],
  );

  const setVu = useCallback(
    (vu: boolean | null) => updateFilters({ vu }),
    [updateFilters],
  );

  return {
    filters,
    updateFilters,
    toggleFilter,
    excludeFilter,
    setFilterMode,
    removeFilter,
    clearAllFilters,
    setSearch,
    setSort,
    setPage,
    setVu,
  };
}
