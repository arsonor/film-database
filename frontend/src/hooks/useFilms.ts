import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchFilms } from "@/api/client";
import type { FilterState } from "@/types/api";

export function useFilms(filters: FilterState) {
  const [debouncedFilters, setDebouncedFilters] = useState(filters);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedFilters(filters), 300);
    return () => clearTimeout(timer);
  }, [filters]);

  const { data: films = null, isLoading: loading, error } = useQuery({
    queryKey: ["films", debouncedFilters],
    queryFn: () => fetchFilms(debouncedFilters),
  });

  return { films, loading, error: error?.message ?? null };
}
