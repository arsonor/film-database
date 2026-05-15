import { ChevronRight, Info } from "lucide-react";
import type { ChainFilm } from "@/types/api";
import { cn } from "@/lib/utils";

export interface ChainStepEntry {
  film: ChainFilm;
  via_tag?: { dimension: string; value: string } | null;
}

interface ChainProgressProps {
  origin: ChainFilm;
  target: ChainFilm;
  steps: ChainStepEntry[];
  onTargetInfo?: () => void;
}

function MiniPoster({
  film, dim, label, onInfo,
}: {
  film: ChainFilm; dim?: boolean; label?: string; onInfo?: () => void;
}) {
  return (
    <div className={cn("flex flex-col items-center gap-1", dim && "opacity-70")}>
      {label && (
        <span className="text-[9px] uppercase tracking-wide text-muted-foreground">{label}</span>
      )}
      <div className="relative">
        <div className="h-16 w-11 overflow-hidden rounded border border-border bg-muted">
          {film.poster_url ? (
            <img src={film.poster_url} alt={film.title} className="h-full w-full object-cover" />
          ) : null}
        </div>
        {onInfo && (
          <button
            onClick={(e) => { e.stopPropagation(); onInfo(); }}
            aria-label="Read synopsis"
            className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full border border-primary/60 bg-primary text-primary-foreground shadow-sm hover:bg-primary/90"
          >
            <Info className="h-3 w-3" />
          </button>
        )}
      </div>
      <div className="line-clamp-1 max-w-[80px] text-center text-[10px] text-muted-foreground">
        {film.title}
      </div>
    </div>
  );
}

export function ChainProgress({ origin, target, steps, onTargetInfo }: ChainProgressProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto py-2">
      <MiniPoster film={origin} label="Origin" />
      {steps.map((s, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <div className="flex flex-col items-center px-1">
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            {s.via_tag && (
              <span className="rounded bg-emerald-500/15 px-1 text-[9px] text-emerald-300">
                {s.via_tag.value}
              </span>
            )}
          </div>
          <MiniPoster film={s.film} />
        </div>
      ))}
      <ChevronRight className="h-3 w-3 text-muted-foreground" />
      <MiniPoster film={target} label="Target" onInfo={onTargetInfo} />
    </div>
  );
}
