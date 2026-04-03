import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft,
  Check,
  Film,
  Loader2,
  Plus,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { enrichFilm, saveFilm, searchTMDB } from "@/api/client";
import { PersonCard } from "@/components/films/PersonCard";
import { EditableTagSection } from "@/components/films/EditableTagSection";
import type { EnrichmentPreview, TMDBSearchResult } from "@/types/api";
import {
  formatDuration,
  formatPersonName,
  formatYear,
  tmdbImageUrl,
} from "@/lib/utils";

type WizardStep = "search" | "enriching" | "review";

const ENRICHMENT_MESSAGES = [
  "Fetching from TMDB...",
  "Classifying with AI...",
  "Analyzing themes and atmosphere...",
  "Preparing preview...",
];

export function AddFilmPage() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  useEffect(() => {
    if (!isAdmin) navigate("/browse", { replace: true });
  }, [isAdmin, navigate]);

  const [step, setStep] = useState<WizardStep>("search");

  // Search state
  const [searchTitle, setSearchTitle] = useState("");
  const [searchYear, setSearchYear] = useState("");
  const [searchResults, setSearchResults] = useState<TMDBSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Enrichment state
  const [enrichmentMsg, setEnrichmentMsg] = useState(ENRICHMENT_MESSAGES[0]!);
  const [preview, setPreview] = useState<EnrichmentPreview | null>(null);
  const [enrichError, setEnrichError] = useState<string | null>(null);

  // Save state
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Enrichment message rotation
  const msgIntervalRef = useRef<ReturnType<typeof setInterval>>();

  // ============================================
  // Step 1: Search
  // ============================================
  const handleSearch = useCallback(async () => {
    if (!searchTitle.trim()) return;
    setSearching(true);
    setSearchError(null);
    setSearchResults([]);
    try {
      const year = searchYear ? parseInt(searchYear, 10) : undefined;
      const results = await searchTMDB(searchTitle.trim(), year);
      setSearchResults(results);
      if (results.length === 0) setSearchError("No results found on TMDB.");
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }, [searchTitle, searchYear]);

  const handleSearchKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleSearch();
    },
    [handleSearch],
  );

  // ============================================
  // Step 2: Enrich
  // ============================================
  const handleSelectCandidate = useCallback(
    async (tmdbId: number) => {
      setStep("enriching");
      setEnrichError(null);
      setEnrichmentMsg(ENRICHMENT_MESSAGES[0]!);

      // Rotate messages
      let msgIndex = 0;
      msgIntervalRef.current = setInterval(() => {
        msgIndex = Math.min(msgIndex + 1, ENRICHMENT_MESSAGES.length - 1);
        setEnrichmentMsg(ENRICHMENT_MESSAGES[msgIndex]!);
      }, 3000);

      try {
        const data = await enrichFilm(tmdbId);
        setPreview(data);
        setStep("review");
      } catch (err) {
        setEnrichError(err instanceof Error ? err.message : "Enrichment failed");
        setStep("search");
      } finally {
        clearInterval(msgIntervalRef.current);
      }
    },
    [],
  );

  useEffect(() => {
    return () => clearInterval(msgIntervalRef.current);
  }, []);

  // ============================================
  // Step 3: Save
  // ============================================
  const handleSave = useCallback(async () => {
    if (!preview) return;
    setSaving(true);
    setSaveError(null);
    try {
      const result = await saveFilm(preview);
      navigate(`/films/${result.film_id}`);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }, [preview, navigate]);

  const handleBackToSearch = useCallback(() => {
    setStep("search");
    setPreview(null);
    setEnrichError(null);
    setSaveError(null);
  }, []);

  // ============================================
  // Render
  // ============================================

  if (step === "enriching") {
    return <EnrichingScreen message={enrichmentMsg} />;
  }

  if (step === "review" && preview) {
    return (
      <ReviewScreen
        preview={preview}
        setPreview={setPreview}
        onSave={handleSave}
        onBack={handleBackToSearch}
        saving={saving}
        saveError={saveError}
      />
    );
  }

  // Default: search step
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur sm:px-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex items-center gap-2">
          <Plus className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold">Add Film</h1>
        </div>
      </div>

      <div className="mx-auto max-w-3xl px-4 py-8">
        {/* Search form */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold">Search TMDB</h2>
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchTitle}
                onChange={(e) => setSearchTitle(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Film title..."
                className="pl-9"
                autoFocus
              />
            </div>
            <Input
              value={searchYear}
              onChange={(e) => setSearchYear(e.target.value.replace(/\D/g, "").slice(0, 4))}
              onKeyDown={handleSearchKeyDown}
              placeholder="Year"
              className="w-24"
            />
            <Button onClick={handleSearch} disabled={searching || !searchTitle.trim()}>
              {searching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Search"
              )}
            </Button>
          </div>

          {searchError && (
            <p className="text-sm text-destructive-foreground">{searchError}</p>
          )}
          {enrichError && (
            <p className="text-sm text-destructive-foreground">{enrichError}</p>
          )}
        </div>

        {/* Search results */}
        {searchResults.length > 0 && (
          <div className="mt-6 space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground">
              {searchResults.length} result{searchResults.length !== 1 ? "s" : ""}
            </h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {searchResults.map((r) => (
                <SearchResultCard
                  key={r.tmdb_id}
                  result={r}
                  onSelect={handleSelectCandidate}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Search result card
// =============================================================================

function SearchResultCard({
  result,
  onSelect,
}: {
  result: TMDBSearchResult;
  onSelect: (tmdbId: number) => void;
}) {
  const year = result.release_date ? result.release_date.slice(0, 4) : "—";

  if (result.already_in_db) {
    return (
      <div className="flex gap-3 rounded-lg border border-border bg-card/50 p-3 opacity-60">
        <div className="h-24 w-16 shrink-0 overflow-hidden rounded">
          {result.poster_url ? (
            <img
              src={result.poster_url}
              alt={result.title}
              className="h-full w-full object-cover grayscale"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-muted">
              <Film className="h-5 w-5 text-muted-foreground" />
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">{result.title}</p>
          <p className="text-xs text-muted-foreground">{year}</p>
          <Badge variant="secondary" className="mt-1 text-[10px]">
            Already in database
          </Badge>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={() => onSelect(result.tmdb_id)}
      className="flex gap-3 rounded-lg border border-border bg-card p-3 text-left transition-colors hover:border-primary hover:bg-card/80"
    >
      <div className="h-24 w-16 shrink-0 overflow-hidden rounded">
        {result.poster_url ? (
          <img
            src={result.poster_url}
            alt={result.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-muted">
            <Film className="h-5 w-5 text-muted-foreground" />
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground">{result.title}</p>
        {result.original_title !== result.title && (
          <p className="text-xs text-muted-foreground">{result.original_title}</p>
        )}
        <p className="text-xs text-muted-foreground">{year}</p>
        {result.overview && (
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
            {result.overview}
          </p>
        )}
      </div>
    </button>
  );
}

// =============================================================================
// Enriching loading screen
// =============================================================================

function EnrichingScreen({ message }: { message: string }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background">
      <Sparkles className="h-12 w-12 animate-pulse text-primary" />
      <div className="text-center">
        <h2 className="text-xl font-semibold text-foreground">Enriching Film</h2>
        <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      </div>
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
    </div>
  );
}

// =============================================================================
// Review / Edit screen
// =============================================================================

function ReviewScreen({
  preview,
  setPreview,
  onSave,
  onBack,
  saving,
  saveError,
}: {
  preview: EnrichmentPreview;
  setPreview: (p: EnrichmentPreview) => void;
  onSave: () => void;
  onBack: () => void;
  saving: boolean;
  saveError: string | null;
}) {
  const film = preview.film;
  const enrichment = preview.enrichment as Record<string, unknown>;
  const posterUrl = tmdbImageUrl(film.poster_url as string | null, "w342");
  const year = formatYear(film.first_release_date as string | null);
  const duration = formatDuration(film.duration as number | null);

  // Extract directors from crew
  const directors = (preview.crew || [])
    .filter((c) => c.role === "Director")
    .map((c) => formatPersonName(c.firstname as string | null, c.lastname as string));

  // Taxonomy values from enrichment (Claude) — editable via local state
  const getEnrichmentList = (key: string): string[] => {
    const val = enrichment[key];
    return Array.isArray(val) ? (val as string[]) : [];
  };

  // Local editable state for taxonomy dimensions
  const [categories, setCategories] = useState(preview.categories);
  const [cinemaTypes, setCinemaTypes] = useState(getEnrichmentList("cinema_type"));
  const [themes, setThemes] = useState(getEnrichmentList("themes"));
  const [characters, setCharacters] = useState(getEnrichmentList("character_context"));
  const [motivations, setMotivations] = useState(getEnrichmentList("motivations"));
  const [atmospheres, setAtmospheres] = useState(getEnrichmentList("atmosphere"));
  const [messages, setMessages] = useState(getEnrichmentList("message"));
  const [timePeriods, setTimePeriods] = useState(getEnrichmentList("time_context"));
  const [placeContexts, setPlaceContexts] = useState(getEnrichmentList("place_environment"));
  const [streamingPlatforms, setStreamingPlatforms] = useState(preview.streaming_platforms);

  // Sync editable state back to preview before save
  const handleSave = useCallback(() => {
    const updatedEnrichment = {
      ...enrichment,
      cinema_type: cinemaTypes,
      themes,
      character_context: characters,
      motivations,
      atmosphere: atmospheres,
      message: messages,
      time_context: timePeriods,
      place_environment: placeContexts,
    };

    setPreview({
      ...preview,
      categories,
      enrichment: updatedEnrichment,
      streaming_platforms: streamingPlatforms,
    });

    // Trigger save after state update (next tick)
    setTimeout(onSave, 0);
  }, [
    preview, setPreview, onSave,
    categories, cinemaTypes, themes, characters,
    motivations, atmospheres, messages,
    timePeriods, placeContexts, streamingPlatforms, enrichment,
  ]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur sm:px-6">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="flex-1 text-lg font-semibold">Review & Edit</h1>
        <Button onClick={handleSave} disabled={saving} className="gap-1.5">
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Check className="h-4 w-4" />
          )}
          {saving ? "Saving..." : "Add to Database"}
        </Button>
      </div>

      {saveError && (
        <div className="border-b border-destructive bg-destructive/10 px-4 py-2 text-center text-sm text-destructive-foreground">
          {saveError}
        </div>
      )}

      {preview.enrichment_failed && (
        <div className="border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-center text-sm text-amber-300">
          AI enrichment failed — you can add tags manually below.
        </div>
      )}

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-6 sm:px-6">
        {/* Film header */}
        <div className="flex gap-4">
          {posterUrl ? (
            <img
              src={posterUrl}
              alt={film.original_title as string}
              className="h-48 w-32 shrink-0 rounded-lg object-cover shadow-lg"
            />
          ) : (
            <div className="flex h-48 w-32 shrink-0 items-center justify-center rounded-lg bg-card">
              <Film className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
          <div className="min-w-0 space-y-2">
            <h2 className="text-2xl font-bold text-foreground">
              {film.original_title as string}
            </h2>
            {/* Titles */}
            {preview.titles.length > 0 && (
              <div className="flex flex-wrap gap-x-3 text-sm text-muted-foreground">
                {preview.titles
                  .filter((t) => !t.is_original)
                  .map((t, i) => (
                    <span key={i}>
                      {t.title as string}{" "}
                      <span className="text-xs opacity-60">({t.language_code as string})</span>
                    </span>
                  ))}
              </div>
            )}
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{year}</span>
              <span className="text-border">|</span>
              <span>{duration}</span>
            </div>
            {directors.length > 0 && (
              <p className="text-sm text-muted-foreground">
                Directed by{" "}
                <span className="font-medium text-foreground">
                  {directors.join(", ")}
                </span>
              </p>
            )}
            {preview.keywords.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {preview.keywords.slice(0, 10).map((kw) => (
                  <Badge key={kw} variant="outline" className="text-[10px]">
                    {kw}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        <Separator />

        {/* Cast preview */}
        {preview.cast.length > 0 && (
          <section>
            <h3 className="mb-3 text-lg font-semibold">Cast</h3>
            <div className="flex gap-1 overflow-x-auto pb-2">
              {(preview.cast as Record<string, unknown>[]).map((member, i) => (
                <PersonCard
                  key={`${member.tmdb_id}-${i}`}
                  personId={member.tmdb_id as number}
                  firstname={member.firstname as string | null}
                  lastname={member.lastname as string}
                  role={member.character_name as string || ""}
                  photoUrl={member.photo_url as string | null}
                />
              ))}
            </div>
          </section>
        )}

        <Separator />

        {/* Editable taxonomy sections */}
        <section>
          <h3 className="mb-4 text-xl font-bold">Classification</h3>
          <div className="grid gap-6 sm:grid-cols-2">
            <InlineTagEditor
              label="Categories"
              dimension="categories"
              values={categories}
              onChange={setCategories}
            />
            <InlineTagEditor
              label="Cinema"
              dimension="cinema_types"
              values={cinemaTypes}
              onChange={setCinemaTypes}
            />
          </div>
        </section>

        <section>
          <h3 className="mb-4 text-xl font-bold">Context & Themes</h3>
          <div className="grid gap-6 sm:grid-cols-2">
            <InlineTagEditor
              label="Themes"
              dimension="themes"
              values={themes}
              onChange={setThemes}
            />
            <InlineTagEditor
              label="Characters"
              dimension="characters"
              values={characters}
              onChange={setCharacters}
            />
            <InlineTagEditor
              label="Motivations"
              dimension="motivations"
              values={motivations}
              onChange={setMotivations}
            />
            <InlineTagEditor
              label="Atmospheres"
              dimension="atmospheres"
              values={atmospheres}
              onChange={setAtmospheres}
            />
            <InlineTagEditor
              label="Messages"
              dimension="messages"
              values={messages}
              onChange={setMessages}
            />
          </div>
        </section>

        <Separator />

        <section>
          <h3 className="mb-4 text-xl font-bold">Setting</h3>
          <div className="grid gap-6 sm:grid-cols-2">
            <InlineTagEditor
              label="Time Periods"
              dimension="time_periods"
              values={timePeriods}
              onChange={setTimePeriods}
            />
            <InlineTagEditor
              label="Place Contexts"
              dimension="place_contexts"
              values={placeContexts}
              onChange={setPlaceContexts}
            />
          </div>
        </section>

        <Separator />

        {/* Streaming platforms */}
        <section>
          <h3 className="mb-3 text-lg font-semibold">Streaming Platforms</h3>
          <div className="flex flex-wrap gap-1.5">
            {streamingPlatforms.map((p) => (
              <Badge key={p} variant="secondary" className="gap-1 pr-1 text-xs">
                {p}
                <button
                  onClick={() =>
                    setStreamingPlatforms((prev) => prev.filter((x) => x !== p))
                  }
                  className="ml-0.5 rounded-full p-0.5 hover:bg-destructive/20"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {streamingPlatforms.length === 0 && (
              <span className="text-sm text-muted-foreground">None detected</span>
            )}
          </div>
        </section>

        {/* Awards from enrichment */}
        {Array.isArray(enrichment.awards) && (enrichment.awards as unknown[]).length > 0 && (
          <section>
            <h3 className="mb-3 text-lg font-semibold">Awards (from AI)</h3>
            <div className="space-y-1">
              {(enrichment.awards as Record<string, unknown>[]).map((a, i) => (
                <div key={i} className="text-sm text-muted-foreground">
                  <span className="text-foreground">{a.festival_name as string}</span>
                  {a.year ? <span> ({String(a.year)})</span> : null}
                  {a.category ? <span> — {String(a.category)}</span> : null}
                  <span
                    className={`ml-2 text-xs font-medium ${
                      a.result === "won" ? "text-amber-400" : "text-muted-foreground"
                    }`}
                  >
                    {a.result === "won" ? "Won" : "Nominated"}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Bottom save bar */}
        <div className="sticky bottom-0 flex items-center justify-between border-t border-border bg-background py-4">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Search
          </Button>
          <Button onClick={handleSave} disabled={saving} className="gap-1.5">
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            {saving ? "Saving..." : "Add to Database"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// InlineTagEditor — lightweight tag editor for the review screen
// =============================================================================

import { fetchTaxonomy } from "@/api/client";

function InlineTagEditor({
  label,
  dimension,
  values,
  onChange,
}: {
  label: string;
  dimension: string;
  values: string[];
  onChange: (values: string[]) => void;
}) {
  const [allOptions, setAllOptions] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const loadOptions = useCallback(async () => {
    if (loaded) return;
    try {
      const data = await fetchTaxonomy(dimension);
      setAllOptions(data.items.map((item) => item.name));
      setLoaded(true);
    } catch {
      // Silently fail
    }
  }, [dimension, loaded]);

  const available = allOptions.filter(
    (opt) =>
      !values.includes(opt) &&
      opt.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div>
      <h4 className="mb-2 text-sm font-medium text-muted-foreground">{label}</h4>
      <div className="flex flex-wrap gap-1.5">
        {values.map((val) => (
          <Badge key={val} variant="secondary" className="gap-1 pr-1 text-xs">
            {val}
            <button
              onClick={() => onChange(values.filter((v) => v !== val))}
              className="ml-0.5 rounded-full p-0.5 hover:bg-destructive/20"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
      </div>
      <div className="relative mt-2">
        <Plus className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => {
            loadOptions();
            setShowDropdown(true);
          }}
          onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
          placeholder={`Add ${label.toLowerCase()}...`}
          className="h-8 pl-8 text-xs"
        />
        {showDropdown && available.length > 0 && (
          <div className="absolute top-full z-50 mt-1 max-h-40 w-full overflow-y-auto rounded-md border bg-popover shadow-md">
            {available.map((opt) => (
              <button
                key={opt}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  onChange([...values, opt]);
                  setSearch("");
                  setShowDropdown(false);
                }}
                className="flex w-full items-center px-3 py-1.5 text-xs hover:bg-accent hover:text-accent-foreground"
              >
                {opt}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
