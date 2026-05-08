import { useQuery } from "@tanstack/react-query";
import { getDashboardStats } from "@/api/client";
import { useAuth } from "@/context/AuthContext";

export function useDashboardStats() {
  const { tier, isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["dashboard-stats", tier ?? "anonymous", isAuthenticated],
    queryFn: getDashboardStats,
    staleTime: 5 * 60 * 1000,
  });
}
