// Discrete color buckets for the Geography world maps.
//
// We deliberately *don't* use a continuous log scale: counts span 1 to 3000+
// across markets, and continuous interpolation made the visual difference
// between 1 and 1000 films almost imperceptible. Discrete steps match the
// legend exactly and produce clearly distinct colors.

export interface CountBucket {
  min: number;
  label: string;
  color: string;
}

export const FILM_COUNT_BUCKETS: CountBucket[] = [
  { min: 1,    label: "1–4",     color: "hsla(46, 80%, 75%, 0.55)" }, // pale amber
  { min: 5,    label: "5–19",    color: "hsla(40, 85%, 60%, 0.80)" }, // light amber
  { min: 20,   label: "20–99",   color: "hsla(34, 92%, 50%, 0.95)" }, // amber
  { min: 100,  label: "100–499", color: "hsla(26, 95%, 45%, 1.00)" }, // deep amber
  { min: 500,  label: "500+",    color: "hsla(14, 88%, 40%, 1.00)" }, // burnt orange
];

export const NO_DATA_COLOR = "#1f1f1f";

export function bucketFor(count: number): CountBucket | null {
  if (count <= 0) return null;
  let chosen: CountBucket = FILM_COUNT_BUCKETS[0]!;
  for (const b of FILM_COUNT_BUCKETS) {
    if (count >= b.min) chosen = b;
  }
  return chosen;
}

export function bucketColor(count: number): string {
  const b = bucketFor(count);
  return b ? b.color : NO_DATA_COLOR;
}
