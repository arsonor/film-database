import { useCallback, useEffect, useState } from "react";
import { fetchFilmDetail } from "@/api/client";
import type { FilmDetail } from "@/types/api";

export function useFilmDetail(filmId: number) {
  const [film, setFilm] = useState<FilmDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFilmDetail(filmId);
      setFilm(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load film");
    } finally {
      setLoading(false);
    }
  }, [filmId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { film, setFilm, loading, error, refetch: fetch };
}
