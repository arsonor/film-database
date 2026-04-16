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

export function formatPersonName(firstname: string | null, lastname: string): string {
  return firstname ? `${firstname} ${lastname}` : lastname;
}

export function formatCurrency(amount: number | null): string {
  if (!amount) return "—";
  if (amount >= 1_000_000_000) return `$${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
  return `$${amount.toLocaleString()}`;
}

export function tmdbImageUrl(path: string | null, size = "w500"): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

export function dimensionLabel(dimension: string): string {
  const labels: Record<string, string> = {
    categories: "Genres",
    themes: "Themes",
    atmospheres: "Atmospheres",
    characters: "Characters",
    motivations: "Motivations",
    messages: "Messages",
    cinema_types: "Cinema Types",
    time_periods: "Time Periods",
    place_contexts: "Place Contexts",
    studios: "Studios",
  };
  return labels[dimension] ?? capitalize(dimension.replace(/_/g, " "));
}
