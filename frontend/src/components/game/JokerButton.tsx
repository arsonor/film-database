import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface JokerButtonProps {
  icon: LucideIcon;
  label: string;
  remaining: number;
  onClick: () => void;
  disabled?: boolean;
}

export function JokerButton({ icon: Icon, label, remaining, onClick, disabled }: JokerButtonProps) {
  const isDead = remaining <= 0 || disabled;
  return (
    <button
      onClick={onClick}
      disabled={isDead}
      className={cn(
        "flex flex-col items-center gap-1 rounded-md border px-3 py-2 text-xs font-medium transition-colors",
        isDead
          ? "cursor-not-allowed border-border/40 text-muted-foreground/40"
          : "border-border bg-muted/30 text-foreground hover:border-primary hover:bg-primary/10",
      )}
      title={label}
    >
      <Icon className="h-4 w-4" />
      <span className="hidden sm:inline">{label}</span>
      <span className="text-[10px] text-muted-foreground">×{remaining}</span>
    </button>
  );
}
