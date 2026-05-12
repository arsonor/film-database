import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { PosterRow } from "./PosterRow";
import { getFilmsByCountry } from "@/api/client";
import type { FilmByCountry } from "@/types/api";

interface CountryFilmsPanelProps {
  iso: string;
  country: string;
  type: "production" | "set_place";
  onClose: () => void;
}

// Pure-ASCII unicode regional indicator flag emoji from ISO alpha-2 code.
function flagEmoji(iso: string): string {
  if (!iso || iso.length !== 2) return "";
  const A = 0x1f1e6;
  const codePoints = [...iso.toUpperCase()].map(
    (c) => A + (c.charCodeAt(0) - 65),
  );
  return String.fromCodePoint(...codePoints);
}

export function CountryFilmsPanel({
  iso,
  country,
  type,
  onClose,
}: CountryFilmsPanelProps) {
  const [films, setFilms] = useState<FilmByCountry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setFilms(null);
    setError(null);
    getFilmsByCountry(type, iso, 10)
      .then((data) => {
        if (!cancelled) setFilms(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [iso, type]);

  return (
    <div className="mt-3 rounded-lg border border-border bg-background p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl leading-none">{flagEmoji(iso)}</span>
          <h3 className="text-sm font-semibold text-foreground">{country}</h3>
          <span className="font-mono text-[10px] text-muted-foreground">
            {iso}
          </span>
          <span className="ml-1 text-xs text-muted-foreground">
            — top 10 {type === "production" ? "co-produced" : "set in"}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {error && (
        <p className="text-xs text-destructive">Failed to load: {error}</p>
      )}

      {films === null && !error && (
        <div className="flex gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-[195px] w-[130px] rounded-md" />
          ))}
        </div>
      )}

      {films && films.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No films matched for this country.
        </p>
      )}

      {films && films.length > 0 && (
        <PosterRow
          items={films.map((f) => ({
            film_id: f.film_id,
            title: f.title,
            poster_url: f.poster_url,
            year: f.year,
          }))}
        />
      )}
    </div>
  );
}
