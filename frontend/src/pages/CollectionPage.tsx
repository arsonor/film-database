import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDownAZ, ArrowLeft, ArrowUpAZ, Eye, Heart, Bookmark,
  List, Plus, Star, Trash2, X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/context/AuthContext";

const TIER_MAX_LISTS: Record<string, number | null> = {
  anonymous: 0,
  free: 3,
  pro: null,
  admin: null,
};
import {
  fetchUserFilms,
  fetchUserLists,
  createUserList,
  deleteUserList,
  fetchListFilms,
  fetchTaxonomy,
} from "@/api/client";
import type { UserList } from "@/api/client";
import { FilmGrid } from "@/components/films/FilmGrid";
import { Pagination } from "@/components/films/Pagination";
import type { TaxonomyItem } from "@/types/api";

type BuiltInTab = "seen" | "favorite" | "watchlist";
type ActiveView = { type: "builtin"; tab: BuiltInTab } | { type: "list"; listId: number };
type CollectionSort = "recent" | "year" | "rating" | "popularity";
type RatingFilter = "any" | "none" | number;

const BUILT_IN_TABS: { key: BuiltInTab; label: string; icon: typeof Eye }[] = [
  { key: "seen", label: "Seen", icon: Eye },
  { key: "favorite", label: "Favorites", icon: Heart },
  { key: "watchlist", label: "Watchlist", icon: Bookmark },
];

const YEAR_MIN = 1900;
const YEAR_MAX = 2030;

function StarLabel({ value }: { value: number }) {
  const full = Math.floor(value / 2);
  const half = value % 2 === 1;
  return (
    <span className="inline-flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`h-3 w-3 ${
            i <= full
              ? "fill-amber-400 text-amber-400"
              : i === full + 1 && half
                ? "fill-amber-400/50 text-amber-400"
                : "fill-none text-muted-foreground/30"
          }`}
        />
      ))}
      <span className="ml-0.5 text-[10px] text-muted-foreground">{value}/10</span>
    </span>
  );
}

export function CollectionPage() {
  const navigate = useNavigate();
  const { isAuthenticated, tier } = useAuth();
  const queryClient = useQueryClient();

  const [activeView, setActiveView] = useState<ActiveView>({ type: "builtin", tab: "seen" });
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<CollectionSort>("recent");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Filters
  const [yearMin, setYearMin] = useState("");
  const [yearMax, setYearMax] = useState("");
  const [language, setLanguage] = useState("");
  const [genre, setGenre] = useState("");
  const [ratingFilter, setRatingFilter] = useState<RatingFilter>("any");

  // Create list
  const [newListName, setNewListName] = useState("");
  const [showNewList, setShowNewList] = useState(false);

  // Taxonomy data
  const [languages, setLanguages] = useState<TaxonomyItem[]>([]);
  const [categories, setCategories] = useState<TaxonomyItem[]>([]);

  useEffect(() => {
    fetchTaxonomy("languages").then((d) => setLanguages(d.items)).catch(() => {});
    fetchTaxonomy("categories").then((d) => setCategories(d.items)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!isAuthenticated) navigate("/auth", { replace: true });
  }, [isAuthenticated, navigate]);

  // User lists
  const { data: userLists = [] } = useQuery({
    queryKey: ["user-lists"],
    queryFn: fetchUserLists,
    enabled: isAuthenticated,
  });

  const resetPage = useCallback(() => setPage(1), []);

  const switchView = useCallback((view: ActiveView) => {
    setActiveView(view);
    setPage(1);
  }, []);

  const handleStatusChanged = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["collection"] });
    queryClient.invalidateQueries({ queryKey: ["list-films"] });
    queryClient.invalidateQueries({ queryKey: ["user-lists"] });
    queryClient.invalidateQueries({ queryKey: ["films"] });
    queryClient.invalidateQueries({ queryKey: ["film"] });
  }, [queryClient]);

  const handleCreateList = useCallback(async () => {
    const name = newListName.trim();
    if (!name) return;
    try {
      await createUserList(name);
      queryClient.invalidateQueries({ queryKey: ["user-lists"] });
      setNewListName("");
      setShowNewList(false);
    } catch { /* ignore */ }
  }, [newListName, queryClient]);

  const handleDeleteList = useCallback(async (listId: number) => {
    if (!window.confirm("Delete this list? Films won't be removed from your collection.")) return;
    await deleteUserList(listId);
    queryClient.invalidateQueries({ queryKey: ["user-lists"] });
    if (activeView.type === "list" && activeView.listId === listId) {
      setActiveView({ type: "builtin", tab: "seen" });
    }
  }, [activeView, queryClient]);

  const parsedYearMin = yearMin ? parseInt(yearMin, 10) : null;
  const parsedYearMax = yearMax ? parseInt(yearMax, 10) : null;
  const effectiveYearMin = parsedYearMin && parsedYearMin > YEAR_MIN ? parsedYearMin : null;
  const effectiveYearMax = parsedYearMax && parsedYearMax < YEAR_MAX ? parsedYearMax : null;

  let ratingMin: number | null = null;
  let ratingMax: number | null = null;
  if (ratingFilter === "none") {
    ratingMin = 0; ratingMax = 0;
  } else if (typeof ratingFilter === "number") {
    ratingMin = ratingFilter; ratingMax = ratingFilter;
  }

  const hasActiveFilters = effectiveYearMin != null || effectiveYearMax != null || language !== "" || genre !== "" || ratingFilter !== "any";

  const clearFilters = useCallback(() => {
    setYearMin(""); setYearMax(""); setLanguage(""); setGenre(""); setRatingFilter("any"); setPage(1);
  }, []);

  // Built-in collection query
  const collectionOpts = useMemo(() => ({
    filter: activeView.type === "builtin" ? activeView.tab : "seen" as const,
    page, sortBy, sortOrder,
    yearMin: effectiveYearMin, yearMax: effectiveYearMax,
    language: language || undefined,
    categories: genre ? [genre] : undefined,
    ratingMin, ratingMax,
  }), [activeView, page, sortBy, sortOrder, effectiveYearMin, effectiveYearMax, language, genre, ratingMin, ratingMax]);

  const collectionQuery = useQuery({
    queryKey: ["collection", collectionOpts],
    queryFn: () => fetchUserFilms(collectionOpts),
    enabled: isAuthenticated && activeView.type === "builtin",
  });

  // Custom list query
  const listQuery = useQuery({
    queryKey: ["list-films", activeView.type === "list" ? activeView.listId : null, page, sortBy, sortOrder],
    queryFn: () => fetchListFilms(
      (activeView as { type: "list"; listId: number }).listId,
      page, sortBy, sortOrder,
    ),
    enabled: isAuthenticated && activeView.type === "list",
  });

  const films = activeView.type === "builtin" ? collectionQuery.data : listQuery.data;
  const isLoading = activeView.type === "builtin" ? collectionQuery.isLoading : listQuery.isLoading;
  const error = activeView.type === "builtin" ? collectionQuery.error : listQuery.error;

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 lg:px-6">
        <Button variant="ghost" size="icon" onClick={() => navigate("/browse")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-lg font-semibold">My Collection</h1>
      </header>

      <main className="mx-auto max-w-7xl p-4 lg:p-6">
        {/* Tabs + Sort */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {BUILT_IN_TABS.map(({ key, label, icon: Icon }) => {
              const isActive = activeView.type === "builtin" && activeView.tab === key;
              const count = isActive ? films?.total ?? 0 : null;
              return (
                <Button
                  key={key}
                  variant={isActive ? "default" : "outline"}
                  size="sm"
                  className="gap-1.5"
                  onClick={() => switchView({ type: "builtin", tab: key })}
                >
                  <Icon className={`h-4 w-4 ${key === "favorite" && isActive ? "fill-current" : ""} ${key === "watchlist" && isActive ? "fill-current" : ""}`} />
                  {label}
                  {count !== null && (
                    <span className="ml-1 rounded-full bg-background/20 px-1.5 text-xs">{count}</span>
                  )}
                </Button>
              );
            })}

            {/* Separator */}
            {userLists.length > 0 && <span className="text-border">|</span>}

            {/* Custom lists */}
            {userLists.map((list) => {
              const isActive = activeView.type === "list" && activeView.listId === list.list_id;
              return (
                <div key={list.list_id} className="group relative flex items-center">
                  <Button
                    variant={isActive ? "default" : "outline"}
                    size="sm"
                    className="gap-1.5 pr-7"
                    onClick={() => switchView({ type: "list", listId: list.list_id })}
                  >
                    <List className="h-4 w-4" />
                    {list.list_name}
                    <span className="rounded-full bg-background/20 px-1.5 text-xs">{list.film_count}</span>
                  </Button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteList(list.list_id); }}
                    className="absolute right-1 flex h-5 w-5 items-center justify-center rounded-full text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                    title="Delete list"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              );
            })}

            {/* New list */}
            {(() => {
              const maxLists = TIER_MAX_LISTS[tier ?? "free"] ?? 0;
              const canCreate = maxLists === null || userLists.length < maxLists;
              if (showNewList) return (
                <div className="flex items-center gap-1">
                  <Input
                    value={newListName}
                    onChange={(e) => setNewListName(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") handleCreateList(); if (e.key === "Escape") setShowNewList(false); }}
                    placeholder="List name"
                    className="h-8 w-32 text-xs"
                    autoFocus
                  />
                  <Button size="sm" variant="ghost" className="h-8 px-2" onClick={handleCreateList}>
                    <Plus className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="ghost" className="h-8 px-2" onClick={() => { setShowNewList(false); setNewListName(""); }}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              );
              if (!canCreate) return (
                <span className="text-xs text-muted-foreground">
                  {maxLists}/{maxLists} lists — upgrade to Pro for more
                </span>
              );
              return (
                <Button variant="ghost" size="sm" className="gap-1 text-muted-foreground" onClick={() => setShowNewList(true)}>
                  <Plus className="h-4 w-4" /> New list
                </Button>
              );
            })()}
          </div>

          <div className="flex items-center gap-2">
            <Select value={sortBy} onValueChange={(val) => { setSortBy(val as CollectionSort); resetPage(); }}>
              <SelectTrigger className="h-9 w-32 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="recent">Recent</SelectItem>
                <SelectItem value="year">Year</SelectItem>
                <SelectItem value="rating">Rating</SelectItem>
                <SelectItem value="popularity">Popularity</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="ghost" size="icon" onClick={() => setSortOrder((o) => o === "asc" ? "desc" : "asc")} title={sortOrder === "asc" ? "Ascending" : "Descending"}>
              {sortOrder === "asc" ? <ArrowUpAZ className="h-4 w-4" /> : <ArrowDownAZ className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Filters (built-in tabs only) */}
        {activeView.type === "builtin" && (
          <div className="mb-5 flex flex-wrap items-end gap-3">
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-muted-foreground">Year</span>
              <Input type="number" min={YEAR_MIN} max={YEAR_MAX} value={yearMin} placeholder="from"
                onChange={(e) => setYearMin(e.target.value)} onBlur={resetPage}
                onKeyDown={(e) => { if (e.key === "Enter") resetPage(); }}
                className="h-7 w-16 text-center text-xs" />
              <span className="text-xs text-muted-foreground">–</span>
              <Input type="number" min={YEAR_MIN} max={YEAR_MAX} value={yearMax} placeholder="to"
                onChange={(e) => setYearMax(e.target.value)} onBlur={resetPage}
                onKeyDown={(e) => { if (e.key === "Enter") resetPage(); }}
                className="h-7 w-16 text-center text-xs" />
            </div>

            <Select value={language || "__all__"} onValueChange={(val) => { setLanguage(val === "__all__" ? "" : val); resetPage(); }}>
              <SelectTrigger className="h-7 w-36 text-xs"><SelectValue placeholder="Language" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Any language</SelectItem>
                {languages.filter((l) => (l.film_count ?? 0) > 0).map((lang) => (
                  <SelectItem key={lang.id} value={lang.name}>{lang.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={genre || "__all__"} onValueChange={(val) => { setGenre(val === "__all__" ? "" : val); resetPage(); }}>
              <SelectTrigger className="h-7 w-36 text-xs"><SelectValue placeholder="Genre" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Any genre</SelectItem>
                {categories.filter((c) => (c.film_count ?? 0) > 0).map((cat) => (
                  <SelectItem key={cat.id} value={cat.name}>{cat.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={ratingFilter === "any" ? "any" : ratingFilter === "none" ? "none" : String(ratingFilter)}
              onValueChange={(val) => {
                if (val === "any") setRatingFilter("any");
                else if (val === "none") setRatingFilter("none");
                else setRatingFilter(parseInt(val, 10));
                resetPage();
              }}
            >
              <SelectTrigger className="h-7 w-40 text-xs"><SelectValue placeholder="Rating" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any rating</SelectItem>
                <SelectItem value="none">Not rated</SelectItem>
                {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map((v) => (
                  <SelectItem key={v} value={String(v)}><StarLabel value={v} /></SelectItem>
                ))}
              </SelectContent>
            </Select>

            {hasActiveFilters && (
              <button onClick={clearFilters} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                <X className="h-3 w-3" /> Clear
              </button>
            )}
          </div>
        )}

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
          <Pagination page={page} totalPages={films.total_pages} onPageChange={setPage} />
        )}
      </main>
    </div>
  );
}
