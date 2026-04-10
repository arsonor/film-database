import type { PaginatedFilms } from "@/types/api";
import { Skeleton } from "@/components/ui/skeleton";
import { FilmCard } from "./FilmCard";

interface FilmGridProps {
  films: PaginatedFilms | null;
  loading: boolean;
  error: string | null;
  canToggleStatus?: boolean;
  onStatusChanged?: () => void;
}

function SkeletonCard() {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg bg-card">
      <Skeleton className="aspect-[2/3] w-full" />
      <div className="space-y-2 p-2.5">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

export function FilmGrid({ films, loading, error, canToggleStatus, onStatusChanged }: FilmGridProps) {
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20 text-center">
        <p className="text-lg font-medium text-destructive-foreground">Error</p>
        <p className="max-w-md text-sm text-muted-foreground">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        {Array.from({ length: 24 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!films || films.items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20 text-center">
        <p className="text-lg font-medium text-foreground">No films found</p>
        <p className="text-sm text-muted-foreground">
          Try adjusting your filters or search terms.
        </p>
      </div>
    );
  }

  return (
    <div>
      <p className="mb-4 text-sm text-muted-foreground">
        Showing {films.items.length} of {films.total} films
      </p>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        {films.items.map((film) => (
          <FilmCard key={film.film_id} film={film} canToggleStatus={canToggleStatus} onStatusChanged={onStatusChanged} />
        ))}
      </div>
    </div>
  );
}
