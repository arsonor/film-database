import { useCallback, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight, Filter, LogIn, Lock, Sparkles } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
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

function SimilarFilmCard({ film, showScore }: { film: SimilarFilm; showScore: boolean }) {
  const year = film.first_release_date?.slice(0, 4);

  const sharedEntries = Object.entries(film.shared_tags).filter(
    ([, tags]) => tags.length > 0
  );

  const card = (
    <Link to={`/films/${film.film_id}`} className="group relative shrink-0 w-[140px]">
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
      <div className="mt-1.5 space-y-0.5">
        <p className="text-xs font-medium leading-tight line-clamp-2">
          {film.original_title}
        </p>
        <p className="text-[10px] text-muted-foreground">
          {year}{film.director ? ` · ${film.director}` : ""}
        </p>
      </div>
    </Link>
  );

  if (!showScore || sharedEntries.length === 0) return card;

  return (
    <Tooltip>
      <TooltipTrigger asChild>{card}</TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-[280px] space-y-1.5 p-3">
        {sharedEntries.map(([dim, tags]) => (
          <div key={dim}>
            <p className="text-[10px] font-semibold text-background/60">
              {dimensionLabel(dim)}
            </p>
            <div className="flex flex-wrap gap-1">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-block rounded bg-background/15 px-1.5 py-0.5 text-[10px]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </TooltipContent>
    </Tooltip>
  );
}

function TeaserCard({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link to={href} className="shrink-0 w-[140px]">
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-muted">
        <div className="absolute inset-0 backdrop-blur-sm bg-background/60 flex flex-col items-center justify-center gap-2 p-3 text-center">
          {icon}
          <p className="text-[11px] font-medium leading-tight">{label}</p>
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
    <TooltipProvider>
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

        {/* Reserve height during loading to prevent layout shift */}
        {isLoading ? (
          <div className="flex gap-3 overflow-hidden" style={{ minHeight: 260 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="shrink-0 w-[140px]">
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
            className="flex gap-3 overflow-x-auto snap-x snap-mandatory scrollbar-thin pb-2 items-start"
            style={{ minHeight: 260 }}
          >
            {items.map((item) => (
              <div key={item.film_id} className="snap-start">
                <SimilarFilmCard film={item} showScore={isPro} />
              </div>
            ))}

            {!isAuthenticated && (
              <div className="snap-start">
                <TeaserCard
                  href="/auth"
                  icon={<LogIn className="h-5 w-5 text-muted-foreground" />}
                  label="Sign up free for more"
                />
              </div>
            )}

            {isAuthenticated && !isPro && (
              <div className="snap-start">
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
    </TooltipProvider>
  );
}
