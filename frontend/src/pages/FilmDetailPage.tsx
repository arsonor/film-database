import { useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft,
  Eye,
  EyeOff,
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
import { deleteFilm, toggleVu } from "@/api/client";
import { PersonCard } from "@/components/films/PersonCard";
import { ExternalLinks } from "@/components/films/ExternalLinks";
import { AwardsTable } from "@/components/films/AwardsTable";
import { EditableFinancials } from "@/components/films/EditableFinancials";
import { EditableTagSection } from "@/components/films/EditableTagSection";
import { RelatedFilmsSection } from "@/components/films/RelatedFilmsSection";
import { SimilarFilmsCarousel } from "@/components/films/SimilarFilmsCarousel";
import { SectionHeading } from "@/components/films/SectionHeading";
import type { CrewMember } from "@/types/api";
import {
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
  const { isAdmin } = useAuth();
  const { film, setFilm, loading, error, refetch } = useFilmDetail(filmId);

  const handleToggleVu = useCallback(async () => {
    if (!film) return;
    const newVu = !film.vu;
    // Optimistic update
    setFilm({ ...film, vu: newVu });
    try {
      await toggleVu(film.film_id, newVu);
    } catch {
      // Revert on error
      setFilm({ ...film, vu: film.vu });
    }
  }, [film, setFilm]);

  const handleDelete = useCallback(async () => {
    if (!film) return;
    if (!window.confirm(`Delete "${film.original_title}" and all its data? This cannot be undone.`)) return;
    try {
      await deleteFilm(film.film_id);
      navigate("/browse");
    } catch {
      // stay on page
    }
  }, [film, navigate]);

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
      <div className="relative">
        {/* Backdrop */}
        {backdropUrl ? (
          <div className="relative h-[320px] w-full overflow-hidden sm:h-[420px] lg:h-[480px]">
            <img
              src={backdropUrl}
              alt=""
              className="h-full w-full object-cover"
            />
            {/* Gradient overlays */}
            <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-background/40 to-transparent" />
          </div>
        ) : (
          <div className="h-[200px] w-full bg-card sm:h-[300px]" />
        )}

        {/* Hero Content — overlaid on backdrop */}
        <div className="absolute inset-x-0 bottom-0 px-4 pb-6 sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-6xl gap-6">
            {/* Back button */}
            <Button
              variant="ghost"
              size="icon"
              className="absolute left-4 top-4 z-10 bg-background/50 backdrop-blur sm:left-6"
              onClick={() => navigate(-1)}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>

            {/* Poster */}
            <div className="hidden shrink-0 sm:block">
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

            {/* Info block */}
            <div className="flex min-w-0 flex-1 flex-col justify-end gap-3">
              {/* Title */}
              <h1 className="text-2xl font-bold leading-tight text-foreground sm:text-3xl lg:text-4xl">
                {film.original_title}
              </h1>

              {/* Localized titles */}
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

              {/* Meta line: year, duration, color */}
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

              {/* Categories */}
              {film.categories.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {film.categories.map((cat) => (
                    <Badge key={cat} className="text-xs">
                      {cat}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Directors */}
              {directors.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  Directed by{" "}
                  {directors.map((d, i) => (
                    <span key={d.person_id}>
                      {i > 0 && ", "}
                      <button
                        onClick={() =>
                          navigate(
                            `/browse?q=${encodeURIComponent(formatPersonName(d.firstname, d.lastname))}`,
                          )
                        }
                        className="font-medium text-foreground hover:text-primary"
                      >
                        {formatPersonName(d.firstname, d.lastname)}
                      </button>
                    </span>
                  ))}
                </p>
              )}

              {/* Seen toggle + External links row */}
              <div className="flex flex-wrap items-center gap-3">
                {isAdmin ? (
                  <Button
                    variant={film.vu ? "default" : "outline"}
                    size="sm"
                    className={`gap-1.5 ${film.vu ? "bg-emerald-600 hover:bg-emerald-700" : ""}`}
                    onClick={handleToggleVu}
                  >
                    {film.vu ? (
                      <>
                        <Eye className="h-4 w-4" /> Seen
                      </>
                    ) : (
                      <>
                        <EyeOff className="h-4 w-4" /> Unseen
                      </>
                    )}
                  </Button>
                ) : (
                  <Badge variant={film.vu ? "default" : "outline"} className={`gap-1.5 ${film.vu ? "bg-emerald-600" : ""}`}>
                    {film.vu ? <><Eye className="h-3 w-3" /> Seen</> : <><EyeOff className="h-3 w-3" /> Unseen</>}
                  </Badge>
                )}

                <ExternalLinks
                  tmdbId={film.tmdb_id}
                  imdbId={film.imdb_id}
                  title={film.original_title}
                  year={film.first_release_date}
                />

                {isAdmin && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={handleDelete}
                    title="Delete film"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>

              {/* Production info — compact, in hero area */}
              <div className="space-y-1 text-sm text-muted-foreground">
                {film.studios.length > 0 && (
                  <div>{film.studios.join(" · ")}</div>
                )}
                {film.sources.length > 0 &&
                  film.sources.map((src, i) => (
                    <div key={i}>
                      {src.source_type}
                      {src.source_title && `: ${src.source_title}`}
                      {src.author && ` by ${src.author}`}
                    </div>
                  ))}
                <div className="flex items-center gap-2">
                  {film.budget != null && film.budget > 0 && (
                    <span>Budget: {formatCurrency(film.budget)}</span>
                  )}
                  {film.budget != null && film.budget > 0 && film.revenue != null && film.revenue > 0 && (
                    <span className="text-border">|</span>
                  )}
                  {film.revenue != null && film.revenue > 0 && (
                    <span>Revenue: {formatCurrency(film.revenue)}</span>
                  )}
                  {isAdmin && (
                    <EditableFinancials
                      filmId={film.film_id}
                      budget={film.budget}
                      revenue={film.revenue}
                      onSaved={refetch}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile poster (shown below hero on small screens) */}
      <div className="px-4 sm:hidden">
        {posterUrl && (
          <img
            src={posterUrl}
            alt={film.original_title}
            className="-mt-24 relative z-10 mx-auto w-40 rounded-lg shadow-2xl"
          />
        )}
      </div>

      {/* ================================================================ */}
      {/* Content Sections */}
      {/* ================================================================ */}
      <div className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
        {/* Synopsis */}
        {film.summary && (
          <section>
            <SectionHeading title="Synopsis" />
            <p className="leading-relaxed text-muted-foreground">{film.summary}</p>
          </section>
        )}

        {/* Related Films */}
        <RelatedFilmsSection
          filmId={film.film_id}
          sequels={film.sequels}
          onSaved={refetch}
          readOnly={!isAdmin}
        />

        <Separator />

        {/* Cast */}
        {film.cast.length > 0 && (
          <section>
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
          </section>
        )}

        {/* Crew */}
        {crewGroups.length > 0 && (
          <section>
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
          </section>
        )}

        <Separator />

        {/* Classification — editable taxonomy sections */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-foreground">Classification</h2>
          <div className="grid gap-6 sm:grid-cols-2">
            <EditableTagSection
              filmId={film.film_id}
              dimension="categories"
              currentValues={film.categories}
              onSaved={refetch}
              readOnly={!isAdmin}
            />
            <EditableTagSection
              filmId={film.film_id}
              dimension="cinema_types"
              currentValues={film.cinema_types}
              onSaved={refetch}
              readOnly={!isAdmin}
            />
          </div>
        </section>

        {/* Context & Themes — editable */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-foreground">Context & Themes</h2>
          <div className="grid gap-6 sm:grid-cols-2">
            <EditableTagSection
              filmId={film.film_id}
              dimension="themes"
              currentValues={film.themes}
              onSaved={refetch}
              readOnly={!isAdmin}
            />
            <EditableTagSection
              filmId={film.film_id}
              dimension="characters"
              currentValues={film.characters}
              onSaved={refetch}
              readOnly={!isAdmin}
            />
            <EditableTagSection
              filmId={film.film_id}
              dimension="motivations"
              currentValues={film.motivations}
              onSaved={refetch}
              readOnly={!isAdmin}
            />
            <EditableTagSection
              filmId={film.film_id}
              dimension="atmospheres"
              currentValues={film.atmospheres}
              onSaved={refetch}
              readOnly={!isAdmin}
            />
            <EditableTagSection
              filmId={film.film_id}
              dimension="messages"
              currentValues={film.messages}
              onSaved={refetch}
              readOnly={!isAdmin}
            />
          </div>
        </section>

        <Separator />

        {/* Setting */}
        <section>
          <SectionHeading title="Setting" />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {/* Time periods */}
            <EditableTagSection
              filmId={film.film_id}
              dimension="time_periods"
              currentValues={film.time_periods}
              onSaved={refetch}
              readOnly={!isAdmin}
            />

            {/* Place contexts */}
            <EditableTagSection
              filmId={film.film_id}
              dimension="place_contexts"
              currentValues={film.place_contexts}
              onSaved={refetch}
              readOnly={!isAdmin}
            />

            {/* Geography */}
            {film.set_places.length > 0 && (
              <div>
                <h3 className="mb-3 text-lg font-semibold text-foreground">Geography</h3>
                <div className="space-y-1">
                  {film.set_places.map((place, i) => {
                    const parts = [place.country, place.state_city].filter(Boolean);
                    const label = parts.length > 0 ? parts.join(", ") : place.continent || "Unknown";
                    return (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <span className="text-foreground">{label}</span>
                        <Badge variant="outline" className="text-[10px]">
                          {place.place_type}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </section>

        <Separator />

        {/* Awards */}
        <section>
          <AwardsTable awards={film.awards} filmId={film.film_id} onSaved={refetch} readOnly={!isAdmin} />
        </section>

        <Separator />

        {/* Streaming */}
        {film.streaming_platforms.length > 0 && (
          <section>
            <SectionHeading title="Streaming" />
            <div className="flex flex-wrap gap-2">
              {film.streaming_platforms.map((platform) => (
                <Badge key={platform} variant="secondary" className="gap-1.5 text-xs">
                  <Tv className="h-3 w-3" />
                  {platform}
                </Badge>
              ))}
            </div>
          </section>
        )}

        <Separator />

        {/* Similar Films (placeholder) */}
        <section>
          <SimilarFilmsCarousel filmId={film.film_id} />
        </section>
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
