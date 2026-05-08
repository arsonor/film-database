import { useState } from "react";
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
import type {
  GenderCounts,
  LivingCounts,
  PeopleGenderKey,
  PeoplePayload,
  PeopleRoleKey,
  PersonRank,
} from "@/types/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Section } from "./Section";
import { PersonRankCard } from "./PersonRankCard";
import {
  CHART_AXIS,
  CHART_PRIMARY,
  CHART_SECONDARY,
  TOOLTIP_ITEM_STYLE,
  TOOLTIP_LABEL_STYLE,
  TOOLTIP_STYLE,
} from "./chartTheme";

interface Props {
  data: PeoplePayload;
}

const GENDER_COLORS = { M: "#3b82f6", F: "#ec4899", unknown: "#64748b" };
const LIVING_COLORS = { living: "#22c55e", deceased: "#64748b", unknown: "#94a3b8" };

const ROLE_LABELS: Record<PeopleRoleKey, string> = {
  directors: "Directors",
  actors: "Actors",
  composers: "Composers",
};
const ROLE_SINGULAR: Record<PeopleRoleKey, "Director" | "Actor" | "Composer"> = {
  directors: "Director",
  actors: "Actor",
  composers: "Composer",
};
const GENDER_LABELS: Record<PeopleGenderKey, string> = {
  all: "All",
  male: "Male only",
  female: "Female only",
};

function PersonGrid({
  people,
  role,
}: {
  people: PersonRank[];
  role: "Director" | "Actor" | "Composer";
}) {
  if (people.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-border bg-card/50 p-6 text-center text-sm text-muted-foreground">
        No matching people in the database.
      </p>
    );
  }
  return (
    <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
      {people.map((p) => (
        <PersonRankCard key={p.person_id} person={p} role={role} />
      ))}
    </div>
  );
}

function GenderPie({ title, counts }: { title: string; counts: GenderCounts }) {
  const data = [
    { name: "Male", value: counts.M, color: GENDER_COLORS.M },
    { name: "Female", value: counts.F, color: GENDER_COLORS.F },
    { name: "Unknown", value: counts.unknown, color: GENDER_COLORS.unknown },
  ].filter((d) => d.value > 0);
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="mb-2 text-xs font-medium text-muted-foreground">{title}</div>
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Tooltip contentStyle={TOOLTIP_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={60}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function LivingPie({ title, counts }: { title: string; counts: LivingCounts }) {
  const data = [
    { name: "Living", value: counts.living, color: LIVING_COLORS.living },
    { name: "Deceased", value: counts.deceased, color: LIVING_COLORS.deceased },
    { name: "Unknown", value: counts.unknown, color: LIVING_COLORS.unknown },
  ].filter((d) => d.value > 0);
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="mb-2 text-xs font-medium text-muted-foreground">{title}</div>
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Tooltip contentStyle={TOOLTIP_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={60}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function NationalityChart({
  data,
}: {
  data: { nationality: string; count: number }[];
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <ResponsiveContainer
        width="100%"
        height={Math.max(220, data.length * 26)}
      >
        <BarChart data={data} layout="vertical" margin={{ left: 60 }}>
          <XAxis type="number" stroke={CHART_AXIS} fontSize={11} />
          <YAxis
            type="category"
            dataKey="nationality"
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
          <Bar dataKey="count" fill={CHART_PRIMARY} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PeopleTab({ data }: Props) {
  const [role, setRole] = useState<PeopleRoleKey>("directors");
  const [genderFilter, setGenderFilter] = useState<PeopleGenderKey>("all");

  const directorGenderDecade = data.directors_gender_by_decade.map((d) => ({
    decade: `${d.decade}s`,
    M: d.M,
    F: d.F,
  }));

  const birthDecade = data.directors_by_birth_decade.map((d) => ({
    decade: `${d.birth_decade}s`,
    count: d.count,
  }));

  const peopleList = data.top_people[role][genderFilter] ?? [];

  return (
    <div>
      <Section title="Most prolific">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Select value={role} onValueChange={(v) => setRole(v as PeopleRoleKey)}>
            <SelectTrigger className="h-9 w-40 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(ROLE_LABELS) as PeopleRoleKey[]).map((k) => (
                <SelectItem key={k} value={k}>
                  {ROLE_LABELS[k]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={genderFilter}
            onValueChange={(v) => setGenderFilter(v as PeopleGenderKey)}
          >
            <SelectTrigger className="h-9 w-36 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(GENDER_LABELS) as PeopleGenderKey[]).map((k) => (
                <SelectItem key={k} value={k}>
                  {GENDER_LABELS[k]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <PersonGrid people={peopleList} role={ROLE_SINGULAR[role]} />
      </Section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Director nationalities">
          <NationalityChart data={data.top_director_nationalities} />
        </Section>
        <Section title="Actor nationalities">
          <NationalityChart data={data.top_actor_nationalities} />
        </Section>
      </div>

      <Section title="Gender split">
        <div className="grid gap-3 md:grid-cols-3">
          <GenderPie title="All people" counts={data.gender_split.all} />
          <GenderPie title="Directors" counts={data.gender_split.directors} />
          <GenderPie title="Actors" counts={data.gender_split.actors} />
        </div>
      </Section>

      <Section
        title="Female directors over time"
        subtitle="Women directing films, by decade"
      >
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={directorGenderDecade}>
              <XAxis dataKey="decade" stroke={CHART_AXIS} fontSize={11} />
              <YAxis stroke={CHART_AXIS} fontSize={11} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
                cursor={{ fill: "rgba(245,158,11,0.08)" }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="M" stackId="g" fill={GENDER_COLORS.M} name="Male" />
              <Bar dataKey="F" stackId="g" fill={GENDER_COLORS.F} name="Female" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="Living vs deceased">
        <div className="grid gap-3 md:grid-cols-2">
          <LivingPie title="Directors" counts={data.living_status.directors} />
          <LivingPie title="Actors" counts={data.living_status.actors} />
        </div>
      </Section>

      <Section
        title="What generation are our directors from?"
        subtitle="How many directors in the database were born in each decade — i.e. which generation produced the most filmmakers we cover."
      >
        <div className="rounded-lg border border-border bg-card p-3">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={birthDecade}>
              <XAxis dataKey="decade" stroke={CHART_AXIS} fontSize={11} />
              <YAxis stroke={CHART_AXIS} fontSize={11} />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
                cursor={{ fill: "rgba(245,158,11,0.08)" }}
              />
              <Bar dataKey="count" fill={CHART_SECONDARY} name="Directors born" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>
    </div>
  );
}
