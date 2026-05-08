import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { FinancialsPayload } from "@/types/api";
import { Section } from "./Section";
import { PosterRow } from "./PosterRow";
import {
  CHART_AXIS,
  CHART_GRID,
  CHART_PRIMARY,
  TOOLTIP_ITEM_STYLE,
  TOOLTIP_LABEL_STYLE,
  TOOLTIP_STYLE,
  formatMillions,
} from "./chartTheme";

interface Props {
  data: FinancialsPayload;
}

export function FinancialsTab({ data }: Props) {
  const navigate = useNavigate();
  const lineData = data.avg_budget_by_decade.map((d) => ({
    decade: `${d.decade}s`,
    avg: d.avg_budget,
    avgM: d.avg_budget / 1_000_000,
    film_count: d.film_count,
  }));

  const GENRE_COLORS: Record<string, string> = {
    Drama: "#f59e0b",
    Comedy: "#fbbf24",
    Action: "#ef4444",
    Adventure: "#f97316",
    Thriller: "#a855f7",
    Romance: "#ec4899",
    Horror: "#6b7280",
    "Science-Fiction": "#22d3ee",
    Fantasy: "#8b5cf6",
    Musical: "#10b981",
    Disaster: "#dc2626",
    Historical: "#92400e",
  };
  const FALLBACK_COLOR = "#64748b";

  const scatterByGenre = useMemo(() => {
    const groups = new Map<
      string,
      { x: number; y: number; title: string; film_id: number }[]
    >();
    for (const d of data.budget_revenue_scatter) {
      const cat = d.category || "Other";
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push({
        x: d.budget,
        y: d.revenue,
        title: d.title,
        film_id: d.film_id,
      });
    }
    return Array.from(groups.entries())
      .map(([cat, points]) => ({
        category: cat,
        color: GENRE_COLORS[cat] ?? FALLBACK_COLOR,
        points,
      }))
      .sort((a, b) => b.points.length - a.points.length);
  }, [data.budget_revenue_scatter]);

  const allPoints = data.budget_revenue_scatter;
  const minVal = allPoints.length
    ? Math.min(...allPoints.map((d) => Math.min(d.budget, d.revenue)))
    : 1000;
  const maxVal = allPoints.length
    ? Math.max(...allPoints.map((d) => Math.max(d.budget, d.revenue)))
    : 1_000_000_000;
  const xMin = Math.max(minVal, 1000);
  const xMax = maxVal;
  // Diagonal y = 2x — sample points across the log range so the line renders
  const breakEvenLine = useMemo(() => {
    const pts: { x: number; y: number }[] = [];
    const logMin = Math.log10(xMin);
    const logMax = Math.log10(xMax);
    const steps = 20;
    for (let i = 0; i <= steps; i++) {
      const x = Math.pow(10, logMin + (i * (logMax - logMin)) / steps);
      pts.push({ x, y: x * 2 });
    }
    return pts;
  }, [xMin, xMax]);

  return (
    <div>
      <p className="mb-4 text-xs italic text-muted-foreground">
        Based on {data.budget_revenue_scatter.length} films with available financial data — not adjusted for inflation.
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Top 20 highest-grossing">
          <PosterRow
            items={data.top_grossing.map((f) => ({
              film_id: f.film_id,
              title: f.title,
              poster_url: f.poster_url,
              year: f.year,
              caption: formatMillions(f.revenue),
            }))}
          />
        </Section>

        <Section title="Top 20 biggest budgets">
          <PosterRow
            items={data.top_budgets.map((f) => ({
              film_id: f.film_id,
              title: f.title,
              poster_url: f.poster_url,
              year: f.year,
              caption: formatMillions(f.budget),
            }))}
          />
        </Section>
      </div>

      <Section
        title="Most profitable"
        subtitle="Revenue ÷ budget ratio (films with budget > $1M)"
      >
        <PosterRow
          items={data.most_profitable.map((f) => ({
            film_id: f.film_id,
            title: f.title,
            poster_url: f.poster_url,
            year: f.year,
            caption: `×${f.ratio.toFixed(1)}`,
          }))}
        />
      </Section>

      <Section title="Average budget by decade">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={lineData}>
              <CartesianGrid stroke={CHART_GRID} vertical={false} />
              <XAxis dataKey="decade" stroke={CHART_AXIS} fontSize={11} />
              <YAxis
                stroke={CHART_AXIS}
                fontSize={11}
                tickFormatter={(v) => `$${v.toFixed(0)}M`}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
                formatter={(_v, _n, p) => {
                  const pl = (p as { payload?: { avg: number; film_count: number } })?.payload;
                  if (!pl) return ["", "Avg budget"];
                  return [
                    `${formatMillions(pl.avg)} (${pl.film_count} films)`,
                    "Avg budget",
                  ];
                }}
              />
              <Line
                type="monotone"
                dataKey="avgM"
                stroke={CHART_PRIMARY}
                strokeWidth={2}
                dot={{ fill: CHART_PRIMARY, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section
        title="Budget vs Revenue"
        subtitle={
          "Each dot is a film, colored by genre — horizontal axis = production budget, vertical axis = worldwide box office. " +
          "The dashed line marks the rough profitability threshold: studios usually need a film to earn about 2× its production budget at the box office to break even, " +
          "because cinemas keep roughly half of ticket sales and there's also marketing to recoup. Films above the line generally turned a profit; films below the line lost money. " +
          "Hover any dot to see the film's title alongside its budget and revenue; click the dot to open the film."
        }
      >
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={460}>
            <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
              <CartesianGrid stroke={CHART_GRID} />
              <XAxis
                type="number"
                dataKey="x"
                name="Budget"
                scale="log"
                domain={[xMin, xMax]}
                stroke={CHART_AXIS}
                fontSize={11}
                tickFormatter={formatMillions}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Revenue"
                scale="log"
                domain={[xMin, xMax]}
                stroke={CHART_AXIS}
                fontSize={11}
                tickFormatter={formatMillions}
              />
              <ZAxis range={[40, 40]} />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                content={(props: unknown) => {
                  const p = props as {
                    active?: boolean;
                    payload?: {
                      payload?: {
                        title?: string;
                        x?: number;
                        y?: number;
                      };
                      name?: string;
                    }[];
                  };
                  if (!p.active || !p.payload?.length) return null;
                  const datum = p.payload[0]?.payload;
                  const genre = p.payload[0]?.name;
                  if (!datum) return null;
                  return (
                    <div
                      style={{
                        ...TOOLTIP_STYLE,
                        padding: "8px 10px",
                        maxWidth: 260,
                      }}
                    >
                      <div
                        style={{
                          ...TOOLTIP_LABEL_STYLE,
                          fontWeight: 600,
                          color: "#e5e5e5",
                          marginBottom: 4,
                        }}
                      >
                        {datum.title}
                      </div>
                      {genre && (
                        <div
                          style={{
                            fontSize: 10,
                            color: "#94a3b8",
                            marginBottom: 4,
                          }}
                        >
                          {genre}
                        </div>
                      )}
                      <div style={TOOLTIP_ITEM_STYLE}>
                        Budget:{" "}
                        <span style={{ color: "#fbbf24" }}>
                          {formatMillions(datum.x ?? 0)}
                        </span>
                      </div>
                      <div style={TOOLTIP_ITEM_STYLE}>
                        Revenue:{" "}
                        <span style={{ color: "#fbbf24" }}>
                          {formatMillions(datum.y ?? 0)}
                        </span>
                      </div>
                    </div>
                  );
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {scatterByGenre.map((g) => (
                <Scatter
                  key={g.category}
                  name={g.category}
                  data={g.points}
                  fill={g.color}
                  fillOpacity={0.75}
                  cursor="pointer"
                  onClick={(p: unknown) => {
                    const fid = (p as { film_id?: number } | undefined)?.film_id;
                    if (fid) navigate(`/films/${fid}`);
                  }}
                />
              ))}
              <Scatter
                name="Break-even (2× budget)"
                data={breakEvenLine}
                line={{ stroke: "#94a3b8", strokeDasharray: "4 4", strokeWidth: 1.5 }}
                shape={() => <g />}
                legendType="line"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Section>
    </div>
  );
}
