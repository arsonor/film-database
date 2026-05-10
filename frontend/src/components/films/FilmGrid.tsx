import type { PaginatedFilms } from "@/types/api";
import { Skeleton } from "@/components/ui/skeleton";
import { TooltipProvider } from "@/components/ui/tooltip";
import { FilmCard } from "./FilmCard";

interface FilmGridProps {
  films: PaginatedFilms | null;
  loading: boolean;
  error: string | null;
  canToggleStatus?: boolean;
  onStatusChanged?: () => void;
  compact?: boolean;
}

function SkeletonCard({ compact }: { compact?: boolean }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg bg-card">
      <Skeleton className="aspect-[2/3] w-full" />
      {!compact && (
        <div className="space-y-2 p-2.5">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      )}
    </div>
  );
}

export function FilmGrid({ films, loading, error, canToggleStatus, onStatusChanged, compact }: FilmGridProps) {
  const gridClass = compact
    ? "grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10"
    : "grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6";
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
      <div className={gridClass}>
        {Array.from({ length: compact ? 60 : 24 }).map((_, i) => (
          <SkeletonCard key={i} compact={compact} />
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

  const content = (
    <div>
      <p className="mb-4 text-sm text-muted-foreground">
        Showing {films.items.length} of {films.total} films
      </p>
      <div className={gridClass}>
        {films.items.map((film) => (
          <FilmCard key={film.film_id} film={film} canToggleStatus={canToggleStatus} onStatusChanged={onStatusChanged} compact={compact} />
        ))}
      </div>
    </div>
  );

  if (compact) {
    return <TooltipProvider delayDuration={150}>{content}</TooltipProvider>;
  }
  return content;
}
