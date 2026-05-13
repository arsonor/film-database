import { Heart } from "lucide-react";
import { cn } from "@/lib/utils";

interface LivesDisplayProps {
  lives: number;
  shakeKey?: number;
}

export function LivesDisplay({ lives, shakeKey }: LivesDisplayProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-1",
        shakeKey !== undefined && shakeKey > 0 && "animate-shake",
      )}
      key={shakeKey}
    >
      {[0, 1, 2].map((i) => {
        const alive = i < lives;
        return (
          <Heart
            key={i}
            className={cn(
              "h-5 w-5 transition-all",
              alive ? "fill-red-500 text-red-500" : "fill-none text-muted-foreground/30",
            )}
          />
        );
      })}
    </div>
  );
}
