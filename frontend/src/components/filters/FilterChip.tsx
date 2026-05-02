import { useCallback, useRef, useState } from "react";
import { Ban, Info, Lock } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

export type ChipState = "off" | "include" | "exclude" | "locked";

interface FilterChipProps {
  name: string;
  count: number | null;
  state: ChipState;
  tooltip?: string;
  onInclude: () => void;
  onExclude: () => void;
  onLockedClick?: () => void;
}

const LONG_PRESS_MS = 500;

export function FilterChip({ name, count, state, tooltip, onInclude, onExclude, onLockedClick }: FilterChipProps) {
  const longPressRef = useRef<ReturnType<typeof setTimeout>>();
  const didLongPress = useRef(false);
  const [infoOpen, setInfoOpen] = useState(false);

  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      if (state === "locked") return;
      onExclude();
    },
    [onExclude, state],
  );

  const handleTouchStart = useCallback(() => {
    if (state === "locked") return;
    didLongPress.current = false;
    longPressRef.current = setTimeout(() => {
      didLongPress.current = true;
      onExclude();
    }, LONG_PRESS_MS);
  }, [onExclude, state]);

  const handleTouchEnd = useCallback(() => {
    clearTimeout(longPressRef.current);
  }, []);

  const handleClick = useCallback(() => {
    if (state === "locked") {
      onLockedClick?.();
      return;
    }
    if (didLongPress.current) return;
    onInclude();
  }, [onInclude, onLockedClick, state]);

  const chip = (
    <button
      onClick={handleClick}
      onContextMenu={handleContextMenu}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchEnd}
      title={tooltip}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium transition-colors select-none",
        state === "include" &&
          "border-primary bg-primary text-primary-foreground",
        state === "exclude" &&
          "border-red-400 bg-red-500/15 text-red-400 line-through",
        state === "off" &&
          "border-border bg-transparent text-muted-foreground hover:border-primary/50 hover:text-foreground",
        state === "locked" &&
          "cursor-not-allowed border-border/40 bg-transparent text-muted-foreground/50 opacity-100",
      )}
    >
      {state === "locked" && <Lock className="h-2.5 w-2.5 shrink-0" />}
      {state === "exclude" && <Ban className="h-3 w-3 shrink-0" />}
      <span className="truncate">{name}</span>
      {count !== null && count > 0 && (
        <span
          className={cn(
            "ml-0.5 text-[10px]",
            state === "include" ? "text-primary-foreground/80" :
            state === "exclude" ? "text-red-400/60" :
            "text-muted-foreground/60",
          )}
        >
          {count}
        </span>
      )}
    </button>
  );

  if (!tooltip) return chip;

  return (
    <Popover open={infoOpen} onOpenChange={setInfoOpen}>
      <div className="inline-flex items-center">
        {chip}
        <PopoverTrigger asChild>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setInfoOpen((v) => !v);
            }}
            className={cn(
              "-ml-0.5 rounded p-0.5 lg:hidden",
              state === "include"
                ? "text-primary-foreground/60"
                : "text-muted-foreground/40 hover:text-muted-foreground",
            )}
          >
            <Info className="h-3 w-3" />
          </button>
        </PopoverTrigger>
      </div>
      <PopoverContent
        side="top"
        className="w-64 px-3 py-2 text-xs"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <p className="font-medium mb-1">{name}</p>
        <p className="text-muted-foreground">{tooltip}</p>
      </PopoverContent>
    </Popover>
  );
}
