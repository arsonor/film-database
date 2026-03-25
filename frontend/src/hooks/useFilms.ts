import { useCallback, useEffect, useRef, useState } from "react";
import { fetchFilms } from "@/api/client";
import type { FilterState, PaginatedFilms } from "@/types/api";

export function useFilms(filters: FilterState) {
  const [films, setFilms] = useState<PaginatedFilms | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const abortRef = useRef<AbortController>();

  const load = useCallback(async (f: FilterState) => {
    // Cancel previous in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const data = await fetchFilms(f);
      if (!controller.signal.aborted) {
        setFilms(data);
        setLoading(false);
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch films";
        if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
          setError(
            "Cannot connect to the API. Make sure the backend is running on port 8000.",
          );
        } else {
          setError(message);
        }
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    // Debounce text-based filter changes (q, director)
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      load(filters);
    }, 300);

    return () => clearTimeout(debounceRef.current);
  }, [filters, load]);

  return { films, loading, error };
}
