import { useCallback, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { ActiveFilters } from "@/components/filters/ActiveFilters";
import { FilmGrid } from "@/components/films/FilmGrid";
import { Pagination } from "@/components/films/Pagination";
import { useAuth } from "@/context/AuthContext";
import { useFilterState } from "@/hooks/useFilterState";
import { useFilms } from "@/hooks/useFilms";
import { useTaxonomy } from "@/hooks/useTaxonomy";

const ANON_LIMIT = 20;

export function BrowsePage() {
  const {
    filters,
    toggleFilter,
    excludeFilter,
    setFilterMode,
    removeFilter,
    clearAllFilters,
    setSearch,
    setSort,
    setPage,
    setSeen,
    updateFilters,
  } = useFilterState();

  const { isAdmin, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const effectiveFilters = useMemo(() => {
    if (isAuthenticated) return filters;
    return {
      ...filters,
      sort_by: "popularity" as const,
      sort_order: "desc" as const,
      per_page: ANON_LIMIT,
      page: 1,
    };
  }, [filters, isAuthenticated]);

  const { films, loading, error } = useFilms(effectiveFilters);
  const { taxonomies } = useTaxonomy();
  const queryClient = useQueryClient();

  const handleStatusChanged = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["films"] });
    queryClient.invalidateQueries({ queryKey: ["collection"] });
    queryClient.invalidateQueries({ queryKey: ["film"] });
  }, [queryClient]);

  const handleShuffle = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["films"] });
  }, [queryClient]);

  const anonExtra = !isAuthenticated && films ? films.total - Math.min(films.total, ANON_LIMIT) : 0;

  return (
    <Layout
      filters={effectiveFilters}
      totalFilms={films?.total ?? null}
      taxonomies={taxonomies}
      onSearchChange={setSearch}
      onSortChange={setSort}
      onShuffle={handleShuffle}
      onToggleFilter={toggleFilter}
      onExcludeFilter={excludeFilter}
      onSetFilterMode={setFilterMode}
      onUpdateFilters={updateFilters}
      isAdmin={isAdmin}
    >
      <ActiveFilters
        filters={filters}
        onRemoveArrayFilter={removeFilter}
        onClearAll={clearAllFilters}
        onUpdateFilters={updateFilters}
      />

      <FilmGrid films={films} loading={loading} error={error} canToggleStatus={isAuthenticated} onStatusChanged={handleStatusChanged} />

      {!isAuthenticated && anonExtra > 0 && (
        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            {anonExtra} more film{anonExtra > 1 ? "s" : ""} match this search —{" "}
            <button
              onClick={() => navigate("/auth")}
              className="font-medium text-primary hover:underline"
            >
              sign up free
            </button>{" "}
            to see all results.
          </p>
        </div>
      )}

      {isAuthenticated && films && films.total_pages > 1 && (
        <Pagination
          page={filters.page}
          totalPages={films.total_pages}
          onPageChange={setPage}
        />
      )}
    </Layout>
  );
}
