import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { GamePoolFilters } from "@/types/api";

// Shared decade list — consistent across Tag It / Chain It / Guess It.
// `min: null` on "All" → no constraint. "<50s" caps year_max at 1949.
export const DECADES = [
  { label: "All",   min: null, max: null },
  { label: "<50s",  min: null, max: 1949 },
  { label: "50s",   min: 1950, max: 1959 },
  { label: "60s",   min: 1960, max: 1969 },
  { label: "70s",   min: 1970, max: 1979 },
  { label: "80s",   min: 1980, max: 1989 },
  { label: "90s",   min: 1990, max: 1999 },
  { label: "2000s", min: 2000, max: 2009 },
  { label: "2010s", min: 2010, max: 2019 },
  { label: "2020s", min: 2020, max: 2029 },
] as const;

// Languages restricted to ones that actually have enough films to make a game viable.
export const GAME_LANGUAGES = [
  "English",
  "French",
  "Spanish",
  "Italian",
  "German",
  "Japanese",
  "Korean",
  "Chinese",
  "Russian",
] as const;

export interface DecadeRange {
  minIdx: number | null;  // index into DECADES (excluding "All"); null = no selection ("All")
  maxIdx: number | null;
}

export const NO_RANGE: DecadeRange = { minIdx: null, maxIdx: null };

/** Turn a (min, max) decade range into year_min/year_max for the API. */
export function rangeToFilters(range: DecadeRange): { year_min?: number; year_max?: number } {
  if (range.minIdx == null || range.maxIdx == null) return {};
  const lo = DECADES[range.minIdx];
  const hi = DECADES[range.maxIdx];
  const out: { year_min?: number; year_max?: number } = {};
  if (lo?.min != null) out.year_min = lo.min;
  if (hi?.max != null) out.year_max = hi.max;
  return out;
}

interface DecadeRangePickerProps {
  range: DecadeRange;
  onChange: (r: DecadeRange) => void;
}

/**
 * Click "All" to clear.
 * Click a single decade to select it.
 * Click another decade to extend the range (contiguous) between the two clicked.
 * Click the only selected decade again to deselect (back to All).
 */
export function DecadeRangePicker({ range, onChange }: DecadeRangePickerProps) {
  function handle(idx: number) {
    if (idx === 0) {
      onChange(NO_RANGE);
      return;
    }
    if (range.minIdx == null || range.maxIdx == null) {
      onChange({ minIdx: idx, maxIdx: idx });
      return;
    }
    if (range.minIdx === idx && range.maxIdx === idx) {
      onChange(NO_RANGE);
      return;
    }
    // Extend the range to include the clicked decade.
    const lo = Math.min(range.minIdx, idx);
    const hi = Math.max(range.maxIdx, idx);
    onChange({ minIdx: lo, maxIdx: hi });
  }

  function inRange(idx: number) {
    if (idx === 0) return range.minIdx == null;
    if (range.minIdx == null || range.maxIdx == null) return false;
    return idx >= range.minIdx && idx <= range.maxIdx;
  }

  return (
    <div className="flex flex-wrap justify-center gap-1">
      {DECADES.map((d, i) => {
        const active = inRange(i);
        return (
          <button
            key={d.label}
            onClick={() => handle(i)}
            className={cn(
              "rounded-md border px-2 py-1 text-xs font-medium",
              active
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-muted-foreground hover:text-foreground",
            )}
          >
            {d.label}
          </button>
        );
      })}
    </div>
  );
}

interface LanguagePickerProps {
  value: string;
  available: string[];  // names returned by the taxonomy endpoint
  onChange: (v: string) => void;
}

/** Restricts the language list to the curated GAME_LANGUAGES (and only those present in DB). */
export function LanguagePicker({ value, available, onChange }: LanguagePickerProps) {
  const allowed = GAME_LANGUAGES.filter((l) => available.includes(l));
  return (
    <Select value={value || "any"} onValueChange={(v) => onChange(v === "any" ? "" : v)}>
      <SelectTrigger className="h-9 w-44 text-xs">
        <SelectValue placeholder="Any language" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="any">Any language</SelectItem>
        {allowed.map((l) => (
          <SelectItem key={l} value={l}>{l}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/** Convenience: build the GamePoolFilters body from a range + language. */
export function buildPoolFilters(range: DecadeRange, language: string): GamePoolFilters {
  const f: GamePoolFilters = { ...rangeToFilters(range) };
  if (language) f.language = language;
  return f;
}
