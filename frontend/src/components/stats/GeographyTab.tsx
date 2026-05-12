import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import type { GeographyPayload, MostInternationalFilm } from "@/types/api";
import { LockedTabPlaceholder } from "./LockedTabPlaceholder";
import { Section } from "./Section";
import { StatCard } from "./StatCard";
import { WorldMap } from "./WorldMap";
import { CountryFilmsPanel } from "./CountryFilmsPanel";
import { SetPlaceTreemap } from "./SetPlaceTreemap";

interface Props {
  data: GeographyPayload | null;
}

export function GeographyTab({ data }: Props) {
  const { isAuthenticated } = useAuth();
  const [selectedProd, setSelectedProd] = useState<
    { iso: string; country: string } | null
  >(null);
  const [selectedSet, setSelectedSet] = useState<
    { iso: string; country: string } | null
  >(null);

  if (data === null) {
    return (
      <LockedTabPlaceholder
        reason={isAuthenticated ? "upgrade" : "signup"}
        tabName="Geography"
      />
    );
  }

  return (
    <div className="space-y-8">
      {/* Stat cards row */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <StatCard
          value={data.production_country_total}
          label="Countries produced in"
        />
        {data.most_international_film && (
          <MostInternationalCard film={data.most_international_film} />
        )}
      </div>

      {/* Production map */}
      <Section
        title="Where films are produced"
        subtitle="Each country shaded by the number of films co-produced there. Click a country for its top 10 films."
      >
        <WorldMap
          data={data.production_countries}
          onCountryClick={(iso, country) =>
            setSelectedProd({ iso, country })
          }
          selectedIso={selectedProd?.iso ?? null}
        />
        {selectedProd && (
          <CountryFilmsPanel
            iso={selectedProd.iso}
            country={selectedProd.country}
            type="production"
            onClose={() => setSelectedProd(null)}
          />
        )}
      </Section>

      {/* Set-place map */}
      <Section
        title="Where films take place"
        subtitle="Same map, different question: which countries are the films set in?"
      >
        <WorldMap
          data={data.set_place_countries}
          onCountryClick={(iso, country) =>
            setSelectedSet({ iso, country })
          }
          selectedIso={selectedSet?.iso ?? null}
        />
        {selectedSet && (
          <CountryFilmsPanel
            iso={selectedSet.iso}
            country={selectedSet.country}
            type="set_place"
            onClose={() => setSelectedSet(null)}
          />
        )}
      </Section>

      {/* Treemap */}
      <Section
        title="Locations breakdown"
        subtitle="Drill down continent → country → city. Click a city to browse its films."
      >
        <SetPlaceTreemap data={data.set_place_treemap} />
      </Section>
    </div>
  );
}

function MostInternationalCard({ film }: { film: MostInternationalFilm }) {
  return (
    <Link
      to={`/films/${film.film_id}`}
      className="group flex items-center gap-3 rounded-lg border border-border bg-card p-3 transition-colors hover:border-amber-500/60 hover:bg-amber-500/5"
    >
      {film.poster_url ? (
        <img
          src={film.poster_url}
          alt={film.title}
          className="h-[90px] w-[60px] rounded object-cover ring-1 ring-border group-hover:ring-amber-500/60"
        />
      ) : (
        <div className="flex h-[90px] w-[60px] items-center justify-center rounded bg-muted text-[10px] text-muted-foreground">
          No poster
        </div>
      )}
      <div className="min-w-0 flex-1">
        <div className="text-2xl font-semibold text-primary">
          {film.country_count} countries
        </div>
        <div className="mt-0.5 text-xs uppercase tracking-wide text-muted-foreground">
          Most international film
        </div>
        <div className="mt-1 truncate text-sm font-medium text-foreground">
          {film.title}
          {film.year && (
            <span className="ml-1 text-xs text-muted-foreground">
              ({film.year})
            </span>
          )}
        </div>
        {film.countries.length > 0 && (
          <div className="mt-1 truncate font-mono text-[10px] text-muted-foreground">
            {film.countries.join(" · ")}
          </div>
        )}
      </div>
    </Link>
  );
}
