import { cn } from "@/lib/utils";
import type { GameFilm } from "@/types/api";

interface FilmPickListProps {
  films: GameFilm[];
  poolSize: number;
  targetFilmId: number;
  targetVisible: boolean;
  onPick: (film: GameFilm) => void;
  disabled?: boolean;
  hideHeader?: boolean;
}

export function FilmPickList({ films, poolSize, targetFilmId, targetVisible, onPick, disabled, hideHeader }: FilmPickListProps) {
  return (
    <div className="flex flex-col gap-2">
      {!hideHeader && (
        <div className="text-xs text-muted-foreground">
          {poolSize} films matching · pick the next film in the chain
          {targetVisible && <span className="ml-2 text-amber-400">🎯 target is in the list!</span>}
        </div>
      )}
      {films.length === 0 ? (
        <div className="rounded-md border border-border bg-muted/20 p-4 text-center text-xs text-muted-foreground">
          No films match this combination. Try a different tag.
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
          {films.map((f) => {
            const isTarget = targetVisible && f.film_id === targetFilmId;
            return (
              <button
                key={f.film_id}
                onClick={() => onPick(f)}
                disabled={disabled}
                className={cn(
                  "group flex flex-col overflow-hidden rounded border-2 bg-muted/20 transition-all hover:border-primary disabled:cursor-not-allowed disabled:opacity-50",
                  isTarget
                    ? "border-amber-400 shadow-lg shadow-amber-400/30 ring-2 ring-amber-400/40"
                    : "border-border",
                )}
              >
                <div className="aspect-[2/3] w-full bg-muted">
                  {f.poster_url && (
                    <img src={f.poster_url} alt={f.title} className="h-full w-full object-cover" />
                  )}
                </div>
                <div className="p-1.5 text-left">
                  <div className="line-clamp-2 text-[11px] font-medium">{f.title}</div>
                  <div className="text-[10px] text-muted-foreground">{f.year ?? ""}</div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
