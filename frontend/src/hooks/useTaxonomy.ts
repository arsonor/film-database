import { useEffect, useState } from "react";
import { fetchTaxonomy } from "@/api/client";
import { TAXONOMY_DIMENSIONS, type TaxonomyItem } from "@/types/api";

export function useTaxonomy() {
  const [taxonomies, setTaxonomies] = useState<Record<string, TaxonomyItem[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadAll() {
      try {
        const results = await Promise.all(
          TAXONOMY_DIMENSIONS.map((dim) => fetchTaxonomy(dim)),
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
