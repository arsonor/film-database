import { Layout } from "@/components/layout/Layout";
import { ActiveFilters } from "@/components/filters/ActiveFilters";
import { FilmGrid } from "@/components/films/FilmGrid";
import { Pagination } from "@/components/films/Pagination";
import { useFilterState } from "@/hooks/useFilterState";
import { useFilms } from "@/hooks/useFilms";
import { useTaxonomy } from "@/hooks/useTaxonomy";

export function BrowsePage() {
  const {
    filters,
    toggleFilter,
    removeFilter,
    clearAllFilters,
    setSearch,
    setSort,
    setPage,
    setVu,
    updateFilters,
  } = useFilterState();

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
      onUpdateFilters={updateFilters}
      onSetVu={setVu}
    >
      <ActiveFilters
        filters={filters}
        onRemoveArrayFilter={removeFilter}
        onClearAll={clearAllFilters}
        onUpdateFilters={updateFilters}
      />

      <FilmGrid films={films} loading={loading} error={error} />

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
