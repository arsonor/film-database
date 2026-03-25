import { useCallback, useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FilterSection } from "@/components/filters/FilterSection";
import { searchGeography } from "@/api/client";
import type {
  ArrayFilterKey,
  FilterState,
  GeographySearchResult,
  TaxonomyItem,
} from "@/types/api";
import { TAXONOMY_DIMENSIONS } from "@/types/api";
import { dimensionLabel } from "@/lib/utils";

interface SidebarProps {
  filters: FilterState;
  taxonomies: Record<string, TaxonomyItem[]>;
  languages: TaxonomyItem[];
  onToggleFilter: (dimension: ArrayFilterKey, value: string) => void;
  onUpdateFilters: (updates: Partial<FilterState>) => void;
  onSetVu: (vu: boolean | null) => void;
}

// Which dimensions start expanded
const EXPANDED_BY_DEFAULT = new Set(["categories", "themes", "atmospheres"]);

export function SidebarContent({
  filters,
  taxonomies,
  languages,
  onToggleFilter,
  onUpdateFilters,
  onSetVu,
}: SidebarProps) {
  // Location autocomplete state
  const [locationQuery, setLocationQuery] = useState(filters.location);
  const [locationResults, setLocationResults] = useState<GeographySearchResult[]>([]);
  const [showLocationResults, setShowLocationResults] = useState(false);
  const locationTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Director debounce
  const [directorInput, setDirectorInput] = useState(filters.director);
  const directorTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Year range
  const [yearMinInput, setYearMinInput] = useState(
    filters.year_min !== null ? String(filters.year_min) : "",
  );
  const [yearMaxInput, setYearMaxInput] = useState(
    filters.year_max !== null ? String(filters.year_max) : "",
  );

  // Sync external filter changes to local inputs
  useEffect(() => {
    setLocationQuery(filters.location);
  }, [filters.location]);
  useEffect(() => {
    setDirectorInput(filters.director);
  }, [filters.director]);

  // Location search with debounce
  const handleLocationChange = useCallback(
    (value: string) => {
      setLocationQuery(value);
      clearTimeout(locationTimeoutRef.current);
      if (!value || value.length < 2) {
        setLocationResults([]);
        setShowLocationResults(false);
        if (!value) onUpdateFilters({ location: "" });
        return;
      }
      locationTimeoutRef.current = setTimeout(async () => {
        const results = await searchGeography(value);
        setLocationResults(results);
        setShowLocationResults(true);
      }, 300);
    },
    [onUpdateFilters],
  );

  const selectLocation = useCallback(
    (result: GeographySearchResult) => {
      setLocationQuery(result.label);
      setShowLocationResults(false);
      // Use the most specific part for the filter
      const filterValue = result.state_city || result.country || result.continent || result.label;
      onUpdateFilters({ location: filterValue });
    },
    [onUpdateFilters],
  );

  // Director debounce
  const handleDirectorChange = useCallback(
    (value: string) => {
      setDirectorInput(value);
      clearTimeout(directorTimeoutRef.current);
      directorTimeoutRef.current = setTimeout(() => {
        onUpdateFilters({ director: value || "" });
      }, 500);
    },
    [onUpdateFilters],
  );

  // Year range with blur
  const handleYearMinBlur = useCallback(() => {
    const val = yearMinInput ? parseInt(yearMinInput, 10) : null;
    onUpdateFilters({ year_min: val && !isNaN(val) ? val : null });
  }, [yearMinInput, onUpdateFilters]);

  const handleYearMaxBlur = useCallback(() => {
    const val = yearMaxInput ? parseInt(yearMaxInput, 10) : null;
    onUpdateFilters({ year_max: val && !isNaN(val) ? val : null });
  }, [yearMaxInput, onUpdateFilters]);

  // Seen toggle
  const vuValue = filters.vu === null ? "all" : filters.vu ? "seen" : "unseen";

  return (
    <ScrollArea className="h-full">
      <div className="space-y-1 p-4">
        {/* Taxonomy filter sections */}
        {TAXONOMY_DIMENSIONS.map((dim) => {
          const items = taxonomies[dim] || [];
          if (items.length === 0) return null;
          return (
            <FilterSection
              key={dim}
              title={dimensionLabel(dim)}
              dimension={dim}
              items={items}
              activeValues={filters[dim]}
              onToggle={(value) => onToggleFilter(dim, value)}
              defaultExpanded={EXPANDED_BY_DEFAULT.has(dim)}
            />
          );
        })}

        {/* Location autocomplete */}
        <div className="border-b border-border pb-3 pt-2">
          <label className="mb-2 block text-sm font-medium text-foreground">Location</label>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={locationQuery}
              onChange={(e) => handleLocationChange(e.target.value)}
              onBlur={() => setTimeout(() => setShowLocationResults(false), 200)}
              placeholder="Search locations..."
              className="h-8 pl-8 text-xs"
            />
            {showLocationResults && locationResults.length > 0 && (
              <div className="absolute top-full z-50 mt-1 w-full rounded-md border bg-popover shadow-md">
                {locationResults.slice(0, 8).map((r) => (
                  <button
                    key={r.geography_id}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => selectLocation(r)}
                    className="flex w-full items-center justify-between px-3 py-2 text-xs hover:bg-accent hover:text-accent-foreground"
                  >
                    <span className="truncate">{r.label}</span>
                    <span className="ml-2 text-muted-foreground">{r.film_count}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Language dropdown */}
        <div className="border-b border-border pb-3 pt-2">
          <label className="mb-2 block text-sm font-medium text-foreground">Language</label>
          <Select
            value={filters.language || "__all__"}
            onValueChange={(val) =>
              onUpdateFilters({ language: val === "__all__" ? "" : val })
            }
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="All languages" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">All languages</SelectItem>
              {languages
                .filter((l) => (l.film_count ?? 0) > 0)
                .map((lang) => (
                  <SelectItem key={lang.id} value={lang.name}>
                    {lang.name} ({lang.film_count})
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </div>

        {/* Seen toggle */}
        <div className="border-b border-border pb-3 pt-2">
          <label className="mb-2 block text-sm font-medium text-foreground">Seen</label>
          <Select value={vuValue} onValueChange={(val) => {
            if (val === "all") onSetVu(null);
            else if (val === "seen") onSetVu(true);
            else onSetVu(false);
          }}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="seen">Seen only</SelectItem>
              <SelectItem value="unseen">Unseen only</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Year range */}
        <div className="border-b border-border pb-3 pt-2">
          <label className="mb-2 block text-sm font-medium text-foreground">Year Range</label>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              value={yearMinInput}
              onChange={(e) => setYearMinInput(e.target.value)}
              onBlur={handleYearMinBlur}
              onKeyDown={(e) => e.key === "Enter" && handleYearMinBlur()}
              placeholder="From"
              className="h-8 text-xs"
              min={1888}
              max={2030}
            />
            <span className="text-xs text-muted-foreground">—</span>
            <Input
              type="number"
              value={yearMaxInput}
              onChange={(e) => setYearMaxInput(e.target.value)}
              onBlur={handleYearMaxBlur}
              onKeyDown={(e) => e.key === "Enter" && handleYearMaxBlur()}
              placeholder="To"
              className="h-8 text-xs"
              min={1888}
              max={2030}
            />
          </div>
        </div>

        {/* Director filter */}
        <div className="pb-3 pt-2">
          <label className="mb-2 block text-sm font-medium text-foreground">Director</label>
          <Input
            value={directorInput}
            onChange={(e) => handleDirectorChange(e.target.value)}
            placeholder="Search director..."
            className="h-8 text-xs"
          />
        </div>
      </div>
    </ScrollArea>
  );
}
