interface StatCardProps {
  value: number | string;
  label: string;
  sublabel?: string;
}

export function StatCard({ value, label, sublabel }: StatCardProps) {
  const display =
    typeof value === "number" ? value.toLocaleString() : value;
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-2xl font-semibold text-primary">{display}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      {sublabel && (
        <div className="mt-0.5 text-[10px] text-muted-foreground/70">{sublabel}</div>
      )}
    </div>
  );
}
