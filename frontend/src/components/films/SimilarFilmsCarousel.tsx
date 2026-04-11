import { Lock, Sparkles } from "lucide-react";
import { SectionHeading } from "./SectionHeading";
import { Skeleton } from "@/components/ui/skeleton";

interface SimilarFilmsCarouselProps {
  filmId: number;
  locked?: boolean;
}

export function SimilarFilmsCarousel({ filmId: _filmId, locked }: SimilarFilmsCarouselProps) {
  if (locked) {
    return (
      <div>
        <SectionHeading title="Similar Films" />
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-amber-500/30 bg-amber-500/5 p-6">
          <Lock className="h-5 w-5 text-amber-500/60" />
          <div>
            <p className="text-sm font-medium text-foreground">Discover similar films</p>
            <p className="text-xs text-muted-foreground">Upgrade to Pro to unlock personalized recommendations</p>
          </div>
        </div>
      </div>
    );
  }

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
