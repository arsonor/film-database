import { useCallback, useEffect, useRef, useState } from "react";
import { Lock, Search } from "lucide-react";
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
import { useTierAccess } from "@/lib/tierAccess";
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
  isAdmin,
}: SidebarProps) {
  const tierAccess = useTierAccess(filters);

  // Tier message banner
  const [tierMessage, setTierMessage] = useState<string | null>(null);
  useEffect(() => {
    if (!tierMessage) return;
    const t = setTimeout(() => setTierMessage(null), 3000);
    return () => clearTimeout(t);
  }, [tierMessage]);

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

  const locationLocked = !tierAccess.isDropdownAllowed("location");
  const sourceLocked = !tierAccess.isDropdownAllowed("source");
  const studiosLocked = !tierAccess.isDropdownAllowed("studios");

  const handleLockedClick = useCallback(() => {
    setTierMessage(
      tierAccess.tierName === "anonymous"
        ? "Create an account to unlock more filters"
        : "Upgrade to Pro to unlock all filters"
    );
  }, [tierAccess.tierName]);

  const handleLimitReached = useCallback(() => {
    setTierMessage(
      `Filter limit reached (${tierAccess.currentFilterCount}/${tierAccess.maxFilters}) — ${
        tierAccess.tierName === "anonymous" ? "sign in for more" : "upgrade to Pro"
      }`
    );
  }, [tierAccess.currentFilterCount, tierAccess.maxFilters, tierAccess.tierName]);

  // Check if adding a new dropdown filter would exceed the limit
  const checkFilterLimit = useCallback((): boolean => {
    if (tierAccess.canAddFilter) return false;
    handleLimitReached();
    return true;
  }, [tierAccess.canAddFilter, handleLimitReached]);

  const selectLocation = useCallback(
    (result: GeographySearchResult) => {
      setLocationQuery(result.label);
      setShowLocationResults(false);
      if (!filters.location && checkFilterLimit()) return;
      const filterValue = result.state_city || result.country || result.continent || result.label;
      onUpdateFilters({ location: filterValue });
    },
    [filters.location, checkFilterLimit, onUpdateFilters],
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

  return (
    <ScrollArea className="h-full">
      <div className="space-y-1 p-4">
        {/* Tier message banner */}
        {tierMessage && (
          <div className="mb-2 rounded-md border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-400">
            {tierMessage}
          </div>
        )}

        {/* Year range dual slider + inputs */}
        <div className="border-b border-border pb-3 pt-2">
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

        {/* Taxonomy filter sections */}
        {TAXONOMY_DIMENSIONS.map((dim) => {
          const items = taxonomies[dim] || [];
          if (items.length === 0) return null;

          const locked = !tierAccess.isDimensionAllowed(dim);
          const lockedTagNames = !locked
            ? new Set(
                items
                  .filter((item) => !tierAccess.isTagAllowed(dim, item.sort_order))
                  .map((item) => item.name)
              )
            : undefined;
          // Don't pass empty set
          const effectiveLockedTags = lockedTagNames && lockedTagNames.size > 0 ? lockedTagNames : undefined;

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
              locked={locked}
              lockedTagNames={effectiveLockedTags}
              canAddFilter={tierAccess.canAddFilter}
              canUseOrNot={tierAccess.canUseOrNot}
              onLockedClick={handleLockedClick}
              onLimitReached={handleLimitReached}
            />
          );
        })}

        {/* Location autocomplete */}
        <div className={`border-b border-border pb-3 pt-2 ${locationLocked ? "opacity-40 pointer-events-none" : ""}`}>
          <label className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
            Location
            {locationLocked && <Lock className="h-3 w-3 text-amber-500/60" />}
          </label>
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
            onValueChange={(val) => {
              const newVal = val === "__all__" ? "" : val;
              if (newVal && !filters.language && checkFilterLimit()) return;
              onUpdateFilters({ language: newVal });
            }}
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

        {/* Source dropdown */}
        <div className={`border-b border-border pb-3 pt-2 ${sourceLocked ? "opacity-40 pointer-events-none" : ""}`}>
          <label className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
            Origin/Adaptation
            {sourceLocked && <Lock className="h-3 w-3 text-amber-500/60" />}
          </label>
          <Select
            value={filters.source || "__all__"}
            onValueChange={(val) => {
              const newVal = val === "__all__" ? "" : val;
              if (newVal && !filters.source && checkFilterLimit()) return;
              onUpdateFilters({ source: newVal });
            }}
          >
            <SelectTrigger className="h-8 text-xs">
              <SelectValue placeholder="All sources" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">All sources</SelectItem>
              <SelectItem value="original screenplay">Original screenplay</SelectItem>
              <SelectItem value="novel">Novel</SelectItem>
              <SelectItem value="comic">Comic</SelectItem>
              <SelectItem value="TV series">TV series</SelectItem>
              <SelectItem value="true story">True story</SelectItem>
              <SelectItem value="play">Play</SelectItem>
              <SelectItem value="video game">Video game</SelectItem>
              <SelectItem value="poem">Poem</SelectItem>
              <SelectItem value="short story">Short story</SelectItem>
              <SelectItem value="remake">Remake</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Studios search */}
        <div className={`border-b border-border pb-3 pt-2 ${studiosLocked ? "opacity-40 pointer-events-none" : ""}`}>
          <label className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
            Studio
            {studiosLocked && <Lock className="h-3 w-3 text-amber-500/60" />}
          </label>
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
                      if (filters.studios.include.length === 0 && checkFilterLimit()) return;
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


      </div>
    </ScrollArea>
  );
}
