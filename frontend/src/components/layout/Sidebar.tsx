import { useCallback, useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { DualRangeSlider } from "@/components/ui/dual-range-slider";
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
  onExcludeFilter: (dimension: ArrayFilterKey, value: string) => void;
  onSetFilterMode: (dimension: ArrayFilterKey, mode: "or" | "and") => void;
  onUpdateFilters: (updates: Partial<FilterState>) => void;
  onSetVu: (vu: boolean | null) => void;
  isAdmin?: boolean;
}

// Which dimensions start expanded
const EXPANDED_BY_DEFAULT = new Set<string>();

const YEAR_MIN = 1900;
const YEAR_MAX = 2030;

export function SidebarContent({
  filters,
  taxonomies,
  languages,
  onToggleFilter,
  onExcludeFilter,
  onSetFilterMode,
  onUpdateFilters,
  onSetVu,
  isAdmin,
}: SidebarProps) {
  // Location autocomplete state
  const [locationQuery, setLocationQuery] = useState(filters.location);
  const [locationResults, setLocationResults] = useState<GeographySearchResult[]>([]);
  const [showLocationResults, setShowLocationResults] = useState(false);
  const locationTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Year range slider local state
  const [yearRange, setYearRange] = useState<[number, number]>([
    filters.year_min ?? YEAR_MIN,
    filters.year_max ?? YEAR_MAX,
  ]);

  // Sync external filter changes to local inputs
  useEffect(() => {
    setLocationQuery(filters.location);
  }, [filters.location]);

  useEffect(() => {
    setYearRange([filters.year_min ?? YEAR_MIN, filters.year_max ?? YEAR_MAX]);
  }, [filters.year_min, filters.year_max]);

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
      const filterValue = result.state_city || result.country || result.continent || result.label;
      onUpdateFilters({ location: filterValue });
    },
    [onUpdateFilters],
  );

  // Year range slider commit
  const handleYearAfterChange = useCallback(
    (value: [number, number]) => {
      const yearMin = value[0] <= YEAR_MIN ? null : value[0];
      const yearMax = value[1] >= YEAR_MAX ? null : value[1];
      onUpdateFilters({ year_min: yearMin, year_max: yearMax });
    },
    [onUpdateFilters],
  );

  // Studios data + search
  const studioItems = taxonomies["studios"] || [];
  const [studioQuery, setStudioQuery] = useState("");
  const [showStudioResults, setShowStudioResults] = useState(false);

  const filteredStudios = studioItems
    .filter(
      (s) =>
        (s.film_count ?? 0) > 0 &&
        s.name.toLowerCase().includes(studioQuery.toLowerCase()),
    );

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
              tagFilter={filters[dim]}
              onToggle={(value) => onToggleFilter(dim, value)}
              onExclude={(value) => onExcludeFilter(dim, value)}
              onSetMode={(mode) => onSetFilterMode(dim, mode)}
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

        {/* Studios search */}
        <div className="border-b border-border pb-3 pt-2">
          <label className="mb-2 block text-sm font-medium text-foreground">Studio</label>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={filters.studios.include.length === 1 && !studioQuery ? filters.studios.include[0]! : studioQuery}
              onChange={(e) => {
                setStudioQuery(e.target.value);
                setShowStudioResults(true);
                if (!e.target.value) onUpdateFilters({ studios: { include: [], exclude: [], mode: "or" } });
              }}
              onFocus={() => setShowStudioResults(true)}
              onBlur={() => setTimeout(() => setShowStudioResults(false), 200)}
              placeholder="Search studios..."
              className="h-8 pl-8 text-xs"
            />
            {showStudioResults && filteredStudios.length > 0 && (
              <div className="absolute top-full z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-md border bg-popover shadow-md">
                {filters.studios.include.length > 0 && (
                  <button
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      onUpdateFilters({ studios: { include: [], exclude: [], mode: "or" } });
                      setStudioQuery("");
                      setShowStudioResults(false);
                    }}
                    className="flex w-full items-center px-3 py-2 text-xs italic text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  >
                    Clear selection
                  </button>
                )}
                {filteredStudios.map((studio) => (
                  <button
                    key={studio.id}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      onUpdateFilters({ studios: { include: [studio.name], exclude: [], mode: "or" } });
                      setStudioQuery("");
                      setShowStudioResults(false);
                    }}
                    className="flex w-full items-center justify-between px-3 py-2 text-xs hover:bg-accent hover:text-accent-foreground"
                  >
                    <span className="truncate">{studio.name}</span>
                    <span className="ml-2 text-muted-foreground">{studio.film_count}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Seen toggle (admin only) */}
        {isAdmin && (
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
        )}

        {/* Year range dual slider + inputs */}
        <div className="pb-3 pt-2">
          <label className="mb-2 block text-sm font-medium text-foreground">Year Range</label>
          <div className="px-1">
            <div className="mb-2 flex items-center gap-2 text-xs">
              <Input
                type="number"
                min={YEAR_MIN}
                max={yearRange[1]}
                value={yearRange[0] <= YEAR_MIN ? "" : yearRange[0]}
                placeholder="Min"
                onChange={(e) => {
                  const v = e.target.value ? parseInt(e.target.value, 10) : YEAR_MIN;
                  const clamped = Math.max(YEAR_MIN, Math.min(v, yearRange[1]));
                  setYearRange([clamped, yearRange[1]]);
                }}
                onBlur={() => handleYearAfterChange(yearRange)}
                onKeyDown={(e) => { if (e.key === "Enter") handleYearAfterChange(yearRange); }}
                className="h-7 w-20 text-center text-xs"
              />
              <span className="text-muted-foreground">—</span>
              <Input
                type="number"
                min={yearRange[0]}
                max={YEAR_MAX}
                value={yearRange[1] >= YEAR_MAX ? "" : yearRange[1]}
                placeholder="Max"
                onChange={(e) => {
                  const v = e.target.value ? parseInt(e.target.value, 10) : YEAR_MAX;
                  const clamped = Math.min(YEAR_MAX, Math.max(v, yearRange[0]));
                  setYearRange([yearRange[0], clamped]);
                }}
                onBlur={() => handleYearAfterChange(yearRange)}
                onKeyDown={(e) => { if (e.key === "Enter") handleYearAfterChange(yearRange); }}
                className="h-7 w-20 text-center text-xs"
              />
            </div>
            <DualRangeSlider
              min={YEAR_MIN}
              max={YEAR_MAX}
              value={yearRange}
              onChange={setYearRange}
              onAfterChange={handleYearAfterChange}
            />
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
