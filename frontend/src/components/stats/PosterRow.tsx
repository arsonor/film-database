import { Link } from "react-router-dom";

interface PosterRowItem {
  film_id: number;
  title: string;
  poster_url: string | null;
  year: number | null;
  caption?: string;
}

export function PosterRow({ items }: { items: PosterRowItem[] }) {
  if (items.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">No films available.</p>
    );
  }
  return (
    <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-2">
      {items.map((film, idx) => (
        <Link
          key={film.film_id}
          to={`/films/${film.film_id}`}
          className="group relative flex w-[130px] shrink-0 flex-col"
        >
          <span className="absolute left-1 top-1 z-10 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-semibold text-amber-400">
            #{idx + 1}
          </span>
          {film.poster_url ? (
            <img
              src={film.poster_url}
              alt={film.title}
              className="h-[195px] w-[130px] rounded-md object-cover transition group-hover:ring-2 group-hover:ring-primary/60"
            />
          ) : (
            <div className="flex h-[195px] w-[130px] items-center justify-center rounded-md bg-muted text-xs text-muted-foreground">
              No poster
            </div>
          )}
          <div className="mt-1.5 text-xs font-medium leading-tight line-clamp-2">
            {film.title}
          </div>
          {film.year && (
            <div className="text-[10px] text-muted-foreground">{film.year}</div>
          )}
          {film.caption && (
            <div className="mt-0.5 text-[10px] text-amber-400">{film.caption}</div>
          )}
        </Link>
      ))}
    </div>
  );
}
