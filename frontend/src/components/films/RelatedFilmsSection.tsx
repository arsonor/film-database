import { useCallback, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Film, Plus, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SectionHeading } from "./SectionHeading";
import {
  addFilmRelation,
  deleteFilmRelation,
  searchLocalFilms,
} from "@/api/client";
import type { FilmRelation } from "@/types/api";

const RELATION_TYPES = ["sequel", "prequel", "remake", "spinoff", "reboot"] as const;

interface RelatedFilmsSectionProps {
  filmId: number;
  sequels: FilmRelation[];
  onSaved: () => void;
}

export function RelatedFilmsSection({
  filmId,
  sequels,
  onSaved,
}: RelatedFilmsSectionProps) {
  const [editing, setEditing] = useState(false);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<
    { film_id: number; original_title: string; year: number | null }[]
  >([]);
  const [showResults, setShowResults] = useState(false);
  const [relationType, setRelationType] = useState<string>("remake");
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const handleSearch = useCallback((value: string) => {
    setSearch(value);
    clearTimeout(timeoutRef.current);
    if (!value || value.length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }
    timeoutRef.current = setTimeout(async () => {
      const res = await searchLocalFilms(value);
      // Exclude current film and already-linked films
      const linkedIds = new Set(sequels.map((s) => s.related_film_id));
      setResults(
        res.filter((r) => r.film_id !== filmId && !linkedIds.has(r.film_id)),
      );
      setShowResults(true);
    }, 300);
  }, [filmId, sequels]);

  const handleAdd = useCallback(
    async (relatedFilmId: number) => {
      await addFilmRelation(filmId, relatedFilmId, relationType);
      setSearch("");
      setResults([]);
      setShowResults(false);
      onSaved();
    },
    [filmId, relationType, onSaved],
  );

  const handleRemove = useCallback(
    async (relatedFilmId: number) => {
      await deleteFilmRelation(filmId, relatedFilmId);
      onSaved();
    },
    [filmId, onSaved],
  );

  return (
    <section>
      <SectionHeading
        title="Related Films"
        onEdit={() => setEditing(!editing)}
        editing={editing}
      />

      {sequels.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {sequels.map((rel) => (
            <div
              key={rel.related_film_id}
              className="group flex items-center gap-2 rounded-lg border border-border px-3 py-2 transition-colors hover:border-primary"
            >
              <Link
                to={`/films/${rel.related_film_id}`}
                className="flex items-center gap-2"
              >
                <Film className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
                <span className="text-sm text-foreground">
                  {rel.related_film_title}
                </span>
                <Badge variant="outline" className="text-[10px]">
                  {rel.relation_type}
                </Badge>
              </Link>
              {editing && (
                <button
                  onClick={() => handleRemove(rel.related_film_id)}
                  className="ml-1 rounded-full p-0.5 text-muted-foreground hover:bg-destructive/20 hover:text-destructive"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        !editing && (
          <p className="text-xs italic text-muted-foreground">
            No related films yet
          </p>
        )
      )}

      {editing && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center gap-2">
            {/* Relation type selector */}
            <Select value={relationType} onValueChange={setRelationType}>
              <SelectTrigger className="h-8 w-32 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {RELATION_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Film search input */}
            <div className="relative flex-1">
              <Plus className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => results.length > 0 && setShowResults(true)}
                onBlur={() =>
                  setTimeout(() => setShowResults(false), 200)
                }
                placeholder="Search film to link..."
                className="h-8 pl-8 text-xs"
              />
              {showResults && results.length > 0 && (
                <div className="absolute top-full z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-md border bg-popover shadow-md">
                  {results.map((r) => (
                    <button
                      key={r.film_id}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleAdd(r.film_id)}
                      className="flex w-full items-center justify-between px-3 py-1.5 text-xs hover:bg-accent hover:text-accent-foreground"
                    >
                      <span className="truncate">{r.original_title}</span>
                      <span className="ml-2 text-muted-foreground">
                        {r.year ?? "—"}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={() => {
              setEditing(false);
              setSearch("");
              setResults([]);
            }}
          >
            Done
          </Button>
        </div>
      )}
    </section>
  );
}
