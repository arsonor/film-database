import { Ban, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ArrayFilterKey, FilterState } from "@/types/api";
import { ARRAY_FILTER_KEYS } from "@/types/api";
import { dimensionLabel } from "@/lib/utils";

interface ActiveFiltersProps {
  filters: FilterState;
  onRemoveArrayFilter: (dimension: ArrayFilterKey, value: string) => void;
  onClearAll: () => void;
  onUpdateFilters: (updates: Partial<FilterState>) => void;
}

export function ActiveFilters({
  filters,
  onRemoveArrayFilter,
  onClearAll,
  onUpdateFilters,
}: ActiveFiltersProps) {
  const chips: { key: string; label: string; excluded?: boolean; onRemove: () => void }[] = [];

  // Tag filters
  for (const key of ARRAY_FILTER_KEYS) {
    const tf = filters[key];
    for (const value of tf.include) {
      chips.push({
        key: `${key}:${value}`,
        label: `${dimensionLabel(key)}: ${value}`,
        onRemove: () => onRemoveArrayFilter(key, value),
      });
    }
    for (const value of tf.exclude) {
      chips.push({
        key: `${key}:!${value}`,
        label: `${dimensionLabel(key)}: ${value}`,
        excluded: true,
        onRemove: () => onRemoveArrayFilter(key, value),
      });
    }
  }

  // Search
  if (filters.q) {
    chips.push({
      key: "q",
      label: `Search: "${filters.q}"`,
      onRemove: () => onUpdateFilters({ q: "" }),
    });
  }

  // Location
  if (filters.location) {
    chips.push({
      key: "location",
      label: `Location: ${filters.location}`,
      onRemove: () => onUpdateFilters({ location: "" }),
    });
  }

  // Language
  if (filters.language) {
    chips.push({
      key: "language",
      label: `Language: ${filters.language}`,
      onRemove: () => onUpdateFilters({ language: "" }),
    });
  }

  // Source
  if (filters.source) {
    chips.push({
      key: "source",
      label: `Source: ${filters.source}`,
      onRemove: () => onUpdateFilters({ source: "" }),
    });
  }

  // Year range
  if (filters.year_min !== null) {
    chips.push({
      key: "year_min",
      label: `From: ${filters.year_min}`,
      onRemove: () => onUpdateFilters({ year_min: null }),
    });
  }
  if (filters.year_max !== null) {
    chips.push({
      key: "year_max",
      label: `To: ${filters.year_max}`,
      onRemove: () => onUpdateFilters({ year_max: null }),
    });
  }

  // Seen
  if (filters.vu !== null) {
    chips.push({
      key: "vu",
      label: filters.vu ? "Seen" : "Unseen",
      onRemove: () => onUpdateFilters({ vu: null }),
    });
  }

  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 px-1 pb-3">
      {chips.map((chip) => (
        <Badge
          key={chip.key}
          variant="secondary"
          className={`gap-1 pl-2 pr-1 py-1 text-xs ${
            chip.excluded ? "border-red-400/50 bg-red-500/10 text-red-400 line-through" : ""
          }`}
        >
          {chip.excluded && <Ban className="h-3 w-3 shrink-0" />}
          {chip.label}
          <button
            onClick={chip.onRemove}
            className="ml-0.5 rounded-sm p-0.5 hover:bg-muted-foreground/20 transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
      <Button variant="ghost" size="sm" onClick={onClearAll} className="h-7 text-xs text-muted-foreground">
        Clear all
      </Button>
    </div>
  );
}
