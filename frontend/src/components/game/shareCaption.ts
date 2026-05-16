import type { GamePoolFilters } from "@/types/api";

export function describeFilters(
  difficulty?: "easy" | "medium" | "hard" | null,
  poolFilters?: GamePoolFilters | null,
): string {
  const parts: string[] = [];
  if (difficulty && difficulty !== "medium") parts.push(`🎚 ${difficulty}`);
  if (poolFilters?.year_min != null && poolFilters?.year_max != null) {
    parts.push(`📅 ${poolFilters.year_min}–${poolFilters.year_max}`);
  } else if (poolFilters?.year_min != null) {
    parts.push(`📅 ≥${poolFilters.year_min}`);
  } else if (poolFilters?.year_max != null) {
    parts.push(`📅 ≤${poolFilters.year_max}`);
  }
  if (poolFilters?.language) parts.push(`🗣 ${poolFilters.language}`);
  return parts.length ? parts.join(" · ") : "";
}

const LAUNCH: Record<"tag_it" | "chain_it" | "guess_it", string> = {
  tag_it: "2026-05-13",
  chain_it: "2026-05-15",
  guess_it: "2026-05-15",
};

export function dailyNumber(gameType: "tag_it" | "chain_it" | "guess_it", isoDate?: string | null): number {
  const today = isoDate ?? new Date().toISOString().slice(0, 10);
  return Math.max(1, Math.floor((Date.parse(today) - Date.parse(LAUNCH[gameType])) / 86_400_000) + 1);
}
