import { useCallback, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Filter, LogIn, Lock, Info } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { SectionHeading } from "./SectionHeading";
import { useSimilarFilms } from "@/hooks/useSimilarFilms";
import type { SimilarFilm } from "@/api/client";
import type { FilmDetail } from "@/types/api";
import { ARRAY_FILTER_KEYS } from "@/types/api";
import { dimensionLabel } from "@/lib/utils";

interface SimilarFilmsCarouselProps {
  filmId: number;
  film?: FilmDetail;
}

const CARD_WIDTH = "w-[130px]";

function SharedTagsContent({ entries }: { entries: [string, string[]][] }) {
  return (
    <div className="space-y-1.5">
      {entries.map(([dim, tags]) => (
        <div key={dim}>
          <p className="text-[10px] font-semibold text-muted-foreground">
            {dimensionLabel(dim)}
          </p>
          <div className="flex flex-wrap gap-1">
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-block rounded bg-muted px-1.5 py-0.5 text-[10px]"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SimilarFilmCard({ film, showScore }: { film: SimilarFilm; showScore: boolean }) {
  const year = film.first_release_date?.slice(0, 4);

  const sharedEntries = Object.entries(film.shared_tags).filter(
    ([, tags]) => tags.length > 0
  );

  return (
    <div className={`shrink-0 ${CARD_WIDTH}`}>
      <Link to={`/films/${film.film_id}`} className="group block">
        <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-muted">
          {film.poster_url ? (
            <img
              src={film.poster_url}
              alt={film.original_title}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-muted-foreground p-2 text-center">
              {film.original_title}
            </div>
          )}
          {showScore && (
            <div className="absolute top-1.5 right-1.5 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
              {film.score_pct}%
            </div>
          )}
        </div>
      </Link>
      <div className="mt-1.5 space-y-0.5">
        <Link to={`/films/${film.film_id}`}>
          <p className="text-xs font-medium leading-tight line-clamp-2 hover:underline">
            {film.original_title}
          </p>
        </Link>
        <div className="flex items-center gap-1">
          <p className="text-[10px] text-muted-foreground truncate">
            {year}{film.director ? ` · ${film.director}` : ""}
          </p>
          {showScore && sharedEntries.length > 0 && (
            <Popover>
              <PopoverTrigger asChild>
                <button
                  className="inline-flex items-center gap-0.5 rounded px-1 py-0.5 text-[10px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Info className="h-3 w-3" />
                  Why?
                </button>
              </PopoverTrigger>
              <PopoverContent side="bottom" align="start" className="w-64 p-3">
                <SharedTagsContent entries={sharedEntries} />
              </PopoverContent>
            </Popover>
          )}
        </div>
      </div>
    </div>
  );
}

function TeaserCard({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link to={href} className={`shrink-0 ${CARD_WIDTH}`}>
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg border border-dashed border-amber-500/30 bg-amber-500/5">
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-3 text-center">
          {icon}
          <p className="text-[11px] font-medium leading-tight text-foreground">{label}</p>
        </div>
      </div>
    </Link>
  );
}

export function SimilarFilmsCarousel({ filmId, film }: SimilarFilmsCarouselProps) {
  const navigate = useNavigate();
  const { tier, isAuthenticated } = useAuth();
  const isPro = isAuthenticated && (tier === "pro" || tier === "admin");
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, isError } = useSimilarFilms(filmId);

  const handleRefine = useCallback(() => {
    if (!film) return;
    const sp = new URLSearchParams();
    for (const key of ARRAY_FILTER_KEYS) {
      if (key === "studios") continue;
      const tags = film[key as keyof FilmDetail] as string[] | undefined;
      if (tags?.length) {
        for (const tag of tags) {
          sp.append(key, tag);
        }
      }
    }
    navigate(`/browse?${sp.toString()}`);
  }, [film, navigate]);

  const scroll = (dir: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = dir === "left" ? -300 : 300;
    scrollRef.current.scrollBy({ left: amount, behavior: "smooth" });
  };

  const items = data?.items ?? [];

  return (
      <div id="similar-films">
        <div className="flex items-center justify-between">
          <SectionHeading title="Similar Films" />
          <div className="flex items-center gap-1.5">
            {items.length > 4 && (
              <>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => scroll("left")}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => scroll("right")}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </>
            )}
            {isPro && film && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefine}
                className="gap-1.5 text-xs"
              >
                <Filter className="h-3.5 w-3.5" />
                Refine in Browse
              </Button>
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="flex gap-3 overflow-hidden">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className={`shrink-0 ${CARD_WIDTH}`}>
                <Skeleton className="aspect-[2/3] rounded-lg" />
                <Skeleton className="mt-1.5 h-3 w-3/4" />
                <Skeleton className="mt-1 h-2.5 w-1/2" />
              </div>
            ))}
          </div>
        ) : isError ? (
          <p className="text-sm text-muted-foreground py-4">
            Could not load recommendations.
          </p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            Not enough tags to compute similar films.
          </p>
        ) : (
          <div
            ref={scrollRef}
            className="flex gap-3 overflow-x-auto snap-x scrollbar-thin pb-2 items-start"
          >
            {items.map((item) => (
              <div key={item.film_id} className={`snap-start shrink-0 ${CARD_WIDTH}`}>
                <SimilarFilmCard film={item} showScore={isPro} />
              </div>
            ))}

            {!isAuthenticated && (
              <div className={`snap-start shrink-0 ${CARD_WIDTH}`}>
                <TeaserCard
                  href="/auth"
                  icon={<LogIn className="h-5 w-5 text-amber-500/60" />}
                  label="Sign in for more recommendations"
                />
              </div>
            )}

            {isAuthenticated && !isPro && (
              <div className={`snap-start shrink-0 ${CARD_WIDTH}`}>
                <TeaserCard
                  href="/auth"
                  icon={<Lock className="h-5 w-5 text-amber-500/60" />}
                  label="Upgrade to Pro for full recommendations"
                />
              </div>
            )}
          </div>
        )}
      </div>
  );
}
