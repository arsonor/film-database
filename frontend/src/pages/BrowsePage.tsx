import { Layout } from "@/components/layout/Layout";
import { ActiveFilters } from "@/components/filters/ActiveFilters";
import { FilmGrid } from "@/components/films/FilmGrid";
import { Pagination } from "@/components/films/Pagination";
import { useAuth } from "@/context/AuthContext";
import { useFilterState } from "@/hooks/useFilterState";
import { useFilms } from "@/hooks/useFilms";
import { useTaxonomy } from "@/hooks/useTaxonomy";

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
  const { films, loading, error } = useFilms(filters);
  const { taxonomies } = useTaxonomy();

  return (
    <Layout
      filters={filters}
      totalFilms={films?.total ?? null}
      taxonomies={taxonomies}
      onSearchChange={setSearch}
      onSortChange={setSort}
      onToggleFilter={toggleFilter}
      onExcludeFilter={excludeFilter}
      onSetFilterMode={setFilterMode}
      onUpdateFilters={updateFilters}
      onSetSeen={setSeen}
      isAdmin={isAdmin}
      isAuthenticated={isAuthenticated}
    >
      <ActiveFilters
        filters={filters}
        onRemoveArrayFilter={removeFilter}
        onClearAll={clearAllFilters}
        onUpdateFilters={updateFilters}
      />

      <FilmGrid films={films} loading={loading} error={error} canToggleSeen={isAuthenticated} />

      {films && films.total_pages > 1 && (
        <Pagination
          page={filters.page}
          totalPages={films.total_pages}
          onPageChange={setPage}
        />
      )}
    </Layout>
  );
}
