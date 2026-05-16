import { useState } from "react";
import { Star, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GameFilm } from "@/types/api";

interface FilmGridCellProps {
  film: GameFilm;
  removed: boolean;
  revealed?: boolean;
  shake?: boolean;
  disabled?: boolean;
  onRemove: (filmId: number) => void;
  onGuess: (filmId: number) => void;
}

export function FilmGridCell({ film, removed, revealed, shake, disabled, onRemove, onGuess }: FilmGridCellProps) {
  const [showActions, setShowActions] = useState(false);

  if (removed) {
    return (
      <div className="aspect-[2/3] rounded border border-dashed border-border/40 bg-muted/10 opacity-40" />
    );
  }

  return (
    <div className={cn("relative", shake && "animate-shake")}>
      <button
        onClick={() => !disabled && setShowActions((v) => !v)}
        disabled={disabled}
        className={cn(
          "group relative flex w-full flex-col overflow-hidden rounded-lg border-2 bg-muted/20 transition-all",
          revealed
            ? "border-amber-400 shadow-lg shadow-amber-400/40 ring-2 ring-amber-400/50"
            : showActions
              ? "border-primary"
              : "border-border hover:border-primary/60",
        )}
      >
        <div className="aspect-[2/3] w-full bg-muted">
          {film.poster_url && (
            <img src={film.poster_url} alt={film.title} className="h-full w-full object-cover" />
          )}
        </div>
        <div className="p-1.5 text-left">
          <div className="line-clamp-2 text-[11px] font-medium">{film.title}</div>
        </div>
      </button>
      {showActions && !disabled && !revealed && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-1.5 bg-black/80 p-1 rounded-lg">
          <button
            onClick={() => { setShowActions(false); onRemove(film.film_id); }}
            className="flex items-center gap-1 rounded-md bg-red-500/90 px-2 py-1.5 text-xs font-medium text-white hover:bg-red-500"
          >
            <X className="h-3 w-3" /> Remove
          </button>
          <button
            onClick={() => { setShowActions(false); onGuess(film.film_id); }}
            className="flex items-center gap-1 rounded-md bg-amber-500/90 px-2 py-1.5 text-xs font-medium text-white hover:bg-amber-500"
          >
            <Star className="h-3 w-3" /> This is it!
          </button>
          <button
            onClick={() => setShowActions(false)}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            cancel
          </button>
        </div>
      )}
    </div>
  );
}
