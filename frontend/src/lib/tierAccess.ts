import { useMemo } from "react";
import { useAuth } from "@/context/AuthContext";
import type { FilterState, ArrayFilterKey } from "@/types/api";
import { ARRAY_FILTER_KEYS } from "@/types/api";

type TierName = "anonymous" | "free" | "pro" | "admin";

interface TierConfig {
  allowedDimensions: Set<ArrayFilterKey>;
  allowedDropdowns: Set<string>;
  dimensionSortOrderMax: Partial<Record<ArrayFilterKey, number>>;
  maxFilters: number | null;
  canUseOrNot: boolean;
}

const TIER_CONFIGS: Record<TierName, TierConfig> = {
  anonymous: {
    allowedDimensions: new Set(["categories", "time_periods", "atmospheres"]),
    allowedDropdowns: new Set(["language", "location"]),
    dimensionSortOrderMax: { atmospheres: 299 },
    maxFilters: 2,
    canUseOrNot: false,
  },
  free: {
    allowedDimensions: new Set([
      "categories", "time_periods", "place_contexts",
      "themes", "atmospheres", "characters",
      "motivations", "cinema_types",
    ]),
    allowedDropdowns: new Set(["language", "location"]),
    dimensionSortOrderMax: {
      themes: 399,
      atmospheres: 299,
      place_contexts: 299,
      characters: 299,
      motivations: 199,
      cinema_types: 199,
    },
    maxFilters: 3,
    canUseOrNot: false,
  },
  pro: {
    allowedDimensions: new Set([
      "categories", "themes", "atmospheres", "characters",
      "motivations", "messages", "cinema_types",
      "time_periods", "place_contexts", "studios",
    ]),
    allowedDropdowns: new Set(["language", "location", "source", "studios"]),
    dimensionSortOrderMax: {},
    maxFilters: null,
    canUseOrNot: true,
  },
  admin: {
    allowedDimensions: new Set([
      "categories", "themes", "atmospheres", "characters",
      "motivations", "messages", "cinema_types",
      "time_periods", "place_contexts", "studios",
    ]),
    allowedDropdowns: new Set(["language", "location", "source", "studios"]),
    dimensionSortOrderMax: {},
    maxFilters: null,
    canUseOrNot: true,
  },
};

export function useTierAccess(filters: FilterState) {
  const { tier, isAuthenticated } = useAuth();

  const tierName: TierName = !isAuthenticated
    ? "anonymous"
    : (tier as TierName) ?? "free";

  const config = TIER_CONFIGS[tierName];

  return useMemo(() => {
    const isDimensionAllowed = (dim: ArrayFilterKey): boolean =>
      config.allowedDimensions.has(dim);

    const isTagAllowed = (dim: ArrayFilterKey, sortOrder: number | null): boolean => {
      if (!isDimensionAllowed(dim)) return false;
      const maxOrder = config.dimensionSortOrderMax[dim];
      if (maxOrder !== undefined) {
        return sortOrder !== null && sortOrder <= maxOrder;
      }
      return true;
    };

    const isDropdownAllowed = (name: string): boolean =>
      config.allowedDropdowns.has(name);

    // Count active filters
    let currentFilterCount = 0;
    for (const key of ARRAY_FILTER_KEYS) {
      currentFilterCount += filters[key].include.length + filters[key].exclude.length;
    }
    if (filters.location) currentFilterCount++;
    if (filters.language) currentFilterCount++;
    if (filters.source) currentFilterCount++;

    const canAddFilter = config.maxFilters === null || currentFilterCount < config.maxFilters;

    return {
      isDimensionAllowed,
      isTagAllowed,
      isDropdownAllowed,
      maxFilters: config.maxFilters,
      currentFilterCount,
      canAddFilter,
      canUseOrNot: config.canUseOrNot,
      tierName,
    };
  }, [config, filters, tierName]);
}
