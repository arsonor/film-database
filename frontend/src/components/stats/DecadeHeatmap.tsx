import { useMemo, useState } from "react";

interface DecadeHeatmapProps<T> {
  data: T[];
  rowKey: (cell: T) => string;
  decadeKey: (cell: T) => number;
  valueKey: (cell: T) => number;
  cellLabel: (cell: T) => string;
  tooltip: (cell: T) => string;
  /** Optional custom sort key for rows. When omitted, rows are sorted alphabetically. */
  rowSortOrder?: (cell: T) => number;
  /** Row-label column width (default 110). Bump for long row labels like "hollywood golden age". */
  rowLabelWidth?: number;
}

const CELL = 40;
const COL_LABEL_H = 60;

export function DecadeHeatmap<T>({
  data,
  rowKey,
  decadeKey,
  valueKey,
  cellLabel,
  tooltip,
  rowSortOrder,
  rowLabelWidth = 110,
}: DecadeHeatmapProps<T>) {
  const [hover, setHover] = useState<{ x: number; y: number; text: string } | null>(
    null,
  );

  const { rows, decades, lookup, maxValue } = useMemo(() => {
    const rowOrder = new Map<string, number>();
    const decSet = new Set<number>();
    const lk = new Map<string, T>();
    let mx = 0;

    for (const d of data) {
      const r = rowKey(d);
      const dec = decadeKey(d);
      decSet.add(dec);
      lk.set(`${r}|${dec}`, d);
      const v = valueKey(d);
      if (v > mx) mx = v;
      if (!rowOrder.has(r)) {
        rowOrder.set(r, rowSortOrder ? rowSortOrder(d) : Number.NaN);
      }
    }

    const rowList = Array.from(rowOrder.keys());
    if (rowSortOrder) {
      rowList.sort((a, b) => (rowOrder.get(a)! - rowOrder.get(b)!) || a.localeCompare(b));
    } else {
      rowList.sort((a, b) => a.localeCompare(b));
    }

    return {
      rows: rowList,
      decades: Array.from(decSet).sort((a, b) => a - b),
      lookup: lk,
      maxValue: mx,
    };
  }, [data, rowKey, decadeKey, valueKey, rowSortOrder]);

  const width = rowLabelWidth + decades.length * CELL + 10;
  const height = COL_LABEL_H + rows.length * CELL + 10;

  return (
    <div className="relative overflow-x-auto">
      <svg width={width} height={height} className="text-foreground">
        {rows.map((r, ri) => (
          <text
            key={r}
            x={rowLabelWidth - 6}
            y={COL_LABEL_H + ri * CELL + CELL / 2 + 4}
            textAnchor="end"
            className="fill-muted-foreground text-[11px]"
          >
            {r}
          </text>
        ))}

        {decades.map((dec, ci) => {
          const x = rowLabelWidth + ci * CELL + CELL / 2;
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

        {rows.map((r, ri) =>
          decades.map((dec, ci) => {
            const cell = lookup.get(`${r}|${dec}`);
            const value = cell ? valueKey(cell) : 0;
            const opacity =
              value <= 0 || maxValue <= 0
                ? 0.05
                : Math.min(1, 0.15 + (value / maxValue) * 0.85);
            const x = rowLabelWidth + ci * CELL;
            const y = COL_LABEL_H + ri * CELL;
            const label = cell ? cellLabel(cell) : "";

            return (
              <g key={`${r}-${dec}`}>
                <rect
                  x={x + 1}
                  y={y + 1}
                  width={CELL - 2}
                  height={CELL - 2}
                  fill="#f59e0b"
                  fillOpacity={opacity}
                  rx={3}
                  onMouseEnter={() =>
                    cell &&
                    setHover({
                      x: x + CELL / 2,
                      y,
                      text: tooltip(cell),
                    })
                  }
                  onMouseLeave={() => setHover(null)}
                  className="cursor-pointer"
                />
                {label && (
                  <text
                    x={x + CELL / 2}
                    y={y + CELL / 2 + 4}
                    textAnchor="middle"
                    className="pointer-events-none fill-foreground text-[10px] font-medium"
                  >
                    {label}
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
          style={{ left: hover.x + 10, top: hover.y - 30 }}
        >
          {hover.text}
        </div>
      )}
    </div>
  );
}
