import { useNavigate } from "react-router-dom";
import type { PersonRank } from "@/types/api";
import { getNationalityFlag } from "@/lib/nationalityFlags";

interface PersonRankCardProps {
  person: PersonRank;
  role: "Director" | "Actor" | "Composer";
}

function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const first = parts[0] ?? "";
  if (parts.length === 1) return first.slice(0, 2).toUpperCase();
  const last = parts[parts.length - 1] ?? "";
  return ((first[0] ?? "") + (last[0] ?? "")).toUpperCase() || "?";
}

export function PersonRankCard({ person, role }: PersonRankCardProps) {
  const navigate = useNavigate();
  const flag = getNationalityFlag(person.nationality);
  const yearsLabel =
    person.first_year && person.last_year
      ? person.first_year === person.last_year
        ? `${person.first_year}`
        : `${person.first_year}–${person.last_year}`
      : "";

  return (
    <button
      onClick={() => navigate(`/browse?q=${encodeURIComponent(person.name)}`)}
      className="flex w-full items-center gap-3 rounded-lg border border-border bg-card p-2.5 text-left transition hover:border-primary/50 hover:bg-card/80"
      title={`${role}: ${person.name}`}
    >
      {person.photo_url ? (
        <img
          src={person.photo_url}
          alt={person.name}
          className="h-16 w-16 shrink-0 rounded-md object-cover"
        />
      ) : (
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-md bg-muted text-sm font-semibold text-muted-foreground">
          {initialsOf(person.name)}
        </div>
      )}
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{person.name}</div>
        <div className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
          {flag && <span>{flag}</span>}
          {person.nationality && <span className="truncate">{person.nationality}</span>}
        </div>
        <div className="mt-0.5 text-[11px]">
          <span className="font-semibold text-primary">{person.film_count}</span>{" "}
          <span className="text-muted-foreground">films</span>
          {yearsLabel && (
            <span className="ml-1 text-muted-foreground">
              · Active {yearsLabel}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}
