import { useMemo, useState } from "react";

interface CrossTabHeatmapProps<T> {
  data: T[];
  rowKey: (cell: T) => string;
  colKey: (cell: T) => string;
  rowSortOrder?: (cell: T) => number;
  colSortOrder?: (cell: T) => number;
  valueKey: (cell: T) => number;
  cellLabel: (cell: T) => string;
  tooltip: (cell: T) => string;
  rowLabelWidth?: number;
  cellWidth?: number;
  cellHeight?: number;
  colLabelHeight?: number;
}

export function CrossTabHeatmap<T>({
  data,
  rowKey,
  colKey,
  rowSortOrder,
  colSortOrder,
  valueKey,
  cellLabel,
  tooltip,
  rowLabelWidth = 110,
  cellWidth = 50,
  cellHeight = 40,
  colLabelHeight = 120,
}: CrossTabHeatmapProps<T>) {
  const [hover, setHover] = useState<{ x: number; y: number; text: string } | null>(
    null,
  );

  const { rows, cols, lookup, maxValue } = useMemo(() => {
    const rowOrder = new Map<string, number>();
    const colOrder = new Map<string, number>();
    const lk = new Map<string, T>();
    let mx = 0;

    for (const d of data) {
      const r = rowKey(d);
      const c = colKey(d);
      lk.set(`${r}|${c}`, d);
      const v = valueKey(d);
      if (v > mx) mx = v;
      if (!rowOrder.has(r)) {
        rowOrder.set(r, rowSortOrder ? rowSortOrder(d) : Number.NaN);
      }
      if (!colOrder.has(c)) {
        colOrder.set(c, colSortOrder ? colSortOrder(d) : Number.NaN);
      }
    }

    const sortFn = (order: Map<string, number>, hasOrder: boolean) =>
      (a: string, b: string) =>
        hasOrder
          ? (order.get(a)! - order.get(b)!) || a.localeCompare(b)
          : a.localeCompare(b);

    return {
      rows: Array.from(rowOrder.keys()).sort(sortFn(rowOrder, !!rowSortOrder)),
      cols: Array.from(colOrder.keys()).sort(sortFn(colOrder, !!colSortOrder)),
      lookup: lk,
      maxValue: mx,
    };
  }, [data, rowKey, colKey, valueKey, rowSortOrder, colSortOrder]);

  const width = rowLabelWidth + cols.length * cellWidth + 10;
  const height = colLabelHeight + rows.length * cellHeight + 10;

  return (
    <div className="relative overflow-x-auto">
      <svg width={width} height={height} className="text-foreground">
        {rows.map((r, ri) => (
          <text
            key={r}
            x={rowLabelWidth - 6}
            y={colLabelHeight + ri * cellHeight + cellHeight / 2 + 4}
            textAnchor="end"
            className="fill-muted-foreground text-[11px]"
          >
            {r}
          </text>
        ))}

        {cols.map((c, ci) => {
          const x = rowLabelWidth + ci * cellWidth + cellWidth / 2;
          const y = colLabelHeight - 6;
          return (
            <text
              key={c}
              x={x}
              y={y}
              textAnchor="end"
              transform={`rotate(-45, ${x}, ${y})`}
              className="fill-muted-foreground text-[10px]"
            >
              {c}
            </text>
          );
        })}

        {rows.map((r, ri) =>
          cols.map((c, ci) => {
            const cell = lookup.get(`${r}|${c}`);
            const value = cell ? valueKey(cell) : 0;
            const opacity =
              value <= 0 || maxValue <= 0
                ? 0.05
                : Math.min(1, 0.15 + (value / maxValue) * 0.85);
            const x = rowLabelWidth + ci * cellWidth;
            const y = colLabelHeight + ri * cellHeight;
            const label = cell ? cellLabel(cell) : "";

            return (
              <g key={`${r}-${c}`}>
                <rect
                  x={x + 1}
                  y={y + 1}
                  width={cellWidth - 2}
                  height={cellHeight - 2}
                  fill="#f59e0b"
                  fillOpacity={opacity}
                  rx={3}
                  onMouseEnter={() =>
                    cell &&
                    setHover({
                      x: x + cellWidth / 2,
                      y,
                      text: tooltip(cell),
                    })
                  }
                  onMouseLeave={() => setHover(null)}
                  className="cursor-pointer"
                />
                {label && (
                  <text
                    x={x + cellWidth / 2}
                    y={y + cellHeight / 2 + 4}
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
