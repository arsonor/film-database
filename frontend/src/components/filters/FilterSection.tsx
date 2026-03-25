import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { TaxonomyItem } from "@/types/api";
import { FilterChip } from "./FilterChip";

interface FilterSectionProps {
  title: string;
  dimension: string;
  items: TaxonomyItem[];
  activeValues: string[];
  onToggle: (value: string) => void;
  defaultExpanded?: boolean;
}

export function FilterSection({
  title,
  items,
  activeValues,
  onToggle,
  defaultExpanded = false,
}: FilterSectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const activeCount = activeValues.length;

  return (
    <div className="border-b border-border pb-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between py-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
      >
        <span className="flex items-center gap-2">
          {title}
          {activeCount > 0 && (
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground">
              {activeCount}
            </span>
          )}
        </span>
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {expanded && (
        <div className="flex flex-wrap gap-1.5 pb-2">
          {items.map((item) => (
            <FilterChip
              key={item.id}
              name={item.name}
              count={item.film_count}
              active={activeValues.includes(item.name)}
              onClick={() => onToggle(item.name)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
