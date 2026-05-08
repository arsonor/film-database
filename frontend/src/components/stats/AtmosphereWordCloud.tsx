import { useMemo } from "react";

interface AtmosphereWordCloudProps {
  data: { name: string; count: number }[];
}

const COLORS = [
  "text-amber-400",
  "text-amber-300",
  "text-slate-300",
  "text-zinc-200",
  "text-amber-200",
  "text-slate-400",
];

const MIN_REM = 0.75;
const MAX_REM = 2.5;

export function AtmosphereWordCloud({ data }: AtmosphereWordCloudProps) {
  const items = useMemo(() => {
    if (data.length === 0) return [];
    const counts = data.map((d) => d.count);
    const min = Math.min(...counts);
    const max = Math.max(...counts);
    const span = max - min || 1;
    const shuffled = [...data].sort(() => Math.random() - 0.5);
    return shuffled.map((d, i) => {
      const norm = (d.count - min) / span;
      const size = MIN_REM + norm * (MAX_REM - MIN_REM);
      return {
        name: d.name,
        count: d.count,
        size,
        color: COLORS[i % COLORS.length],
      };
    });
  }, [data]);

  return (
    <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 rounded-lg border border-border bg-card p-6">
      {items.map((it) => (
        <span
          key={it.name}
          className={`font-medium ${it.color}`}
          style={{ fontSize: `${it.size}rem`, lineHeight: 1.1 }}
          title={`${it.name} — ${it.count} films`}
        >
          {it.name}
        </span>
      ))}
    </div>
  );
}
