export const CHART_PRIMARY = "#f59e0b";
export const CHART_SECONDARY = "#64748b";
export const CHART_GRID = "#262626";
export const CHART_AXIS = "#94a3b8";

export const TOOLTIP_STYLE = {
  backgroundColor: "#1f1f1f",
  border: "1px solid #404040",
  borderRadius: 6,
  fontSize: 12,
  color: "#e5e5e5",
};
export const TOOLTIP_LABEL_STYLE = { color: "#a3a3a3", fontSize: 11 };
export const TOOLTIP_ITEM_STYLE = { color: "#e5e5e5", fontSize: 12 };

export function formatMillions(n: number): string {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n}`;
}
