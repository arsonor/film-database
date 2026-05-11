import { useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  AtmosphereByCategoryCell,
  CategoryDecadeCell,
  CinemaMovementCell,
  MessageByMovementCell,
  MessageDecadeCell,
  TaxonomyPayload,
} from "@/types/api";
import { Section } from "./Section";
import { AtmosphereWordCloud } from "./AtmosphereWordCloud";
import { DecadeHeatmap } from "./DecadeHeatmap";
import { CrossTabHeatmap } from "./CrossTabHeatmap";
import { PersonTagsWidget } from "./PersonTagsWidget";
import {
  CHART_AXIS,
  CHART_PRIMARY,
  TOOLTIP_ITEM_STYLE,
  TOOLTIP_LABEL_STYLE,
  TOOLTIP_STYLE,
} from "./chartTheme";

const PIE_COLORS = [
  "#f59e0b", "#d97706", "#fbbf24", "#fcd34d", "#92400e", "#b45309",
  "#64748b", "#475569", "#94a3b8", "#cbd5e1", "#1e293b", "#334155",
];

type DecadeView = "genres" | "movements" | "messages";
type CrossView = "atmosphere_by_genre" | "message_by_movement";

const DECADE_TABS: { value: DecadeView; label: string; subtitle: string }[] = [
  {
    value: "genres",
    label: "Genres",
    subtitle: "What share of each decade's films belongs to each genre. Each cell = % of decade.",
  },
  {
    value: "movements",
    label: "Cinema movements",
    subtitle: "Number of films tagged with each movement, per decade. The diagonal pattern reveals when each era dominated.",
  },
  {
    value: "messages",
    label: "Messages",
    subtitle: "% of films per decade conveying each message. Notice when feminist films emerge, when ecological themes appear...",
  },
];

const CROSS_TABS: { value: CrossView; label: string; subtitle: string }[] = [
  {
    value: "atmosphere_by_genre",
    label: "Atmosphere by genre",
    subtitle: "% of films in each genre matching each atmosphere. A genre's signature mood profile.",
  },
  {
    value: "message_by_movement",
    label: "Message by movement",
    subtitle: "% of films in each cinema movement conveying each message. Reveals which ideas each movement championed.",
  },
];

interface Props {
  data: TaxonomyPayload;
}

function TabBar<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: { value: T; label: string }[];
  active: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="mb-3 flex w-fit gap-1 rounded-md border border-border bg-background p-0.5">
      {tabs.map((t) => (
        <button
          key={t.value}
          type="button"
          onClick={() => onChange(t.value)}
          className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
            active === t.value
              ? "bg-amber-500/20 text-amber-500"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function TaxonomyTab({ data }: Props) {
  const [decadeView, setDecadeView] = useState<DecadeView>("genres");
  const [crossView, setCrossView] = useState<CrossView>("atmosphere_by_genre");

  const activeDecade = DECADE_TABS.find((t) => t.value === decadeView)!;
  const activeCross = CROSS_TABS.find((t) => t.value === crossView)!;

  return (
    <div className="space-y-6">
      {/* Compact top row: themes / genres pie / atmosphere cloud */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-3">
          <h3 className="mb-2 text-sm font-semibold text-foreground">Top 20 themes</h3>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={data.top_themes} layout="vertical" margin={{ left: 4, right: 8 }}>
              <XAxis type="number" stroke={CHART_AXIS} fontSize={10} />
              <YAxis
                type="category"
                dataKey="name"
                stroke={CHART_AXIS}
                fontSize={10}
                width={110}
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

        <div className="rounded-lg border border-border bg-card p-3">
          <h3 className="mb-2 text-sm font-semibold text-foreground">Genre distribution</h3>
          <ResponsiveContainer width="100%" height={360}>
            <PieChart>
              <Tooltip contentStyle={TOOLTIP_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
              <Pie
                data={data.category_distribution}
                dataKey="count"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={110}
                label={(e) => e.name}
                labelLine={false}
              >
                {data.category_distribution.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg border border-border bg-card p-3">
          <h3 className="mb-2 text-sm font-semibold text-foreground">Atmospheres</h3>
          <p className="mb-1 text-xs text-muted-foreground">Word cloud sized by film count</p>
          <AtmosphereWordCloud data={data.top_atmospheres} />
        </div>
      </div>

      {/* Decade heatmaps — tab switcher */}
      <Section
        title={`${activeDecade.label} × decade`}
        subtitle={activeDecade.subtitle}
      >
        <TabBar tabs={DECADE_TABS} active={decadeView} onChange={setDecadeView} />
        <div className="rounded-lg border border-border bg-card p-4">
          {decadeView === "genres" && (
            <DecadeHeatmap<CategoryDecadeCell>
              data={data.category_by_decade_heatmap}
              rowKey={(c) => c.category}
              decadeKey={(c) => c.decade}
              valueKey={(c) => c.pct}
              cellLabel={(c) => (c.pct >= 1 ? `${Math.round(c.pct)}%` : "")}
              tooltip={(c) =>
                `${c.category} · ${c.decade}s · ${c.pct}% (${c.film_count} of ${c.decade_total} films)`
              }
            />
          )}
          {decadeView === "movements" && (
            <DecadeHeatmap<CinemaMovementCell>
              data={data.cinema_movements_by_decade}
              rowKey={(c) => c.movement}
              decadeKey={(c) => c.decade}
              valueKey={(c) => c.count}
              cellLabel={(c) => (c.count > 0 ? String(c.count) : "")}
              tooltip={(c) => `${c.movement} · ${c.decade}s · ${c.count} films`}
              rowSortOrder={(c) => c.sort_order}
              rowLabelWidth={160}
            />
          )}
          {decadeView === "messages" && (
            <DecadeHeatmap<MessageDecadeCell>
              data={data.message_by_decade_heatmap}
              rowKey={(c) => c.message}
              decadeKey={(c) => c.decade}
              valueKey={(c) => c.pct}
              cellLabel={(c) => (c.pct >= 0.5 ? `${Math.round(c.pct)}%` : "")}
              tooltip={(c) =>
                `${c.message} · ${c.decade}s · ${c.pct}% (${c.film_count} of ${c.decade_total} films)`
              }
              rowSortOrder={(c) => c.sort_order}
            />
          )}
        </div>
      </Section>

      <Section
        title="Most common tags by filmography"
        subtitle="Pick a director, composer, or actor to see their characteristic themes, atmospheres, characters, and messages."
      >
        <PersonTagsWidget />
      </Section>

      {/* Cross-tab heatmaps — tab switcher */}
      <Section title={activeCross.label} subtitle={activeCross.subtitle}>
        <TabBar tabs={CROSS_TABS} active={crossView} onChange={setCrossView} />
        <div className="rounded-lg border border-border bg-card p-4">
          {crossView === "atmosphere_by_genre" && (
            <CrossTabHeatmap<AtmosphereByCategoryCell>
              data={data.atmosphere_by_category}
              rowKey={(c) => c.category}
              colKey={(c) => c.atmosphere}
              colSortOrder={(c) => c.atmosphere_sort_order}
              valueKey={(c) => c.pct}
              cellLabel={(c) => (c.pct >= 1 ? `${Math.round(c.pct)}%` : "")}
              tooltip={(c) =>
                `${c.category} · ${c.atmosphere} · ${c.pct}% (${c.film_count} of ${c.category_total} films)`
              }
            />
          )}
          {crossView === "message_by_movement" && (
            <CrossTabHeatmap<MessageByMovementCell>
              data={data.message_by_movement}
              rowKey={(c) => c.movement}
              colKey={(c) => c.message}
              rowSortOrder={(c) => c.movement_sort_order}
              colSortOrder={(c) => c.message_sort_order}
              valueKey={(c) => c.pct}
              cellLabel={(c) => (c.pct >= 1 ? `${Math.round(c.pct)}%` : "")}
              tooltip={(c) =>
                `${c.movement} · ${c.message} · ${c.pct}% (${c.film_count} of ${c.movement_total} films)`
              }
              rowLabelWidth={160}
            />
          )}
        </div>
      </Section>
    </div>
  );
}
