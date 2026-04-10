import { useCallback, useState } from "react";
import { Star } from "lucide-react";

interface StarRatingProps {
  value: number | null; // 1-10 or null
  onChange: (value: number | null) => void;
  readonly?: boolean;
}

export function StarRating({ value, onChange, readonly }: StarRatingProps) {
  const [hoveredValue, setHoveredValue] = useState<number | null>(null);

  const displayValue = hoveredValue ?? value ?? 0;

  const handleClick = useCallback(
    (clickValue: number) => {
      if (readonly) return;
      onChange(value === clickValue ? null : clickValue);
    },
    [value, onChange, readonly],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>, starIndex: number) => {
      if (readonly) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const isLeftHalf = e.clientX - rect.left < rect.width / 2;
      setHoveredValue(isLeftHalf ? starIndex * 2 - 1 : starIndex * 2);
    },
    [readonly],
  );

  const handleStarClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>, starIndex: number) => {
      if (readonly) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const isLeftHalf = e.clientX - rect.left < rect.width / 2;
      handleClick(isLeftHalf ? starIndex * 2 - 1 : starIndex * 2);
    },
    [readonly, handleClick],
  );

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => {
        const fullThreshold = i * 2;
        const halfThreshold = i * 2 - 1;
        const isFull = displayValue >= fullThreshold;
        const isHalf = !isFull && displayValue >= halfThreshold;

        return (
          <button
            key={i}
            type="button"
            disabled={readonly}
            onClick={(e) => handleStarClick(e, i)}
            onMouseMove={(e) => handleMouseMove(e, i)}
            onMouseLeave={() => setHoveredValue(null)}
            className={`relative p-0.5 transition-colors ${readonly ? "cursor-default" : "cursor-pointer"}`}
          >
            {/* Empty star (background) */}
            <Star className="h-4 w-4 fill-none text-muted-foreground/40" />
            {/* Filled overlay */}
            {(isFull || isHalf) && (
              <div
                className="absolute inset-0 overflow-hidden p-0.5"
                style={isHalf ? { width: "50%" } : undefined}
              >
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
              </div>
            )}
          </button>
        );
      })}
      {value !== null && (
        <span className="ml-1 text-xs text-muted-foreground">{value}/10</span>
      )}
    </div>
  );
}
