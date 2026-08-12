import { Fragment, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Lock } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import type { TaxonomyItem } from "@/types/api";
import type { TagFilter } from "@/types/api";
import { groupItems } from "@/lib/taxonomyGroups";
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
  descriptions?: Record<string, string>;
  onLockedClick?: () => void;
  onLimitReached?: () => void;
}

type GroupNode = ReturnType<typeof groupItems<TaxonomyItem>>[number];

/** A sub-dimension that is itself split into named sub-sub-dimensions. */
interface ParentNode {
  kind: "parent";
  label: string;
  children: GroupNode[];
}

type TreeNode = ({ kind: "group" } & GroupNode) | ParentNode;

/**
 * Nest consecutive groups that share a `parent` umbrella under a single node,
 * so "Sub-genres" / "Human Relations" / "Narrative techniques" become
 * collapsible sub-dimensions containing collapsible sub-sub-dimensions.
 */
function buildTree(groups: GroupNode[]): TreeNode[] {
  const tree: TreeNode[] = [];
  for (const group of groups) {
    const parent = group.group?.parent;
    if (!parent) {
      tree.push({ kind: "group", ...group });
      continue;
    }
    const last = tree[tree.length - 1];
    if (last && last.kind === "parent" && last.label === parent) {
      last.children.push(group);
    } else {
      tree.push({ kind: "parent", label: parent, children: [group] });
    }
  }
  return tree;
}

export function FilterSection({
  title,
  dimension,
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
  descriptions,
  onLockedClick,
  onLimitReached,
}: FilterSectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  // Sub-dimensions the user has opened. Everything starts collapsed so the
  // dimension reads as a list of named sub-dimensions; anything holding an
  // active filter is force-opened below so selections are never hidden.
  const [openGroups, setOpenGroups] = useState<Set<number>>(new Set());
  const [openParents, setOpenParents] = useState<Set<string>>(new Set());
  const activeCount = tagFilter.include.length + tagFilter.exclude.length;

  const tree = useMemo(
    () => buildTree(groupItems(dimension, items, (item) => item.sort_order)),
    [dimension, items],
  );

  const activeNames = useMemo(
    () => new Set([...tagFilter.include, ...tagFilter.exclude]),
    [tagFilter.include, tagFilter.exclude],
  );

  const toggleGroup = (block: number | null) => {
    if (block === null) return;
    setOpenGroups((prev) => {
      const next = new Set(prev);
      if (next.has(block)) next.delete(block);
      else next.add(block);
      return next;
    });
  };

  const toggleParent = (label: string) => {
    setOpenParents((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  };

  const countActive = (groupItemList: TaxonomyItem[]) =>
    groupItemList.filter((i) => activeNames.has(i.name)).length;

  const allTagsLocked = (groupItemList: TaxonomyItem[]) =>
    locked || groupItemList.every((i) => lockedTagNames?.has(i.name));

  const renderGroupRow = ({
    label,
    total,
    active,
    locked: rowLocked,
    open,
    onClick,
    indent = false,
  }: {
    label: string;
    total: number;
    active: number;
    locked: boolean;
    open: boolean;
    onClick: () => void;
    indent?: boolean;
  }) => (
    <button
      onClick={onClick}
      className={`mt-1.5 flex min-h-[40px] w-full items-center justify-between gap-2 rounded py-2 pr-1 text-left transition-colors hover:text-foreground lg:mt-1 lg:min-h-0 lg:py-1.5 ${
        indent
          ? "pl-4 text-[13px] font-medium text-muted-foreground/90 lg:pl-3 lg:text-[11px]"
          : "pl-1 text-sm font-semibold text-muted-foreground lg:pl-0.5 lg:text-xs"
      }`}
    >
      <span className="flex items-center gap-1.5">
        {label}
        {rowLocked && <Lock className="h-3 w-3 text-amber-500/60 lg:h-2.5 lg:w-2.5" />}
        {active > 0 && (
          <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground lg:h-4 lg:min-w-4 lg:text-[9px]">
            {active}
          </span>
        )}
      </span>
      <span className="flex items-center gap-1.5">
        <span className="text-[11px] font-normal tabular-nums text-muted-foreground/50 lg:text-[10px]">
          {total}
        </span>
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 lg:h-3 lg:w-3" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 lg:h-3 lg:w-3" />
        )}
      </span>
    </button>
  );

  const renderChips = (groupItemList: TaxonomyItem[], indent = false) => (
    <div
      className={`flex flex-wrap gap-2 pb-3 pt-1 lg:gap-1.5 lg:pb-2 lg:pt-0.5 ${
        indent ? "pl-4 lg:pl-3" : ""
      }`}
    >
      {groupItemList.map((item) => {
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
          <FilterChip
            key={item.id}
            name={item.name}
            count={item.film_count}
            state={effectiveState}
            tooltip={descriptions?.[item.name]}
            onInclude={() => onToggle(item.name)}
            onExclude={canUseOrNot ? () => onExclude(item.name) : () => {}}
            onLockedClick={isTagLocked ? onLockedClick : onLimitReached}
          />
        );
      })}
    </div>
  );

  return (
    <div className="border-b border-border pb-2.5 lg:pb-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex min-h-[48px] w-full items-center justify-between py-3 text-base font-semibold text-foreground hover:text-primary transition-colors lg:min-h-0 lg:py-2 lg:text-sm lg:font-medium"
      >
        <span className="flex items-center gap-2">
          {title}
          {locked && (
            <>
              <Lock className="h-3.5 w-3.5 text-amber-500/60 lg:h-3 lg:w-3" />
              <span className="text-[11px] font-normal text-amber-500 lg:text-[10px]">Pro</span>
            </>
          )}
          {activeCount > 0 && (
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[11px] font-bold text-primary-foreground lg:text-[10px]">
              {activeCount}
            </span>
          )}
        </span>
        {expanded ? (
          <ChevronDown className="h-5 w-5 text-muted-foreground lg:h-4 lg:w-4" />
        ) : (
          <ChevronRight className="h-5 w-5 text-muted-foreground lg:h-4 lg:w-4" />
        )}
      </button>
      {expanded && (
        <>
          {canUseOrNot && tagFilter.include.length >= 2 && (
            <div className="flex items-center gap-2 pb-2 lg:gap-1 lg:pb-1.5">
              <button
                onClick={() => onSetMode(tagFilter.mode === "or" ? "and" : "or")}
                className={`rounded px-2.5 py-1 text-xs font-bold uppercase tracking-wide transition-colors lg:px-1.5 lg:py-0.5 lg:text-[10px] ${
                  tagFilter.mode === "or"
                    ? "bg-blue-500/20 text-blue-400"
                    : "bg-amber-500/20 text-amber-400"
                }`}
              >
                {tagFilter.mode}
              </button>
              <span className="text-xs text-muted-foreground lg:text-[10px]">
                {tagFilter.mode === "or" ? "any match" : "all must match"}
              </span>
            </div>
          )}

          {tree.map((node, index) => {
            if (node.kind === "parent") {
              const allItems = node.children.flatMap((c) => c.items);
              const parentActive = countActive(allItems);
              // Never hide an active selection behind a collapsed sub-dimension
              const parentOpen = openParents.has(node.label) || parentActive > 0;

              return (
                <Fragment key={`parent-${node.label}`}>
                  {renderGroupRow({
                    label: node.label,
                    total: allItems.length,
                    active: parentActive,
                    locked: allTagsLocked(allItems),
                    open: parentOpen,
                    onClick: () => toggleParent(node.label),
                  })}
                  {parentOpen &&
                    node.children.map((child, childIndex) => {
                      const childActive = countActive(child.items);
                      const childOpen = openGroups.has(child.block!) || childActive > 0;
                      return (
                        <Fragment key={child.block ?? `child-${childIndex}`}>
                          {renderGroupRow({
                            label: child.group?.label ?? "",
                            total: child.items.length,
                            active: childActive,
                            locked: allTagsLocked(child.items),
                            open: childOpen,
                            onClick: () => toggleGroup(child.block),
                            indent: true,
                          })}
                          {childOpen && renderChips(child.items, true)}
                        </Fragment>
                      );
                    })}
                </Fragment>
              );
            }

            const label = node.group?.label;

            // Groups with no label entry keep the plain-separator rendering
            if (!label) {
              return (
                <Fragment key={node.block ?? `ungrouped-${index}`}>
                  {index > 0 && <Separator className="my-1" />}
                  {renderChips(node.items)}
                </Fragment>
              );
            }

            const groupActive = countActive(node.items);
            const isOpen = openGroups.has(node.block!) || groupActive > 0;

            return (
              <Fragment key={node.block ?? `group-${index}`}>
                {renderGroupRow({
                  label,
                  total: node.items.length,
                  active: groupActive,
                  locked: allTagsLocked(node.items),
                  open: isOpen,
                  onClick: () => toggleGroup(node.block),
                })}
                {isOpen && renderChips(node.items)}
              </Fragment>
            );
          })}
        </>
      )}
    </div>
  );
}
