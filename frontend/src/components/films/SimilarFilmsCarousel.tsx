import { Sparkles } from "lucide-react";
import { SectionHeading } from "./SectionHeading";
import { Skeleton } from "@/components/ui/skeleton";

interface SimilarFilmsCarouselProps {
  filmId: number;
}

export function SimilarFilmsCarousel({ filmId: _filmId }: SimilarFilmsCarouselProps) {
  return (
    <div>
      <SectionHeading title="Similar Films" />
      <div className="flex items-center gap-3 rounded-lg border border-dashed border-border p-6">
        <Sparkles className="h-5 w-5 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Recommendations coming soon
        </p>
      </div>
      {/* Placeholder skeleton carousel */}
      <div className="mt-3 flex gap-3 overflow-hidden">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-40 w-28 shrink-0 rounded-lg" />
        ))}
      </div>
    </div>
  );
}
