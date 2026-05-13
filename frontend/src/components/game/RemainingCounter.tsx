import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface RemainingCounterProps {
  count: number;
  poolSize: number;
}

export function RemainingCounter({ count, poolSize }: RemainingCounterProps) {
  const [displayed, setDisplayed] = useState(count);

  useEffect(() => {
    setDisplayed(count);
  }, [count]);

  const pct = poolSize > 0 ? count / poolSize : 0;
  const color =
    count === 1 ? "text-emerald-400" :
    pct < 0.05 ? "text-amber-400" :
    pct < 0.25 ? "text-orange-400" :
    "text-foreground";

  return (
    <div className="flex flex-col items-center">
      <div className={cn("text-4xl font-bold tabular-nums transition-colors sm:text-5xl", color)}>
        {displayed.toLocaleString()}
      </div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
        of {poolSize.toLocaleString()} remaining
      </div>
    </div>
  );
}
