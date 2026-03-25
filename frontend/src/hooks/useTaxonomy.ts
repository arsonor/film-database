import { useEffect, useState } from "react";
import { fetchTaxonomy } from "@/api/client";
import { TAXONOMY_DIMENSIONS, type TaxonomyItem } from "@/types/api";

// Extra dimensions to fetch that aren't chip-based (used as dropdowns)
const EXTRA_DIMENSIONS = ["studios"] as const;

export function useTaxonomy() {
  const [taxonomies, setTaxonomies] = useState<Record<string, TaxonomyItem[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadAll() {
      try {
        const allDimensions = [...TAXONOMY_DIMENSIONS, ...EXTRA_DIMENSIONS];
        const results = await Promise.all(
          allDimensions.map((dim) => fetchTaxonomy(dim)),
        );
        if (!cancelled) {
          const map: Record<string, TaxonomyItem[]> = {};
          for (const result of results) {
            map[result.dimension] = result.items;
          }
          setTaxonomies(map);
          setLoading(false);
        }
      } catch {
        // Taxonomy fetch failure is non-critical; sidebar will be empty
        if (!cancelled) setLoading(false);
      }
    }

    loadAll();
    return () => {
      cancelled = true;
    };
  }, []);

  return { taxonomies, loading };
}
