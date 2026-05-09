import { useMemo } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PersonalStatsPayload, QuickStatsPayload } from "@/types/api";
import { StatCard } from "./StatCard";
import { Section } from "./Section";
import { PosterRow } from "./PosterRow";
import { tmdbImageUrl } from "@/lib/utils";
import {
  CHART_AXIS,
  CHART_PRIMARY,
  CHART_SECONDARY,
  TOOLTIP_ITEM_STYLE,
  TOOLTIP_LABEL_STYLE,
  TOOLTIP_STYLE,
} from "./chartTheme";

const DURATION_BUCKETS: { key: string; label: string }[] = [
  { key: "<60", label: "<1h" },
  { key: "60-89", label: "1h–1h30" },
  { key: "90-119", label: "1h30–2h" },
  { key: "120-149", label: "2h–2h30" },
  { key: "150-179", label: "2h30–3h" },
  { key: "180+", label: ">3h" },
];

const PIE_COLORS = [
  "#f59e0b", "#d97706", "#fbbf24", "#fcd34d", "#92400e",
  "#64748b", "#475569", "#94a3b8", "#cbd5e1", "#1e293b",
];

interface Props {
  data: QuickStatsPayload;
  personalStats: PersonalStatsPayload | null;
}

export function QuickStatsTab({ data, personalStats }: Props) {
  const hasSeen = !!personalStats?.seen_by_decade?.length;
  const decadeData = useMemo(() => {
    const seenMap = new Map(
      (personalStats?.seen_by_decade ?? []).map((d) => [d.decade, d.count]),
    );
    return data.by_decade.map((d) => {
      const seen = seenMap.get(d.decade) ?? 0;
      return {
        decade: `${d.decade}s`,
        total: d.count,
        seen,
        unseen: Math.max(d.count - seen, 0),
      };
    });
  }, [data.by_decade, personalStats]);

  const durationData = useMemo(() => {
    const map = new Map(data.duration_distribution.map((d) => [d.bucket, d.count]));
    return DURATION_BUCKETS.map((b) => ({
      bucket: b.label,
      count: map.get(b.key) ?? 0,
    }));
  }, [data.duration_distribution]);

  const colorData = data.color_by_decade.map((d) => ({
    decade: `${d.decade}s`,
    color: d.color,
    bw: d.bw,
  }));

  return (
    <div>
      {/* Top row */}
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard value={data.total_films} label="Films" />
        <StatCard value={data.total_directors} label="Directors" />
        <StatCard value={data.total_actors} label="Actors" />
        <StatCard value={data.total_composers} label="Composers" />
      </div>

      {/* Personal stats row */}
      {personalStats && (
        <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard
            value={`${personalStats.seen_pct}%`}
            label="Seen"
            sublabel={`${personalStats.seen_count.toLocaleString()} of ${data.total_films.toLocaleString()}`}
          />
          <StatCard value={personalStats.favorite_count} label="Favorites" />
          <StatCard value={personalStats.watchlist_count} label="Watchlist" />
          <StatCard
            value={personalStats.rated_count}
            label="Rated"
            sublabel={
              personalStats.avg_rating !== null
                ? `Avg ${personalStats.avg_rating.toFixed(1)}/10`
                : undefined
            }
          />
        </div>
      )}

      <Section title="Films by decade">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={decadeData}>
              <XAxis dataKey="decade" stroke={CHART_AXIS} fontSize={11} />
              <YAxis stroke={CHART_AXIS} fontSize={11} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
                cursor={{ fill: "rgba(245,158,11,0.08)" }}
              />
              {hasSeen ? (
                <>
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="seen" stackId="a" fill={CHART_PRIMARY} name="Seen" />
                  <Bar dataKey="unseen" stackId="a" fill={CHART_SECONDARY} name="Unseen" />
                </>
              ) : (
                <Bar dataKey="total" fill={CHART_PRIMARY} name="Films" />
              )}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="Duration distribution">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={durationData}>
              <XAxis dataKey="bucket" stroke={CHART_AXIS} fontSize={11} />
              <YAxis stroke={CHART_AXIS} fontSize={11} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
                cursor={{ fill: "rgba(245,158,11,0.08)" }}
              />
              <Bar dataKey="count" fill={CHART_PRIMARY} name="Films" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="Color vs Black & White over time">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={colorData}>
              <XAxis dataKey="decade" stroke={CHART_AXIS} fontSize={11} />
              <YAxis stroke={CHART_AXIS} fontSize={11} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
                cursor={{ fill: "rgba(245,158,11,0.08)" }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="color" stackId="a" fill={CHART_PRIMARY} name="Color" />
              <Bar dataKey="bw" stackId="a" fill={CHART_SECONDARY} name="B&W" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="Most awarded films">
        <PosterRow
          items={data.most_awarded_films.map((f) => ({
            film_id: f.film_id,
            title: f.title,
            poster_url: f.poster_url,
            year: f.year,
            caption: `${f.wins}× won · ${f.nominations}× nom.`,
          }))}
        />
      </Section>

      <Section
        title="Top 20 franchises"
        subtitle="Most-represented TMDB collections in the database"
      >
        {data.top_franchises.length === 0 ? (
          <p className="text-xs text-muted-foreground">No franchise data yet.</p>
        ) : (
          <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-2">
            {data.top_franchises.map((fr, idx) => {
              const poster = tmdbImageUrl(fr.poster_path, "w500");
              const cleanName = fr.name.replace(/\s*Collection\s*$/i, "");
              const href =
                `/browse?tmdb_collection_id=${fr.collection_id}` +
                `&tmdb_collection_name=${encodeURIComponent(cleanName)}` +
                `&sort_by=year&sort_order=asc`;
              return (
                <a
                  key={fr.collection_id}
                  href={href}
                  className="group relative flex w-[130px] shrink-0 flex-col"
                  title={fr.name}
                >
                  <span className="absolute left-1 top-1 z-10 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-semibold text-amber-400">
                    #{idx + 1}
                  </span>
                  {poster ? (
                    <img
                      src={poster}
                      alt={fr.name}
                      className="h-[195px] w-[130px] rounded-md object-cover transition group-hover:ring-2 group-hover:ring-primary/60"
                    />
                  ) : (
                    <div className="flex h-[195px] w-[130px] items-center justify-center rounded-md bg-muted px-2 text-center text-[10px] text-muted-foreground">
                      {cleanName}
                    </div>
                  )}
                  <div className="mt-1.5 line-clamp-2 text-xs font-medium leading-tight">
                    {cleanName}
                  </div>
                  <div className="text-[10px] text-amber-400">
                    {fr.count} films
                  </div>
                </a>
              );
            })}
          </div>
        )}
      </Section>

      <Section title="Top studios">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={Math.max(280, data.top_studios.length * 22)}>
            <BarChart
              data={data.top_studios}
              layout="vertical"
              margin={{ left: 80 }}
            >
              <XAxis type="number" stroke={CHART_AXIS} fontSize={11} />
              <YAxis
                type="category"
                dataKey="name"
                stroke={CHART_AXIS}
                fontSize={11}
                width={150}
                interval={0}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
                cursor={{ fill: "rgba(245,158,11,0.08)" }}
              />
              <Bar dataKey="count" fill={CHART_PRIMARY} name="Films" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="By source type">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Pie
                data={data.by_source_type}
                dataKey="count"
                nameKey="source_type"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(e: { source_type?: string; name?: string }) =>
                  e.source_type ?? e.name ?? ""
                }
                labelLine={false}
              >
                {data.by_source_type.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Section>
    </div>
  );
}
