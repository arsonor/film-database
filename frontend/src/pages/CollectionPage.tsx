import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Eye, Heart, Bookmark } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { fetchUserFilms } from "@/api/client";
import { FilmGrid } from "@/components/films/FilmGrid";
import { Pagination } from "@/components/films/Pagination";

type CollectionFilter = "seen" | "favorite" | "watchlist";

const TABS: { key: CollectionFilter; label: string; icon: typeof Eye }[] = [
  { key: "seen", label: "Seen", icon: Eye },
  { key: "favorite", label: "Favorites", icon: Heart },
  { key: "watchlist", label: "Watchlist", icon: Bookmark },
];

export function CollectionPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<CollectionFilter>("seen");
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!isAuthenticated) navigate("/auth", { replace: true });
  }, [isAuthenticated, navigate]);

  const queryClient = useQueryClient();

  const handleTabChange = useCallback((tab: CollectionFilter) => {
    setActiveTab(tab);
    setPage(1);
  }, []);

  const handleStatusChanged = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["collection"] });
    queryClient.invalidateQueries({ queryKey: ["films"] });
    queryClient.invalidateQueries({ queryKey: ["film"] });
  }, [queryClient]);

  const { data: films, isLoading, error } = useQuery({
    queryKey: ["collection", activeTab, page],
    queryFn: () => fetchUserFilms(activeTab, page, 24),
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 lg:px-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/browse")}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-lg font-semibold">My Collection</h1>
      </header>

      <main className="mx-auto max-w-7xl p-4 lg:p-6">
        {/* Tabs */}
        <div className="mb-6 flex gap-2">
          {TABS.map(({ key, label, icon: Icon }) => {
            const count = key === activeTab ? films?.total ?? 0 : null;
            return (
              <Button
                key={key}
                variant={activeTab === key ? "default" : "outline"}
                size="sm"
                className="gap-1.5"
                onClick={() => handleTabChange(key)}
              >
                <Icon className={`h-4 w-4 ${key === "favorite" && activeTab === key ? "fill-current" : ""} ${key === "watchlist" && activeTab === key ? "fill-current" : ""}`} />
                {label}
                {count !== null && (
                  <span className="ml-1 rounded-full bg-background/20 px-1.5 text-xs">
                    {count}
                  </span>
                )}
              </Button>
            );
          })}
        </div>

        {/* Grid */}
        <FilmGrid
          films={films ?? null}
          loading={isLoading}
          error={error ? (error as Error).message : null}
          canToggleStatus
          onStatusChanged={handleStatusChanged}
        />

        {/* Pagination */}
        {films && films.total_pages > 1 && (
          <Pagination
            page={page}
            totalPages={films.total_pages}
            onPageChange={setPage}
          />
        )}
      </main>
    </div>
  );
}
