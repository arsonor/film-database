import { Trophy } from "lucide-react";
import type { AwardOut } from "@/types/api";
import { SectionHeading } from "./SectionHeading";

interface AwardsTableProps {
  awards: AwardOut[];
}

export function AwardsTable({ awards }: AwardsTableProps) {
  if (awards.length === 0) {
    return (
      <div>
        <SectionHeading title="Awards" />
        <p className="text-sm text-muted-foreground">No awards recorded.</p>
      </div>
    );
  }

  return (
    <div>
      <SectionHeading title="Awards" />
      <div className="space-y-1.5">
        {awards.map((award, i) => (
          <div
            key={`${award.festival_name}-${award.category}-${i}`}
            className="flex items-start gap-2 rounded-md px-2 py-1.5 text-sm"
          >
            <Trophy
              className={`mt-0.5 h-4 w-4 shrink-0 ${
                award.result === "won" ? "text-amber-400" : "text-muted-foreground"
              }`}
            />
            <div className="min-w-0">
              <span className="font-medium text-foreground">{award.festival_name}</span>
              {award.year && (
                <span className="text-muted-foreground"> ({award.year})</span>
              )}
              {award.category && (
                <span className="text-muted-foreground"> — {award.category}</span>
              )}
              <span
                className={`ml-2 text-xs font-medium ${
                  award.result === "won" ? "text-amber-400" : "text-muted-foreground"
                }`}
              >
                {award.result === "won" ? "Won" : "Nominated"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
