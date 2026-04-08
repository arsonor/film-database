import { useCallback, useRef, useState } from "react";
import { Check, MapPin, Plus, Search, Trash2, X } from "lucide-react";
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
import { searchGeography, updateFilm } from "@/api/client";
import type { FilmSetPlace, GeographySearchResult } from "@/types/api";

type PlaceType = "diegetic" | "shooting" | "fictional";

interface EditEntry {
  continent: string | null;
  country: string | null;
  state_city: string | null;
  place_type: PlaceType;
}

interface EditableGeographySectionProps {
  filmId: number;
  setPlaces: FilmSetPlace[];
  onSaved: () => void;
  readOnly?: boolean;
}

function placeLabel(place: { continent: string | null; country: string | null; state_city: string | null }) {
  const parts = [place.country, place.state_city].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : place.continent || "Unknown";
}

export function EditableGeographySection({
  filmId,
  setPlaces,
  onSaved,
  readOnly,
}: EditableGeographySectionProps) {
  const [editing, setEditing] = useState(false);
  const [entries, setEntries] = useState<EditEntry[]>([]);
  const [saving, setSaving] = useState(false);

  // Search state for adding new places
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeographySearchResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [newPlaceType, setNewPlaceType] = useState<PlaceType>("diegetic");
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const inputRef = useRef<HTMLInputElement>(null);

  const startEditing = useCallback(() => {
    setEntries(
      setPlaces.map((p) => ({
        continent: p.continent,
        country: p.country,
        state_city: p.state_city,
        place_type: p.place_type as PlaceType,
      })),
    );
    setEditing(true);
  }, [setPlaces]);

  const handleCancel = useCallback(() => {
    setEditing(false);
    setQuery("");
    setResults([]);
    setShowResults(false);
  }, []);

  const handleRemove = useCallback((index: number) => {
    setEntries((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleChangePlaceType = useCallback((index: number, pt: PlaceType) => {
    setEntries((prev) =>
      prev.map((e, i) => (i === index ? { ...e, place_type: pt } : e)),
    );
  }, []);

  const handleSearchChange = useCallback((value: string) => {
    setQuery(value);
    clearTimeout(searchTimeoutRef.current);
    if (!value || value.length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }
    searchTimeoutRef.current = setTimeout(async () => {
      const res = await searchGeography(value);
      setResults(res);
      setShowResults(true);
    }, 300);
  }, []);

  const handleSelectResult = useCallback(
    (r: GeographySearchResult) => {
      setEntries((prev) => [
        ...prev,
        {
          continent: r.continent,
          country: r.country,
          state_city: r.state_city,
          place_type: newPlaceType,
        },
      ]);
      setQuery("");
      setResults([]);
      setShowResults(false);
      inputRef.current?.focus();
    },
    [newPlaceType],
  );

  const handleAddCustom = useCallback(() => {
    if (!query.trim()) return;
    // Treat free text as country
    setEntries((prev) => [
      ...prev,
      {
        continent: null,
        country: query.trim(),
        state_city: null,
        place_type: newPlaceType,
      },
    ]);
    setQuery("");
    setResults([]);
    setShowResults(false);
    inputRef.current?.focus();
  }, [query, newPlaceType]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await updateFilm(filmId, {
        set_places: entries.map((e) => ({
          continent: e.continent,
          country: e.country,
          state_city: e.state_city,
          place_type: e.place_type,
        })),
      });
      setEditing(false);
      onSaved();
    } catch {
      // keep editing
    } finally {
      setSaving(false);
    }
  }, [filmId, entries, onSaved]);

  return (
    <div>
      <SectionHeading
        title="Geography"
        onEdit={readOnly ? undefined : () => (editing ? handleCancel() : startEditing())}
        editing={editing}
      />

      {!editing ? (
        setPlaces.length > 0 ? (
          <div className="space-y-1">
            {setPlaces.map((place, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="text-foreground">{placeLabel(place)}</span>
                <Badge variant="outline" className="text-[10px]">
                  {place.place_type}
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs italic text-muted-foreground">No locations yet</p>
        )
      ) : (
        <div className="space-y-3">
          {/* Current entries */}
          {entries.length > 0 && (
            <div className="space-y-1.5">
              {entries.map((entry, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-md border border-border px-2 py-1.5"
                >
                  <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  <span className="flex-1 truncate text-xs text-foreground">
                    {placeLabel(entry)}
                  </span>
                  <Select
                    value={entry.place_type}
                    onValueChange={(v) => handleChangePlaceType(i, v as PlaceType)}
                  >
                    <SelectTrigger className="h-6 w-24 text-[10px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="diegetic">diegetic</SelectItem>
                      <SelectItem value="shooting">shooting</SelectItem>
                      <SelectItem value="fictional">fictional</SelectItem>
                    </SelectContent>
                  </Select>
                  <button
                    onClick={() => handleRemove(i)}
                    className="rounded-full p-0.5 text-muted-foreground hover:bg-destructive/20 hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Add new — search + place type */}
          <div className="flex items-start gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                ref={inputRef}
                value={query}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={() => { if (results.length > 0) setShowResults(true); }}
                onBlur={() => setTimeout(() => setShowResults(false), 200)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && query.trim()) {
                    e.preventDefault();
                    handleAddCustom();
                  }
                }}
                placeholder="Search location..."
                className="h-8 pl-8 text-xs"
              />
              {showResults && (results.length > 0 || query.trim().length >= 2) && (
                <div className="absolute top-full z-50 mt-1 max-h-48 w-full overflow-y-auto rounded-md border bg-popover shadow-md">
                  {query.trim() && !results.some(
                    (r) => r.label.toLowerCase() === query.trim().toLowerCase(),
                  ) && (
                    <button
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={handleAddCustom}
                      className="flex w-full items-center px-3 py-1.5 text-xs font-medium text-primary hover:bg-accent hover:text-accent-foreground"
                    >
                      <Plus className="mr-1.5 h-3 w-3" /> Add "{query.trim()}"
                    </button>
                  )}
                  {results.map((r) => (
                    <button
                      key={r.geography_id}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleSelectResult(r)}
                      className="flex w-full items-center justify-between px-3 py-1.5 text-xs hover:bg-accent hover:text-accent-foreground"
                    >
                      <span className="truncate">{r.label}</span>
                      <span className="ml-2 text-muted-foreground">{r.film_count}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <Select
              value={newPlaceType}
              onValueChange={(v) => setNewPlaceType(v as PlaceType)}
            >
              <SelectTrigger className="h-8 w-24 text-[10px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="diegetic">diegetic</SelectItem>
                <SelectItem value="shooting">shooting</SelectItem>
                <SelectItem value="fictional">fictional</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Save / Cancel */}
          <div className="flex gap-2">
            <Button
              size="sm"
              className="h-7 gap-1 text-xs"
              onClick={handleSave}
              disabled={saving}
            >
              <Check className="h-3 w-3" />
              {saving ? "Saving..." : "Save"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={handleCancel}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
