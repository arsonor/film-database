import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Eye, EyeOff, Heart, Bookmark } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { updateUserFilmStatus } from "@/api/client";
import type { FilmListItem } from "@/types/api";
import { formatYear } from "@/lib/utils";

interface FilmCardProps {
  film: FilmListItem;
  canToggleStatus?: boolean;
  onStatusChanged?: () => void;
}

export function FilmCard({ film, canToggleStatus, onStatusChanged }: FilmCardProps) {
  const [seen, setSeen] = useState(film.user_status?.seen ?? false);
  const [favorite, setFavorite] = useState(film.user_status?.favorite ?? false);
  const [watchlist, setWatchlist] = useState(film.user_status?.watchlist ?? false);

  useEffect(() => { setSeen(film.user_status?.seen ?? false); }, [film.user_status?.seen]);
  useEffect(() => { setFavorite(film.user_status?.favorite ?? false); }, [film.user_status?.favorite]);
  useEffect(() => { setWatchlist(film.user_status?.watchlist ?? false); }, [film.user_status?.watchlist]);

  const handleToggleSeen = useCallback(
    async (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const next = !seen;
      setSeen(next);
      try {
        await updateUserFilmStatus(film.film_id, { seen: next });
        onStatusChanged?.();
      } catch {
        setSeen(seen);
      }
    },
    [film.film_id, seen],
  );

  const handleToggleFavorite = useCallback(
    async (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const next = !favorite;
      setFavorite(next);
      try {
        await updateUserFilmStatus(film.film_id, { favorite: next });
        onStatusChanged?.();
      } catch {
        setFavorite(favorite);
      }
    },
    [film.film_id, favorite],
  );

  const handleToggleWatchlist = useCallback(
    async (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const next = !watchlist;
      setWatchlist(next);
      try {
        await updateUserFilmStatus(film.film_id, { watchlist: next });
        onStatusChanged?.();
      } catch {
        setWatchlist(watchlist);
      }
    },
    [film.film_id, watchlist],
  );

  return (
    <Link
      to={`/films/${film.film_id}`}
      className="group relative flex flex-col overflow-hidden rounded-lg bg-card transition-all hover:scale-105 hover:shadow-xl hover:shadow-black/40"
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] w-full overflow-hidden">
        {film.poster_url ? (
          <img
            src={film.poster_url}
            alt={film.original_title}
            className="h-full w-full object-cover transition-opacity group-hover:opacity-90"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-muted to-card p-4 text-center">
            <span className="text-sm text-muted-foreground">{film.original_title}</span>
          </div>
        )}
        {/* Status icons */}
        {canToggleStatus && (
          <div className="absolute right-2 top-2 flex flex-col gap-1.5">
            <button
              onClick={handleToggleSeen}
              className={`flex h-6 w-6 items-center justify-center rounded-full shadow-md transition-colors ${
                seen
                  ? "bg-emerald-500/90 text-white hover:bg-emerald-600"
                  : "bg-background/60 text-muted-foreground opacity-0 backdrop-blur hover:bg-background/80 group-hover:opacity-100"
              }`}
              title={seen ? "Mark as unseen" : "Mark as seen"}
            >
              {seen ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
            </button>
            <button
              onClick={handleToggleFavorite}
              className={`flex h-6 w-6 items-center justify-center rounded-full shadow-md transition-colors ${
                favorite
                  ? "bg-rose-500/90 text-white hover:bg-rose-600"
                  : "bg-background/60 text-muted-foreground opacity-0 backdrop-blur hover:bg-background/80 group-hover:opacity-100"
              }`}
              title={favorite ? "Remove from favorites" : "Add to favorites"}
            >
              <Heart className={`h-3.5 w-3.5 ${favorite ? "fill-current" : ""}`} />
            </button>
            <button
              onClick={handleToggleWatchlist}
              className={`flex h-6 w-6 items-center justify-center rounded-full shadow-md transition-colors ${
                watchlist
                  ? "bg-amber-500/90 text-white hover:bg-amber-600"
                  : "bg-background/60 text-muted-foreground opacity-0 backdrop-blur hover:bg-background/80 group-hover:opacity-100"
              }`}
              title={watchlist ? "Remove from watchlist" : "Add to watchlist"}
            >
              <Bookmark className={`h-3.5 w-3.5 ${watchlist ? "fill-current" : ""}`} />
            </button>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col gap-1 p-2.5">
        <h3 className="line-clamp-2 text-sm font-medium leading-tight text-foreground">
          {film.original_title}
        </h3>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{formatYear(film.first_release_date)}</span>
          {film.director && (
            <>
              <span className="text-border">|</span>
              <span className="truncate">{film.director}</span>
            </>
          )}
        </div>
        {film.categories.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {film.categories.slice(0, 3).map((cat) => (
              <Badge key={cat} variant="outline" className="px-1.5 py-0 text-[10px] text-muted-foreground">
                {cat}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
