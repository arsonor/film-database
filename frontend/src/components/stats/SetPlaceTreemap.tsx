import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { ResponsiveContainer, Tooltip, Treemap } from "recharts";
import type { SetPlaceTreemapCell } from "@/types/api";

interface SetPlaceTreemapProps {
  data: SetPlaceTreemapCell[];
}

type Level = "continent" | "country" | "city";

interface ViewNode {
  name: string;
  size: number;        // film count rolled up for this node
  level: Level;
  geography_id?: number;
}

const PALETTE = [
  "#f59e0b", "#d97706", "#b45309", "#92400e",
  "#fbbf24", "#fcd34d", "#78350f", "#fde68a",
];

export function SetPlaceTreemap({ data }: SetPlaceTreemapProps) {
  const navigate = useNavigate();
  const [path, setPath] = useState<string[]>([]);

  // Strip the country-level roll-up rows from the source data and key cities
  // (which are leaves) by their three-part path. Then compute roll-ups for
  // continents and countries on the fly so we can show any level.
  const cityRows = useMemo(
    () =>
      data.filter(
        (r) =>
          r.country !== null &&
          r.state_city !== null &&
          r.continent !== null,
      ),
    [data],
  );

  const visible: ViewNode[] = useMemo(() => {
    if (path.length === 0) {
      // Level 0 — continents.
      const totals = new Map<string, number>();
      for (const row of cityRows) {
        totals.set(row.continent, (totals.get(row.continent) ?? 0) + row.film_count);
      }
      return [...totals.entries()]
        .map(([name, size]) => ({ name, size, level: "continent" as const }))
        .sort((a, b) => b.size - a.size);
    }
    if (path.length === 1) {
      // Level 1 — countries within the picked continent.
      const totals = new Map<string, number>();
      for (const row of cityRows) {
        if (row.continent !== path[0]) continue;
        const k = row.country ?? "—";
        totals.set(k, (totals.get(k) ?? 0) + row.film_count);
      }
      return [...totals.entries()]
        .map(([name, size]) => ({ name, size, level: "country" as const }))
        .sort((a, b) => b.size - a.size);
    }
    // Level 2 — cities within the picked country.
    return cityRows
      .filter((r) => r.continent === path[0] && r.country === path[1])
      .map((r) => ({
        name: r.state_city ?? "—",
        size: r.film_count,
        level: "city" as const,
        geography_id: r.geography_id,
      }))
      .sort((a, b) => b.size - a.size);
  }, [cityRows, path]);

  const handleCellClick = (n: ViewNode) => {
    if (n.level === "continent") {
      setPath([n.name]);
    } else if (n.level === "country" && path[0]) {
      setPath([path[0], n.name]);
    } else if (n.level === "city") {
      navigate(`/browse?location=${encodeURIComponent(n.name)}`);
    }
  };

  if (cityRows.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        No location data available.
      </p>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <Breadcrumbs path={path} onJump={(i) => setPath(path.slice(0, i))} />
      <ResponsiveContainer width="100%" height={500}>
        <Treemap
          data={visible as unknown as object[]}
          dataKey="size"
          nameKey="name"
          stroke="#0f0f0f"
          fill="#f59e0b"
          isAnimationActive={false}
          content={
            ((props: CellProps) => (
              <TreemapCell {...props} onCellClick={handleCellClick} />
            )) as never
          }
        >
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              // Recharts wraps the data once in `payload[0].payload` for
              // Treemap; the actual node fields live there.
              const raw = payload[0] as {
                payload?: ViewNode;
                name?: string;
                size?: number;
                level?: Level;
              };
              const n: ViewNode | null = raw.payload?.level
                ? raw.payload
                : raw.level && raw.name
                  ? { name: raw.name, size: raw.size ?? 0, level: raw.level }
                  : null;
              if (!n) return null;
              const hint =
                n.level === "city"
                  ? "click to browse"
                  : `click to drill into ${n.level === "continent" ? "countries" : "cities"}`;
              return (
                <div className="rounded border border-border bg-[#1f1f1f] px-2 py-1 text-[11px] text-foreground shadow-lg">
                  <div className="font-medium">{n.name}</div>
                  <div className="text-muted-foreground">
                    {n.size.toLocaleString()}{" "}
                    {n.size === 1 ? "film" : "films"} — {hint}
                  </div>
                </div>
              );
            }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}

function Breadcrumbs({
  path,
  onJump,
}: {
  path: string[];
  onJump: (depth: number) => void;
}) {
  return (
    <div className="mb-3 flex flex-wrap items-center gap-1 text-xs">
      <button
        type="button"
        onClick={() => onJump(0)}
        className={`rounded px-2 py-0.5 transition-colors ${
          path.length === 0
            ? "bg-amber-500/20 text-amber-500"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        All continents
      </button>
      {path.map((p, i) => (
        <span key={p} className="flex items-center gap-1">
          <ChevronRight className="h-3 w-3 text-muted-foreground" />
          <button
            type="button"
            onClick={() => onJump(i + 1)}
            className={`rounded px-2 py-0.5 transition-colors ${
              i === path.length - 1
                ? "bg-amber-500/20 text-amber-500"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {p}
          </button>
        </span>
      ))}
    </div>
  );
}

// Recharts Treemap spreads each node's source data directly onto the cell
// renderer's props (rather than nesting it under `payload`). So our `level`,
// `size`, `geography_id` arrive as top-level props — read them from there.
interface CellProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  index?: number;
  depth?: number;
  name?: string;
  size?: number;
  level?: Level;
  geography_id?: number;
  onCellClick?: (n: ViewNode) => void;
}

function TreemapCell(props: CellProps) {
  const {
    x = 0,
    y = 0,
    width = 0,
    height = 0,
    index = 0,
    depth = 0,
    name = "",
    size,
    level,
    geography_id,
    onCellClick,
  } = props;

  // Recharts renders parent nodes at depth=0 (the invisible root wrapper)
  // and depth=1 (the actual leaves we feed it). Skip the root.
  if (depth === 0 || !level || !name) {
    return <g />;
  }

  const fill = PALETTE[index % PALETTE.length];
  const node: ViewNode = { name, size: size ?? 0, level, geography_id };

  return (
    <g style={{ cursor: "pointer" }}>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill,
          stroke: "#0f0f0f",
          strokeWidth: 2,
          pointerEvents: "all",
        }}
        onClick={(e) => {
          e.stopPropagation();
          onCellClick && onCellClick(node);
        }}
      />
      {width > 60 && height > 22 && (
        <text
          x={x + 6}
          y={y + 16}
          fill="#0f0f0f"
          fontSize={12}
          fontWeight={600}
          style={{ pointerEvents: "none" }}
        >
          {name}
        </text>
      )}
      {width > 60 && height > 38 && size !== undefined && (
        <text
          x={x + 6}
          y={y + 32}
          fill="rgba(15, 15, 15, 0.7)"
          fontSize={10}
          style={{ pointerEvents: "none" }}
        >
          {size.toLocaleString()}
        </text>
      )}
    </g>
  );
}
