import type { ReactNode } from "react";

interface SectionProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function Section({ title, subtitle, children }: SectionProps) {
  return (
    <section className="mb-8">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      {subtitle && (
        <p className="mb-3 mt-0.5 text-xs text-muted-foreground/70">{subtitle}</p>
      )}
      <div className="mt-3">{children}</div>
    </section>
  );
}
