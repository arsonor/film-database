import { useQuery } from "@tanstack/react-query";
import { fetchSimilarFilms } from "@/api/client";
import { useAuth } from "@/context/AuthContext";

const TIER_LIMITS: Record<string, number> = {
  anonymous: 3,
  free: 6,
  pro: 12,
  admin: 12,
};

export function useSimilarFilms(filmId: number) {
  const { tier, isAuthenticated } = useAuth();
  const effectiveTier = isAuthenticated ? (tier ?? "free") : "anonymous";
  const limit = TIER_LIMITS[effectiveTier] ?? 3;

  return useQuery({
    queryKey: ["similar-films", filmId, limit],
    queryFn: () => fetchSimilarFilms(filmId, limit),
    enabled: filmId > 0,
    staleTime: 5 * 60 * 1000,
  });
}
