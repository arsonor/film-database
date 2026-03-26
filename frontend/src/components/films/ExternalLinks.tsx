import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ExternalLinksProps {
  tmdbId: number | null;
  imdbId: string | null;
  title: string;
  year: string | null;
}

export function ExternalLinks({ tmdbId, imdbId, title, year }: ExternalLinksProps) {
  const yearStr = year ? new Date(year).getFullYear().toString() : "";

  const links = [
    tmdbId
      ? { label: "TMDB", href: `https://www.themoviedb.org/movie/${tmdbId}` }
      : null,
    imdbId
      ? { label: "IMDb", href: `https://www.imdb.com/title/${imdbId}` }
      : null,
    {
      label: "Allocine",
      href: `https://www.google.com/search?q=allocine+${encodeURIComponent(title)}+${yearStr}`,
    },
    {
      label: "Wikipedia",
      href: `https://en.wikipedia.org/wiki/Special:Search/${encodeURIComponent(title)}_(film)`,
    },
  ].filter(Boolean) as { label: string; href: string }[];

  return (
    <div className="flex flex-wrap gap-2">
      {links.map((link) => (
        <Button
          key={link.label}
          variant="outline"
          size="sm"
          className="h-7 gap-1.5 text-xs"
          asChild
        >
          <a href={link.href} target="_blank" rel="noopener noreferrer">
            {link.label}
            <ExternalLink className="h-3 w-3" />
          </a>
        </Button>
      ))}
    </div>
  );
}
