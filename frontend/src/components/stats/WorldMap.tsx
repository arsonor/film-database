import { useEffect, useMemo, useState } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from "react-simple-maps";
import {
  FILM_COUNT_BUCKETS,
  NO_DATA_COLOR,
  bucketColor,
} from "@/lib/colorScale";
import { ISO_NUM_TO_ALPHA2 } from "@/lib/isoNumToAlpha2";

interface WorldMapDatum {
  iso: string;
  country: string;
  film_count: number;
}

interface WorldMapProps {
  data: WorldMapDatum[];
  onCountryClick: (iso: string, country: string) => void;
  selectedIso?: string | null;
}

// Countries our data covers but the 110m basemap doesn't render as a
// distinct clickable polygon (city-states, micro-states, small islands,
// special administrative regions). Exposed as chips below the map so the
// user can still get to them.
const SMALL_TERRITORIES: ReadonlySet<string> = new Set([
  "HK", "MO", "SG", "MT", "LU", "LI", "AD", "MC", "SM",
  "BH", "BB", "BS", "TT", "JM", "MU", "FJ", "CY", "PR",
]);

const TOPOJSON_URL = "/world-110m.json";

export function WorldMap({ data, onCountryClick, selectedIso }: WorldMapProps) {
  const [hover, setHover] = useState<{
    x: number;
    y: number;
    label: string;
  } | null>(null);

  const { countByIso, nameByIso } = useMemo(() => {
    const cByI = new Map<string, number>();
    const nByI = new Map<string, string>();
    for (const d of data) {
      cByI.set(d.iso, d.film_count);
      nByI.set(d.iso, d.country);
    }
    return { countByIso: cByI, nameByIso: nByI };
  }, [data]);

  const territoryChips = useMemo(
    () =>
      data
        .filter((d) => SMALL_TERRITORIES.has(d.iso) && d.film_count > 0)
        .sort((a, b) => b.film_count - a.film_count),
    [data],
  );

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="mb-2 text-[10px] uppercase tracking-wide text-muted-foreground">
        Ctrl + scroll to zoom · drag to pan
      </p>
      <div className="relative overflow-hidden">
        <ComposableMap
          projection="geoEqualEarth"
          projectionConfig={{ scale: 160 }}
          width={900}
          height={420}
          style={{ width: "100%", height: "auto", background: "#0f0f0f" }}
        >
          <ZoomableGroup zoom={1} center={[0, 20]} minZoom={1} maxZoom={4}>
            <Geographies geography={TOPOJSON_URL}>
              {({ geographies }: { geographies: WAGeography[] }) =>
                geographies.map((geo) => {
                  const isoNum = String(geo.id);
                  const alpha2 = ISO_NUM_TO_ALPHA2[isoNum];
                  const count = alpha2 ? countByIso.get(alpha2) ?? 0 : 0;
                  const fill = bucketColor(count);
                  const isSelected = !!alpha2 && alpha2 === selectedIso;
                  const countryName =
                    (alpha2 && nameByIso.get(alpha2)) ||
                    geo.properties?.name ||
                    "";

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={fill}
                      stroke="#334155"
                      strokeWidth={isSelected ? 1.5 : 0.4}
                      style={{
                        default: {
                          outline: "none",
                          stroke: isSelected ? "#f59e0b" : "#334155",
                          strokeWidth: isSelected ? 1.5 : 0.4,
                        },
                        hover: {
                          outline: "none",
                          stroke: "#f59e0b",
                          strokeWidth: 1,
                          cursor: alpha2 && count > 0 ? "pointer" : "default",
                        },
                        pressed: { outline: "none" },
                      }}
                      onMouseEnter={(e: React.MouseEvent) => {
                        if (!alpha2) return;
                        setHover({
                          x: e.clientX,
                          y: e.clientY,
                          label: `${countryName} — ${count.toLocaleString()} ${
                            count === 1 ? "film" : "films"
                          }`,
                        });
                      }}
                      onMouseMove={(e: React.MouseEvent) =>
                        setHover((h) =>
                          h ? { ...h, x: e.clientX, y: e.clientY } : h,
                        )
                      }
                      onMouseLeave={() => setHover(null)}
                      onClick={() => {
                        if (alpha2 && count > 0) {
                          onCountryClick(alpha2, countryName);
                        }
                      }}
                    />
                  );
                })
              }
            </Geographies>
          </ZoomableGroup>
        </ComposableMap>

        {hover && (
          <FloatingTooltip x={hover.x} y={hover.y} text={hover.label} />
        )}
      </div>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground">
        <span>Film count:</span>
        {FILM_COUNT_BUCKETS.map((b) => (
          <div key={b.label} className="flex items-center gap-1">
            <span
              className="inline-block h-3 w-4 rounded-sm border border-border"
              style={{ background: b.color }}
            />
            <span>{b.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1">
          <span
            className="inline-block h-3 w-4 rounded-sm border border-border"
            style={{ background: NO_DATA_COLOR }}
          />
          <span>no data</span>
        </div>
      </div>

      {/* Small-territory chips — for countries the 110m basemap can't render
          as clickable polygons (Hong Kong, Singapore, Luxembourg, etc.). */}
      {territoryChips.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Also:
          </span>
          {territoryChips.map((t) => {
            const isSelected = t.iso === selectedIso;
            return (
              <button
                key={t.iso}
                type="button"
                onClick={() => onCountryClick(t.iso, t.country)}
                className={`rounded-full border px-2 py-0.5 text-[11px] transition-colors ${
                  isSelected
                    ? "border-amber-500 bg-amber-500/20 text-amber-500"
                    : "border-border bg-background text-foreground hover:border-amber-500/60 hover:bg-amber-500/10"
                }`}
                title={`${t.country} — ${t.film_count.toLocaleString()} films`}
              >
                <span
                  className="mr-1.5 inline-block h-2 w-2 rounded-sm align-middle"
                  style={{ background: bucketColor(t.film_count) }}
                />
                {t.country}{" "}
                <span className="text-muted-foreground">
                  ({t.film_count.toLocaleString()})
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function FloatingTooltip({
  x,
  y,
  text,
}: {
  x: number;
  y: number;
  text: string;
}) {
  const [pos, setPos] = useState({ x, y });
  useEffect(() => {
    setPos({ x, y });
  }, [x, y]);
  return (
    <div
      className="pointer-events-none fixed z-50 rounded border border-border bg-[#1f1f1f] px-2 py-1 text-[11px] text-foreground shadow-lg"
      style={{ left: pos.x + 12, top: pos.y + 12 }}
    >
      {text}
    </div>
  );
}

interface WAGeography {
  rsmKey: string;
  id?: string | number;
  properties?: { name?: string };
}
