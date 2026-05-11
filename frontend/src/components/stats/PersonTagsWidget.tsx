import { useCallback, useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getPersonTags, searchPeopleWithFilms } from "@/api/client";
import type {
  PersonRole,
  PersonSearchResult,
  PersonTagsResponse,
  TagCount,
} from "@/types/api";

const ROLES: { value: PersonRole; label: string }[] = [
  { value: "director", label: "Director" },
  { value: "composer", label: "Composer" },
  { value: "actor", label: "Actor" },
];

const DEBOUNCE_MS = 250;

export function PersonTagsWidget() {
  const [role, setRole] = useState<PersonRole>("director");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PersonSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState<PersonSearchResult | null>(null);
  const [tags, setTags] = useState<PersonTagsResponse | null>(null);
  const [loadingTags, setLoadingTags] = useState(false);

  const reset = useCallback(() => {
    setQuery("");
    setResults([]);
    setSelected(null);
    setTags(null);
  }, []);

  // Reset everything when role changes
  const handleRoleChange = useCallback(
    (next: PersonRole) => {
      if (next === role) return;
      setRole(next);
      reset();
    },
    [role, reset],
  );

  // Debounced search
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (selected) return;
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(async () => {
      setSearching(true);
      try {
        const found = await searchPeopleWithFilms(role, query.trim());
        setResults(found);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, DEBOUNCE_MS);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [query, role, selected]);

  const pickPerson = useCallback(
    async (p: PersonSearchResult) => {
      setSelected(p);
      setResults([]);
      setQuery("");
      setLoadingTags(true);
      try {
        const t = await getPersonTags(p.person_id, role);
        setTags(t);
      } catch {
        setTags(null);
      } finally {
        setLoadingTags(false);
      }
    },
    [role],
  );

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      {/* Role toggle + search */}
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="flex gap-1 rounded-md border border-border bg-background p-0.5">
          {ROLES.map((r) => (
            <button
              key={r.value}
              type="button"
              onClick={() => handleRoleChange(r.value)}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                role === r.value
                  ? "bg-amber-500/20 text-amber-500"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
        {!selected && (
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${role}s with ≥ 3 films…`}
            className="max-w-sm"
          />
        )}
        {selected && (
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium text-foreground">{selected.name}</span>
            <span className="text-muted-foreground">— {selected.film_count} films</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={reset}
              className="h-6 w-6 p-0"
              title="Reset"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Search results dropdown */}
      {!selected && query.trim().length >= 2 && (
        <div className="mb-3 max-h-60 overflow-y-auto rounded-md border border-border bg-background">
          {searching && results.length === 0 && (
            <div className="px-3 py-2 text-xs text-muted-foreground">Searching…</div>
          )}
          {!searching && results.length === 0 && (
            <div className="px-3 py-2 text-xs text-muted-foreground">No matches</div>
          )}
          {results.map((p) => (
            <button
              key={p.person_id}
              type="button"
              onClick={() => pickPerson(p)}
              className="flex w-full items-center justify-between px-3 py-1.5 text-left text-sm hover:bg-amber-500/10"
            >
              <span className="text-foreground">{p.name}</span>
              <span className="text-xs text-muted-foreground">{p.film_count} films</span>
            </button>
          ))}
        </div>
      )}

      {/* Ranked lists */}
      {selected && (
        <div className="grid gap-4 sm:grid-cols-2">
          {loadingTags && (
            <>
              <SkeletonBlock title="Top 8 themes" />
              <SkeletonBlock title="Top 5 atmospheres" />
              <SkeletonBlock title="Top 5 characters" />
              <SkeletonBlock title="Top 3 messages" />
            </>
          )}
          {!loadingTags && tags && (
            <>
              <RankBlock title="Top 8 themes" items={tags.top_themes} />
              <RankBlock title="Top 5 atmospheres" items={tags.top_atmospheres} />
              <RankBlock title="Top 5 characters" items={tags.top_characters} />
              <RankBlock title="Top 3 messages" items={tags.top_messages} />
            </>
          )}
        </div>
      )}
    </div>
  );
}

function RankBlock({ title, items }: { title: string; items: TagCount[] }) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      {items.length === 0 ? (
        <p className="text-xs text-muted-foreground">No data</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {items.map((t) => (
            <Badge
              key={t.name}
              variant="outline"
              className="border-amber-500/40 text-xs text-foreground"
            >
              {t.name} <span className="ml-1 text-muted-foreground">({t.count})</span>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function SkeletonBlock({ title }: { title: string }) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <div className="flex flex-wrap gap-1.5">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-5 w-16" />
        ))}
      </div>
    </div>
  );
}
