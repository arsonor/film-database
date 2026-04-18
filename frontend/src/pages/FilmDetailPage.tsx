import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft,
  ArrowUp,
  Film,
  Trash2,
  Tv,
  Clock,
  Palette,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useFilmDetail } from "@/hooks/useFilmDetail";
import { deleteFilm, updateUserFilmStatus } from "@/api/client";
import { FilmStatusBar } from "@/components/films/FilmStatusBar";
import { PersonCard } from "@/components/films/PersonCard";
import { ExternalLinks } from "@/components/films/ExternalLinks";
import { AwardsTable } from "@/components/films/AwardsTable";
import { EditableFinancials } from "@/components/films/EditableFinancials";
import { EditableTagSection } from "@/components/films/EditableTagSection";
import { EditableGeographySection } from "@/components/films/EditableGeographySection";
import { EditableSourceSection } from "@/components/films/EditableSourceSection";
import { RelatedFilmsSection } from "@/components/films/RelatedFilmsSection";
import { SimilarFilmsCarousel } from "@/components/films/SimilarFilmsCarousel";
import { SectionHeading } from "@/components/films/SectionHeading";
import type { CrewMember } from "@/types/api";
import {
  dimensionLabel,
  formatYear,
  formatDuration,
  formatCurrency,
  formatPersonName,
  tmdbImageUrl,
} from "@/lib/utils";

export function FilmDetailPage() {
  const { id } = useParams<{ id: string }>();
  const filmId = Number(id);
  const navigate = useNavigate();
  const { isAdmin, isAuthenticated, tier } = useAuth();
  const queryClient = useQueryClient();
  const { film, loading, error, refetch } = useFilmDetail(filmId);

  const handleStatusChange = useCallback(async (updated: Record<string, unknown>) => {
    if (!film) return;
    const defaultStatus = { seen: false, favorite: false, watchlist: false, rating: null, notes: "" };
    const prev = film.user_status ?? defaultStatus;
    // Optimistic update
    queryClient.setQueryData(["film", filmId], {
      ...film,
      user_status: { ...prev, ...updated },
    });
    try {
      await updateUserFilmStatus(film.film_id, updated);
      queryClient.invalidateQueries({ queryKey: ["films"] });
      queryClient.invalidateQueries({ queryKey: ["collection"] });
    } catch {
      queryClient.setQueryData(["film", filmId], film);
    }
  }, [film, filmId, queryClient]);

  const handleDelete = useCallback(async () => {
    if (!film) return;
    if (!window.confirm(`Delete "${film.original_title}" and all its data? This cannot be undone.`)) return;
    try {
      await deleteFilm(film.film_id);
      queryClient.invalidateQueries({ queryKey: ["films"] });
      navigate("/browse");
    } catch {
      // stay on page
    }
  }, [film, navigate, queryClient]);

  const handleSaved = useCallback(() => {
    refetch();
    queryClient.invalidateQueries({ queryKey: ["films"] });
  }, [refetch, queryClient]);

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error || !film) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-8">
        <p className="text-lg text-destructive-foreground">{error || "Film not found"}</p>
        <Button asChild variant="outline">
          <Link to="/browse">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Browse
          </Link>
        </Button>
      </div>
    );
  }

  const backdropUrl = tmdbImageUrl(film.backdrop_url, "w1280");
  const posterUrl = tmdbImageUrl(film.poster_url, "w500");
  const directors = film.crew.filter((c) => c.role === "Director");
  const writers = film.crew.filter((c) => c.role === "Writer");
  const cinematographers = film.crew.filter((c) => c.role === "Cinematographer");
  const composers = film.crew.filter((c) => c.role === "Composer");
  const otherCrew = film.crew.filter(
    (c) => !["Director", "Writer", "Cinematographer", "Composer"].includes(c.role),
  );

  const year = formatYear(film.first_release_date);

  // Group crew by role for display
  const crewGroups: { role: string; members: CrewMember[] }[] = [];
  for (const [role, members] of [
    ["Director", directors],
    ["Writer", writers],
    ["Cinematographer", cinematographers],
    ["Composer", composers],
  ] as [string, CrewMember[]][]) {
    if (members.length > 0) crewGroups.push({ role, members });
  }
  // Group remaining crew
  const otherRoles = new Map<string, CrewMember[]>();
  for (const c of otherCrew) {
    const arr = otherRoles.get(c.role) || [];
    arr.push(c);
    otherRoles.set(c.role, arr);
  }
  for (const [role, members] of otherRoles) {
    crewGroups.push({ role, members });
  }

  // Non-original titles
  const localizedTitles = film.titles.filter((t) => !t.is_original);

  return (
    <div className="min-h-screen bg-background">
      {/* ================================================================ */}
      {/* Hero Section */}
      {/* ================================================================ */}
      {/* ================================================================ */}
      {/* Backdrop + Back button */}
      {/* ================================================================ */}
      <div className="relative">
        {backdropUrl ? (
          <div className="relative h-[200px] w-full overflow-hidden sm:h-[420px] lg:h-[480px]">
            <img
              src={backdropUrl}
              alt=""
              className="h-full w-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-background/40 to-transparent" />
          </div>
        ) : (
          <div className="h-[120px] w-full bg-card sm:h-[300px]" />
        )}

        {/* Back button — always visible */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute left-4 top-4 z-10 bg-background/50 backdrop-blur sm:left-6"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>

        {/* Desktop hero overlay (sm+) */}
        <div className="absolute inset-x-0 bottom-0 hidden px-6 pb-6 sm:block lg:px-8">
          <div className="mx-auto flex max-w-6xl gap-6">
            {/* Poster */}
            <div className="shrink-0">
              {posterUrl ? (
                <img
                  src={posterUrl}
                  alt={film.original_title}
                  className="w-48 rounded-lg shadow-2xl lg:w-64"
                />
              ) : (
                <div className="flex h-72 w-48 items-center justify-center rounded-lg bg-card shadow-2xl lg:h-96 lg:w-64">
                  <Film className="h-12 w-12 text-muted-foreground" />
                </div>
              )}
            </div>

            {/* Info block — desktop */}
            <div className="flex min-w-0 flex-1 flex-col justify-end gap-3">
              <h1 className="text-3xl font-bold leading-tight text-foreground lg:text-4xl">
                {film.original_title}
              </h1>
              {localizedTitles.length > 0 && (
                <div className="flex flex-wrap gap-x-3 gap-y-1">
                  {localizedTitles.map((t) => (
                    <span key={t.language_code} className="text-sm text-muted-foreground">
                      {t.title}
                      <span className="ml-1 text-xs opacity-60">({t.language_name})</span>
                    </span>
                  ))}
                </div>
              )}
              <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                <span className="font-medium text-foreground">{year}</span>
                {film.duration && (
                  <>
                    <span className="text-border">|</span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      {formatDuration(film.duration)}
                    </span>
                  </>
                )}
                {!film.color && (
                  <>
                    <span className="text-border">|</span>
                    <span className="flex items-center gap-1">
                      <Palette className="h-3.5 w-3.5" />
                      B&W
                    </span>
                  </>
                )}
              </div>
              {film.categories.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {film.categories.map((cat) => (
                    <Badge key={cat} className="text-xs">{cat}</Badge>
                  ))}
                </div>
              )}
              {directors.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  Directed by{" "}
                  {directors.map((d, i) => (
                    <span key={d.person_id}>
                      {i > 0 && ", "}
                      <button
                        onClick={() => navigate(`/browse?q=${encodeURIComponent(formatPersonName(d.firstname, d.lastname))}`)}
                        className="font-medium text-foreground hover:text-primary"
                      >
                        {formatPersonName(d.firstname, d.lastname)}
                      </button>
                    </span>
                  ))}
                </p>
              )}
              <div className="space-y-1 text-sm text-muted-foreground">
                <EditableSourceSection filmId={film.film_id} sources={film.sources} onSaved={handleSaved} readOnly={!isAdmin} />
                <div className="flex items-center gap-2">
                  {film.budget != null && film.budget > 0 && <span>Budget: {formatCurrency(film.budget)}</span>}
                  {film.budget != null && film.budget > 0 && film.revenue != null && film.revenue > 0 && <span className="text-border">|</span>}
                  {film.revenue != null && film.revenue > 0 && <span>Revenue: {formatCurrency(film.revenue)}</span>}
                  {isAdmin && <EditableFinancials filmId={film.film_id} budget={film.budget} revenue={film.revenue} onSaved={handleSaved} />}
                </div>
                <EditableTagSection filmId={film.film_id} dimension="studios" currentValues={film.studios} onSaved={handleSaved} readOnly={!isAdmin} allowCustom hideTitle />
                {film.streaming_platforms.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2">
                    {film.streaming_platforms.map((platform) => (
                      <Badge key={platform} variant="secondary" className="gap-1.5 text-xs">
                        <Tv className="h-3 w-3" />
                        {platform}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-3">
                {isAuthenticated && (
                  <FilmStatusBar filmId={film.film_id} status={film.user_status} onStatusChange={handleStatusChange} />
                )}
                <ExternalLinks tmdbId={film.tmdb_id} imdbId={film.imdb_id} title={film.original_title} year={film.first_release_date} />
                {isAdmin && (
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={handleDelete} title="Delete film">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ================================================================ */}
      {/* Mobile hero content (below backdrop, normal flow) */}
      {/* ================================================================ */}
      <div className="sm:hidden">
        {/* Mobile poster — pulled up over backdrop */}
        {posterUrl && (
          <div className="px-4">
            <img
              src={posterUrl}
              alt={film.original_title}
              className="-mt-20 relative z-10 mx-auto w-36 rounded-lg shadow-2xl"
            />
          </div>
        )}

        {/* Mobile info — normal document flow */}
        <div className="space-y-3 px-4 pt-4 pb-2">
          <h1 className="text-xl font-bold leading-tight text-foreground text-center">
            {film.original_title}
          </h1>
          {localizedTitles.length > 0 && (
            <div className="flex flex-wrap justify-center gap-x-3 gap-y-1">
              {localizedTitles.map((t) => (
                <span key={t.language_code} className="text-xs text-muted-foreground">
                  {t.title}
                  <span className="ml-1 opacity-60">({t.language_name})</span>
                </span>
              ))}
            </div>
          )}
          <div className="flex flex-wrap items-center justify-center gap-2 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{year}</span>
            {film.duration && (
              <>
                <span className="text-border">|</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {formatDuration(film.duration)}
                </span>
              </>
            )}
            {!film.color && (
              <>
                <span className="text-border">|</span>
                <span className="flex items-center gap-1">
                  <Palette className="h-3.5 w-3.5" />
                  B&W
                </span>
              </>
            )}
          </div>
          {film.categories.length > 0 && (
            <div className="flex flex-wrap justify-center gap-1.5">
              {film.categories.map((cat) => (
                <Badge key={cat} className="text-xs">{cat}</Badge>
              ))}
            </div>
          )}
          {directors.length > 0 && (
            <p className="text-center text-sm text-muted-foreground">
              Directed by{" "}
              {directors.map((d, i) => (
                <span key={d.person_id}>
                  {i > 0 && ", "}
                  <button
                    onClick={() => navigate(`/browse?q=${encodeURIComponent(formatPersonName(d.firstname, d.lastname))}`)}
                    className="font-medium text-foreground hover:text-primary"
                  >
                    {formatPersonName(d.firstname, d.lastname)}
                  </button>
                </span>
              ))}
            </p>
          )}
          <div className="space-y-1 text-sm text-muted-foreground">
            <EditableSourceSection filmId={film.film_id} sources={film.sources} onSaved={handleSaved} readOnly={!isAdmin} />
            <div className="flex items-center gap-2">
              {film.budget != null && film.budget > 0 && <span>Budget: {formatCurrency(film.budget)}</span>}
              {film.budget != null && film.budget > 0 && film.revenue != null && film.revenue > 0 && <span className="text-border">|</span>}
              {film.revenue != null && film.revenue > 0 && <span>Revenue: {formatCurrency(film.revenue)}</span>}
              {isAdmin && <EditableFinancials filmId={film.film_id} budget={film.budget} revenue={film.revenue} onSaved={handleSaved} />}
            </div>
            <EditableTagSection filmId={film.film_id} dimension="studios" currentValues={film.studios} onSaved={handleSaved} readOnly={!isAdmin} allowCustom hideTitle />
            {film.streaming_platforms.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                {film.streaming_platforms.map((platform) => (
                  <Badge key={platform} variant="secondary" className="gap-1.5 text-xs">
                    <Tv className="h-3 w-3" />
                    {platform}
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-col gap-3">
            {isAuthenticated && (
              <FilmStatusBar filmId={film.film_id} status={film.user_status} onStatusChange={handleStatusChange} />
            )}
            <ExternalLinks tmdbId={film.tmdb_id} imdbId={film.imdb_id} title={film.original_title} year={film.first_release_date} />
            {isAdmin && (
              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={handleDelete} title="Delete film">
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* ================================================================ */}
      {/* Content Sections */}
      {/* ================================================================ */}
      <div className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
        {/* Section navigation — uses scrollIntoView to avoid polluting browser history */}
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-border pb-4 text-sm font-medium">
          {film.summary && (
            <button onClick={() => document.getElementById("synopsis")?.scrollIntoView({ behavior: "smooth" })} className="text-muted-foreground transition-colors hover:text-primary">Synopsis</button>
          )}
          <button onClick={() => document.getElementById("related-films")?.scrollIntoView({ behavior: "smooth" })} className="text-muted-foreground transition-colors hover:text-primary">Related Films</button>
          <button onClick={() => document.getElementById("similar-films")?.scrollIntoView({ behavior: "smooth" })} className="text-muted-foreground transition-colors hover:text-primary">Similar Films</button>
          <button onClick={() => document.getElementById("taxonomy")?.scrollIntoView({ behavior: "smooth" })} className="text-muted-foreground transition-colors hover:text-primary">Taxonomy</button>
          {(film.cast.length > 0 || crewGroups.length > 0) && (
            <button onClick={() => document.getElementById("cast-crew")?.scrollIntoView({ behavior: "smooth" })} className="text-muted-foreground transition-colors hover:text-primary">Cast & Crew</button>
          )}
          <button onClick={() => document.getElementById("awards")?.scrollIntoView({ behavior: "smooth" })} className="text-muted-foreground transition-colors hover:text-primary">Awards</button>
        </nav>

        {/* Synopsis */}
        {film.summary && (
          <section id="synopsis" className="scroll-mt-20">
            <SectionHeading title="Synopsis" />
            <p className="leading-relaxed text-muted-foreground">{film.summary}</p>
          </section>
        )}

        {/* Related Films */}
        <div id="related-films" className="scroll-mt-20">
          <RelatedFilmsSection
            filmId={film.film_id}
            sequels={film.sequels}
            onSaved={handleSaved}
            readOnly={!isAdmin}
          />
        </div>

        {/* Similar Films */}
        <section id="similar-films" className="scroll-mt-20">
          <SimilarFilmsCarousel filmId={film.film_id} locked={tier !== "pro" && tier !== "admin"} />
        </section>

        <Separator />

        {/* Taxonomy */}
        <section id="taxonomy" className="scroll-mt-20">
          <SectionHeading title="Taxonomy" />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <EditableTagSection
              filmId={film.film_id}
              dimension="time_periods"
              currentValues={film.time_periods}
              onSaved={handleSaved}
              readOnly={!isAdmin}
            />
            <EditableTagSection
              filmId={film.film_id}
              dimension="place_contexts"
              currentValues={film.place_contexts}
              onSaved={handleSaved}
              readOnly={!isAdmin}
            />
            <EditableGeographySection
              filmId={film.film_id}
              setPlaces={film.set_places}
              onSaved={handleSaved}
              readOnly={!isAdmin}
            />
          </div>
          <div className="mt-6 space-y-4">
            <div>
              <EditableTagSection
                filmId={film.film_id}
                dimension="categories"
                currentValues={film.categories}
                onSaved={handleSaved}
                readOnly={!isAdmin}
              />
            </div>
            {isAuthenticated ? (
              <>
                <div className="grid gap-6 sm:grid-cols-2">
                  <EditableTagSection
                    filmId={film.film_id}
                    dimension="themes"
                    currentValues={film.themes}
                    onSaved={handleSaved}
                    readOnly={!isAdmin}
                  />
                  <EditableTagSection
                    filmId={film.film_id}
                    dimension="atmospheres"
                    currentValues={film.atmospheres}
                    onSaved={handleSaved}
                    readOnly={!isAdmin}
                  />
                </div>
                <div className="grid gap-6 sm:grid-cols-2">
                  <EditableTagSection
                    filmId={film.film_id}
                    dimension="characters"
                    currentValues={film.characters}
                    onSaved={handleSaved}
                    readOnly={!isAdmin}
                  />
                  <EditableTagSection
                    filmId={film.film_id}
                    dimension="motivations"
                    currentValues={film.motivations}
                    onSaved={handleSaved}
                    readOnly={!isAdmin}
                  />
                </div>
                <div className="grid gap-6 sm:grid-cols-2">
                  <EditableTagSection
                    filmId={film.film_id}
                    dimension="messages"
                    currentValues={film.messages}
                    onSaved={handleSaved}
                    readOnly={!isAdmin}
                  />
                  <EditableTagSection
                    filmId={film.film_id}
                    dimension="cinema_types"
                    currentValues={film.cinema_types}
                    onSaved={handleSaved}
                    readOnly={!isAdmin}
                  />
                </div>
              </>
            ) : (
              <div className="space-y-3 pt-2">
                <p className="text-sm text-muted-foreground">
                  6 more dimensions available —{" "}
                  <button
                    onClick={() => navigate("/auth")}
                    className="font-medium text-primary hover:underline"
                  >
                    sign up free
                  </button>{" "}
                  to unveil all tags.
                </p>
                <div className="flex flex-wrap gap-3">
                  {([
                    ["themes", film.themes],
                    ["atmospheres", film.atmospheres],
                    ["characters", film.characters],
                    ["motivations", film.motivations],
                    ["messages", film.messages],
                    ["cinema_types", film.cinema_types],
                  ] as [string, string[]][]).map(([dim, values]) => (
                    <span
                      key={dim}
                      className="inline-flex items-center gap-1.5 rounded-md border border-border/50 px-2.5 py-1 text-xs text-muted-foreground"
                    >
                      {dimensionLabel(dim)}
                      <span className="font-semibold text-foreground">{values.length}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>

        <Separator />

        {/* Cast & Crew */}
        {(film.cast.length > 0 || crewGroups.length > 0) && (
          <section id="cast-crew" className="scroll-mt-20 space-y-8">
            {film.cast.length > 0 && (
              <div>
                <SectionHeading title="Cast" />
                <div className="flex gap-1 overflow-x-auto pb-2">
                  {film.cast.map((member) => (
                    <PersonCard
                      key={`${member.person_id}-${member.character_name}`}
                      personId={member.person_id}
                      firstname={member.firstname}
                      lastname={member.lastname}
                      role={member.character_name || ""}
                      photoUrl={member.photo_url}
                    />
                  ))}
                </div>
              </div>
            )}
            {crewGroups.length > 0 && (
              <div>
                <SectionHeading title="Crew" />
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {crewGroups.map((group) => (
                    <div key={group.role}>
                      <h3 className="mb-2 text-sm font-medium text-muted-foreground">
                        {group.role}
                      </h3>
                      <div className="flex flex-wrap gap-1">
                        {group.members.map((m) => (
                          <PersonCard
                            key={m.person_id}
                            personId={m.person_id}
                            firstname={m.firstname}
                            lastname={m.lastname}
                            role={m.role}
                            photoUrl={m.photo_url}
                            size="sm"
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        <Separator />

        {/* Awards */}
        <section id="awards" className="scroll-mt-20">
          <AwardsTable awards={film.awards} filmId={film.film_id} onSaved={handleSaved} readOnly={!isAdmin} />
        </section>

        {/* Back to top */}
        <div className="flex justify-center pt-4 pb-2">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-xs text-muted-foreground hover:text-primary"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          >
            <ArrowUp className="h-3.5 w-3.5" />
            Back to top
          </Button>
        </div>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <Skeleton className="h-[400px] w-full" />
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <Skeleton className="h-6 w-96" />
        <Skeleton className="h-24 w-full" />
        <div className="flex gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-20 shrink-0 rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
