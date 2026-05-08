import { useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import { QuickStatsTab } from "@/components/stats/QuickStatsTab";
import { GeographyTab } from "@/components/stats/GeographyTab";
import { FinancialsTab } from "@/components/stats/FinancialsTab";
import { PeopleTab } from "@/components/stats/PeopleTab";
import { TaxonomyTab } from "@/components/stats/TaxonomyTab";
import { LockedTabPlaceholder } from "@/components/stats/LockedTabPlaceholder";

type TabKey = "quick" | "geo" | "financials" | "people" | "taxonomy";

const TABS: { key: TabKey; label: string }[] = [
  { key: "quick", label: "Quick Stats" },
  { key: "geo", label: "Geography" },
  { key: "financials", label: "Financials" },
  { key: "people", label: "People" },
  { key: "taxonomy", label: "Taxonomy" },
];

function tabButtonClass(active: boolean) {
  return [
    "border-b-2 px-3 py-2 text-sm font-medium transition",
    active
      ? "border-primary text-primary"
      : "border-transparent text-muted-foreground hover:text-foreground",
  ].join(" ");
}

export function StatsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { tier, isAuthenticated } = useAuth();
  const { data, isLoading, error } = useDashboardStats();

  const activeTab = (searchParams.get("tab") as TabKey) || "quick";
  const setTab = useCallback(
    (key: TabKey) => {
      const next = new URLSearchParams(searchParams);
      next.set("tab", key);
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const isAnonymous = !isAuthenticated;
  const effectiveTier = data?.tier ?? (tier ?? (isAuthenticated ? "free" : "anonymous"));
  const isFree = effectiveTier === "free";

  let body: React.ReactNode = null;
  if (isLoading) {
    body = (
      <div className="py-16 text-center text-sm text-muted-foreground">
        Loading dashboard…
      </div>
    );
  } else if (error || !data) {
    body = (
      <div className="py-16 text-center text-sm text-destructive">
        Failed to load dashboard. {(error as Error | undefined)?.message ?? ""}
      </div>
    );
  } else {
    if (activeTab === "quick") {
      body = (
        <QuickStatsTab
          data={data.quick}
          personalStats={data.personal_stats}
        />
      );
    } else if (activeTab === "geo") {
      body = <GeographyTab />;
    } else if (activeTab === "financials") {
      if (!data.financials) {
        body = <LockedTabPlaceholder reason="signup" tabName="Financials" />;
      } else {
        body = <FinancialsTab data={data.financials} />;
      }
    } else if (activeTab === "people") {
      if (!data.people) {
        body = (
          <LockedTabPlaceholder
            reason={isAnonymous ? "signup" : "upgrade"}
            tabName="People"
          />
        );
      } else {
        body = <PeopleTab data={data.people} />;
      }
    } else if (activeTab === "taxonomy") {
      if (!data.taxonomy) {
        body = (
          <LockedTabPlaceholder
            reason={isAnonymous ? "signup" : "upgrade"}
            tabName="Taxonomy"
          />
        );
      } else {
        body = <TaxonomyTab data={data.taxonomy} />;
      }
    }
  }

  const totalFilms = data?.quick.total_films;

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 lg:px-6">
        <Button variant="ghost" size="icon" onClick={() => navigate("/browse")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <BarChart3 className="h-5 w-5 text-primary" />
        <h1 className="text-lg font-semibold">Database Stats</h1>
        {totalFilms !== undefined && (
          <span className="hidden rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground sm:inline-flex">
            {totalFilms.toLocaleString()} films
          </span>
        )}
        <div className="ml-auto text-xs text-muted-foreground">
          {isAuthenticated ? (
            <span>Tier: <span className="font-medium text-foreground">{effectiveTier}</span></span>
          ) : (
            <Link to="/auth?mode=signup" className="text-primary hover:underline">
              Sign up free
            </Link>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-7xl p-4 lg:p-6">
        <div className="mb-6 flex flex-wrap gap-1 border-b border-border">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={tabButtonClass(activeTab === t.key)}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>
        {body}
      </main>
    </div>
  );
}
