import { Lock } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface LockedTabPlaceholderProps {
  reason: "signup" | "upgrade" | "coming_soon";
  tabName: string;
}

export function LockedTabPlaceholder({ reason, tabName }: LockedTabPlaceholderProps) {
  let title = "";
  let body = "";
  let cta: { label: string; href: string } | null = null;

  if (reason === "signup") {
    title = `Sign up free to unlock ${tabName}`;
    body = `Create a free account to access ${tabName} stats.`;
    cta = { label: "Sign up free", href: "/auth?mode=signup" };
  } else if (reason === "upgrade") {
    title = `Upgrade to Pro to unlock ${tabName}`;
    body = `${tabName} stats are part of the Pro tier.`;
    cta = { label: "Upgrade to Pro", href: "#" };
  } else {
    title = `${tabName} stats coming soon`;
    body = "This dashboard tab is under construction.";
  }

  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 p-8 text-center">
      <Lock className="mb-4 h-10 w-10 text-primary/70" />
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">{body}</p>
      {cta && (
        <Button asChild className="mt-5" disabled={cta.href === "#"}>
          {cta.href === "#" ? (
            <span>{cta.label}</span>
          ) : (
            <Link to={cta.href}>{cta.label}</Link>
          )}
        </Button>
      )}
    </div>
  );
}
