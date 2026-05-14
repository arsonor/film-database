import { Info, type LucideIcon } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface JokerButtonProps {
  icon: LucideIcon;
  label: string;
  remaining: number;
  onClick: () => void;
  disabled?: boolean;
  description?: string;
}

export function JokerButton({ icon: Icon, label, remaining, onClick, disabled, description }: JokerButtonProps) {
  const isDead = remaining <= 0 || disabled;
  return (
    <div className="flex items-center gap-1">
      <button
        onClick={onClick}
        disabled={isDead}
        className={cn(
          "flex w-[88px] flex-col items-center gap-1 rounded-md border px-3 py-3 text-sm font-medium transition-colors sm:w-[88px] sm:px-3 sm:py-2 sm:text-xs",
          isDead
            ? "cursor-not-allowed border-border/40 text-muted-foreground/40"
            : "border-border bg-muted/30 text-foreground hover:border-primary hover:bg-primary/10 active:bg-primary/20",
        )}
        title={label}
      >
        <Icon className="h-5 w-5 sm:h-4 sm:w-4" />
        <span>{label}</span>
        <span className="text-[11px] text-muted-foreground sm:text-[10px]">×{remaining}</span>
      </button>
      {description && (
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              onClick={(e) => e.stopPropagation()}
              aria-label={`About ${label}`}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary/60 bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 sm:h-6 sm:w-6"
            >
              <Info className="h-4 w-4 sm:h-3.5 sm:w-3.5" />
            </button>
          </PopoverTrigger>
          <PopoverContent
            side="bottom"
            className="w-64 px-3 py-2 text-xs"
            onOpenAutoFocus={(e) => e.preventDefault()}
          >
            <p className="mb-1 font-medium">{label}</p>
            <p className="text-muted-foreground">{description}</p>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}
