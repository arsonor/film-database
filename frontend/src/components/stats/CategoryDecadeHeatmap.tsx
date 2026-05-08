import { useMemo, useState } from "react";

interface Cell {
  category: string;
  decade: number;
  count: number;
}

interface CategoryDecadeHeatmapProps {
  data: Cell[];
}

const CELL = 40;
const ROW_LABEL_W = 110;
const COL_LABEL_H = 60;

export function CategoryDecadeHeatmap({ data }: CategoryDecadeHeatmapProps) {
  const [hover, setHover] = useState<{
    x: number;
    y: number;
    cell: Cell;
  } | null>(null);

  const { categories, decades, lookup, maxCount } = useMemo(() => {
    const catSet = new Set<string>();
    const decSet = new Set<number>();
    const lk = new Map<string, number>();
    let mx = 0;
    for (const d of data) {
      catSet.add(d.category);
      decSet.add(d.decade);
      lk.set(`${d.category}|${d.decade}`, d.count);
      if (d.count > mx) mx = d.count;
    }
    return {
      categories: Array.from(catSet).sort(),
      decades: Array.from(decSet).sort((a, b) => a - b),
      lookup: lk,
      maxCount: mx,
    };
  }, [data]);

  const width = ROW_LABEL_W + decades.length * CELL + 10;
  const height = COL_LABEL_H + categories.length * CELL + 10;

  return (
    <div className="relative overflow-x-auto">
      <svg width={width} height={height} className="text-foreground">
        {categories.map((cat, ri) => (
          <text
            key={cat}
            x={ROW_LABEL_W - 6}
            y={COL_LABEL_H + ri * CELL + CELL / 2 + 4}
            textAnchor="end"
            className="fill-muted-foreground text-[11px]"
          >
            {cat}
          </text>
        ))}

        {decades.map((dec, ci) => {
          const x = ROW_LABEL_W + ci * CELL + CELL / 2;
          const y = COL_LABEL_H - 6;
          return (
            <text
              key={dec}
              x={x}
              y={y}
              textAnchor="end"
              transform={`rotate(-45, ${x}, ${y})`}
              className="fill-muted-foreground text-[10px]"
            >
              {dec}s
            </text>
          );
        })}

        {categories.map((cat, ri) =>
          decades.map((dec, ci) => {
            const count = lookup.get(`${cat}|${dec}`) ?? 0;
            const opacity =
              count === 0 ? 0.05 : 0.15 + (count / maxCount) * 0.85;
            const x = ROW_LABEL_W + ci * CELL;
            const y = COL_LABEL_H + ri * CELL;
            return (
              <g key={`${cat}-${dec}`}>
                <rect
                  x={x + 1}
                  y={y + 1}
                  width={CELL - 2}
                  height={CELL - 2}
                  fill="#f59e0b"
                  fillOpacity={opacity}
                  rx={3}
                  onMouseEnter={() =>
                    setHover({
                      x: x + CELL / 2,
                      y,
                      cell: { category: cat, decade: dec, count },
                    })
                  }
                  onMouseLeave={() => setHover(null)}
                  className="cursor-pointer"
                />
                {count > 0 && (
                  <text
                    x={x + CELL / 2}
                    y={y + CELL / 2 + 4}
                    textAnchor="middle"
                    className="pointer-events-none fill-foreground text-[10px] font-medium"
                  >
                    {count}
                  </text>
                )}
              </g>
            );
          }),
        )}
      </svg>

      {hover && (
        <div
          className="pointer-events-none absolute z-10 rounded border border-border bg-[#1f1f1f] px-2 py-1 text-[11px] text-foreground shadow-lg"
          style={{
            left: hover.x + 10,
            top: hover.y - 30,
          }}
        >
          {hover.cell.category} · {hover.cell.decade}s · {hover.cell.count} films
        </div>
      )}
    </div>
  );
}
