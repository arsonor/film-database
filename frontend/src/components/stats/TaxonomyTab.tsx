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
import type { TaxonomyPayload } from "@/types/api";
import { Section } from "./Section";
import { AtmosphereWordCloud } from "./AtmosphereWordCloud";
import { CategoryDecadeHeatmap } from "./CategoryDecadeHeatmap";
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

interface Props {
  data: TaxonomyPayload;
}

export function TaxonomyTab({ data }: Props) {
  return (
    <div>
      <Section title="Top 20 themes">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={Math.max(280, data.top_themes.length * 26)}>
            <BarChart data={data.top_themes} layout="vertical" margin={{ left: 60 }}>
              <XAxis type="number" stroke={CHART_AXIS} fontSize={11} />
              <YAxis
                type="category"
                dataKey="name"
                stroke={CHART_AXIS}
                fontSize={11}
                width={120}
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

      <Section title="Genres distribution">
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={340}>
            <PieChart>
              <Tooltip contentStyle={TOOLTIP_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Pie
                data={data.category_distribution}
                dataKey="count"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={120}
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
      </Section>

      <Section title="Atmospheres" subtitle="Word cloud sized by film count">
        <AtmosphereWordCloud data={data.top_atmospheres} />
      </Section>

      <Section
        title="Category evolution over time"
        subtitle="Each cell shows how many films of a given category were released in a decade. Brighter = more films."
      >
        <div className="rounded-lg border border-border bg-card p-4">
          <CategoryDecadeHeatmap data={data.category_by_decade_heatmap} />
        </div>
      </Section>
    </div>
  );
}
