import { useQuery } from "@tanstack/react-query";
import { fetchTaxonomy } from "@/api/client";
import { TAXONOMY_DIMENSIONS, type TaxonomyItem } from "@/types/api";

const EXTRA_DIMENSIONS = ["studios"] as const;

async function loadAllTaxonomies(): Promise<Record<string, TaxonomyItem[]>> {
  const allDimensions = [...TAXONOMY_DIMENSIONS, ...EXTRA_DIMENSIONS];
  const results = await Promise.all(
    allDimensions.map((dim) => fetchTaxonomy(dim)),
  );
  const map: Record<string, TaxonomyItem[]> = {};
  for (const result of results) {
    map[result.dimension] = result.items;
  }
  return map;
}

export function useTaxonomy() {
  const { data: taxonomies = {}, isLoading: loading } = useQuery({
    queryKey: ["taxonomy"],
    queryFn: loadAllTaxonomies,
    staleTime: Infinity,
  });

  return { taxonomies, loading };
}
