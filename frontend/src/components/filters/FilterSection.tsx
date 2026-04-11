import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight, Lock } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import type { TaxonomyItem } from "@/types/api";
import type { TagFilter } from "@/types/api";
import { FilterChip, type ChipState } from "./FilterChip";

interface FilterSectionProps {
  title: string;
  dimension: string;
  items: TaxonomyItem[];
  tagFilter: TagFilter;
  onToggle: (value: string) => void;
  onExclude: (value: string) => void;
  onSetMode: (mode: "or" | "and") => void;
  defaultExpanded?: boolean;
  locked?: boolean;
  lockedTagNames?: Set<string>;
  canAddFilter?: boolean;
  canUseOrNot?: boolean;
  onLockedClick?: () => void;
  onLimitReached?: () => void;
}

export function FilterSection({
  title,
  items,
  tagFilter,
  onToggle,
  onExclude,
  onSetMode,
  defaultExpanded = false,
  locked,
  lockedTagNames,
  canAddFilter = true,
  canUseOrNot = true,
  onLockedClick,
  onLimitReached,
}: FilterSectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const activeCount = tagFilter.include.length + tagFilter.exclude.length;

  return (
    <div className="border-b border-border pb-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between py-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
      >
        <span className="flex items-center gap-2">
          {title}
          {locked && (
            <>
              <Lock className="h-3 w-3 text-amber-500/60" />
              <span className="text-[10px] font-normal text-amber-500">Pro</span>
            </>
          )}
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
        <>
          {canUseOrNot && tagFilter.include.length >= 2 && (
            <div className="flex items-center gap-1 pb-1.5">
              <button
                onClick={() => onSetMode(tagFilter.mode === "or" ? "and" : "or")}
                className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide transition-colors ${
                  tagFilter.mode === "or"
                    ? "bg-blue-500/20 text-blue-400"
                    : "bg-amber-500/20 text-amber-400"
                }`}
              >
                {tagFilter.mode}
              </button>
              <span className="text-[10px] text-muted-foreground">
                {tagFilter.mode === "or" ? "any match" : "all must match"}
              </span>
            </div>
          )}
          <div className="flex flex-wrap gap-1.5 pb-2">
            {items.map((item, index) => {
              const prevOrder = index > 0 ? items[index - 1]!.sort_order : null;
              const showSeparator =
                prevOrder !== null &&
                prevOrder !== undefined &&
                item.sort_order !== null &&
                item.sort_order !== undefined &&
                Math.floor(item.sort_order / 100) !== Math.floor(prevOrder / 100);

              const isTagLocked = locked || lockedTagNames?.has(item.name);

              let chipState: ChipState;
              if (isTagLocked) {
                chipState = "locked";
              } else if (tagFilter.include.includes(item.name)) {
                chipState = "include";
              } else if (tagFilter.exclude.includes(item.name)) {
                chipState = "exclude";
              } else {
                chipState = "off";
              }

              // If filter limit reached, "off" chips behave as locked
              const effectiveState = chipState === "off" && !canAddFilter ? "locked" : chipState;

              return (
                <Fragment key={item.id}>
                  {showSeparator && (
                    <Separator className="my-1" />
                  )}
                  <FilterChip
                    name={item.name}
                    count={item.film_count}
                    state={effectiveState}
                    onInclude={() => onToggle(item.name)}
                    onExclude={canUseOrNot ? () => onExclude(item.name) : () => {}}
                    onLockedClick={isTagLocked ? onLockedClick : onLimitReached}
                  />
                </Fragment>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
