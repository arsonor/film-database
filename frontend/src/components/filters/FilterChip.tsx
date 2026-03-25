import { cn } from "@/lib/utils";

interface FilterChipProps {
  name: string;
  count: number | null;
  active: boolean;
  onClick: () => void;
}

export function FilterChip({ name, count, active, onClick }: FilterChipProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium transition-colors",
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-transparent text-muted-foreground hover:border-primary/50 hover:text-foreground",
      )}
    >
      <span className="truncate">{name}</span>
      {count !== null && count > 0 && (
        <span
          className={cn(
            "ml-0.5 text-[10px]",
            active ? "text-primary-foreground/80" : "text-muted-foreground/60",
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
}
