import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface DualRangeSliderProps {
  min: number;
  max: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
  onAfterChange?: (value: [number, number]) => void;
  className?: string;
}

export function DualRangeSlider({
  min,
  max,
  value,
  onChange,
  onAfterChange,
  className,
}: DualRangeSliderProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState<"min" | "max" | null>(null);
  const valueRef = useRef(value);
  valueRef.current = value;

  const getPercent = useCallback(
    (v: number) => ((v - min) / (max - min)) * 100,
    [min, max],
  );

  const getValueFromPosition = useCallback(
    (clientX: number) => {
      const track = trackRef.current;
      if (!track) return min;
      const rect = track.getBoundingClientRect();
      const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      return Math.round(min + pct * (max - min));
    },
    [min, max],
  );

  const handlePointerDown = useCallback(
    (thumb: "min" | "max") => (e: React.PointerEvent) => {
      e.preventDefault();
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
      setDragging(thumb);
    },
    [],
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging) return;
      const newVal = getValueFromPosition(e.clientX);
      const [curMin, curMax] = valueRef.current;
      if (dragging === "min") {
        onChange([Math.min(newVal, curMax - 1), curMax]);
      } else {
        onChange([curMin, Math.max(newVal, curMin + 1)]);
      }
    },
    [dragging, getValueFromPosition, onChange],
  );

  const handlePointerUp = useCallback(() => {
    if (dragging) {
      setDragging(null);
      onAfterChange?.(valueRef.current);
    }
  }, [dragging, onAfterChange]);

  // Handle track click to move nearest thumb
  const handleTrackClick = useCallback(
    (e: React.MouseEvent) => {
      const clickVal = getValueFromPosition(e.clientX);
      const [curMin, curMax] = valueRef.current;
      const distToMin = Math.abs(clickVal - curMin);
      const distToMax = Math.abs(clickVal - curMax);
      let next: [number, number];
      if (distToMin <= distToMax) {
        next = [Math.min(clickVal, curMax - 1), curMax];
      } else {
        next = [curMin, Math.max(clickVal, curMin + 1)];
      }
      onChange(next);
      onAfterChange?.(next);
    },
    [getValueFromPosition, onChange, onAfterChange],
  );

  const leftPct = getPercent(value[0]);
  const rightPct = getPercent(value[1]);

  return (
    <div
      ref={trackRef}
      className={cn("relative h-6 w-full cursor-pointer select-none", className)}
      onClick={handleTrackClick}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      {/* Track background */}
      <div className="absolute top-1/2 h-1.5 w-full -translate-y-1/2 rounded-full bg-border" />

      {/* Active range */}
      <div
        className="absolute top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-primary"
        style={{ left: `${leftPct}%`, width: `${rightPct - leftPct}%` }}
      />

      {/* Min thumb */}
      <div
        className={cn(
          "absolute top-1/2 h-4.5 w-4.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-primary shadow-md transition-shadow",
          dragging === "min"
            ? "ring-4 ring-primary/30 scale-110"
            : "hover:ring-4 hover:ring-primary/20",
        )}
        style={{ left: `${leftPct}%` }}
        onPointerDown={handlePointerDown("min")}
        onClick={(e) => e.stopPropagation()}
        role="slider"
        aria-valuemin={min}
        aria-valuemax={value[1]}
        aria-valuenow={value[0]}
        tabIndex={0}
      />

      {/* Max thumb */}
      <div
        className={cn(
          "absolute top-1/2 h-4.5 w-4.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-primary shadow-md transition-shadow",
          dragging === "max"
            ? "ring-4 ring-primary/30 scale-110"
            : "hover:ring-4 hover:ring-primary/20",
        )}
        style={{ left: `${rightPct}%` }}
        onPointerDown={handlePointerDown("max")}
        onClick={(e) => e.stopPropagation()}
        role="slider"
        aria-valuemin={value[0]}
        aria-valuemax={max}
        aria-valuenow={value[1]}
        tabIndex={0}
      />
    </div>
  );
}
