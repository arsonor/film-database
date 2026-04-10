import { useQuery } from "@tanstack/react-query";
import { fetchFilmDetail } from "@/api/client";

export function useFilmDetail(filmId: number) {
  const { data: film = null, isLoading: loading, error, refetch } = useQuery({
    queryKey: ["film", filmId],
    queryFn: () => fetchFilmDetail(filmId),
    staleTime: 60 * 1000,
    refetchOnMount: "always",
  });

  return { film, loading, error: error?.message ?? null, refetch };
}
