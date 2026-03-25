import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatYear(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).getFullYear().toString();
}

export function formatDuration(minutes: number | null): string {
  if (!minutes) return "—";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h${m > 0 ? ` ${m}min` : ""}` : `${m}min`;
}

export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function dimensionLabel(dimension: string): string {
  const labels: Record<string, string> = {
    categories: "Categories",
    themes: "Themes",
    atmospheres: "Atmospheres",
    characters: "Character Types",
    character_contexts: "Character Contexts",
    motivations: "Motivations",
    messages: "Messages",
    cinema_types: "Cinema Types",
    cultural_movements: "Cultural Movements",
    time_periods: "Time Periods",
    place_contexts: "Place Contexts",
    studios: "Studios",
  };
  return labels[dimension] ?? capitalize(dimension.replace(/_/g, " "));
}
