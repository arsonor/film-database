import { useCallback, useState } from "react";
import { Check, Trophy, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AwardOut } from "@/types/api";
import { SectionHeading } from "./SectionHeading";
import { updateFilm } from "@/api/client";

interface AwardsTableProps {
  awards: AwardOut[];
  filmId: number;
  onSaved: () => void;
}

interface EditableAward {
  festival_name: string;
  category: string | null;
  year: number | null;
  result: "won" | "nominated";
}

export function AwardsTable({ awards, filmId, onSaved }: AwardsTableProps) {
  const [editing, setEditing] = useState(false);
  const [editAwards, setEditAwards] = useState<EditableAward[]>([]);
  const [saving, setSaving] = useState(false);

  const startEdit = useCallback(() => {
    setEditAwards(
      awards.map((a) => ({
        festival_name: a.festival_name,
        category: a.category,
        year: a.year,
        result: a.result as "won" | "nominated",
      }))
    );
    setEditing(true);
  }, [awards]);

  const handleToggleResult = useCallback((index: number) => {
    setEditAwards((prev) =>
      prev.map((a, i) =>
        i === index
          ? { ...a, result: a.result === "won" ? "nominated" : "won" }
          : a
      )
    );
  }, []);

  const handleRemove = useCallback((index: number) => {
    setEditAwards((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await updateFilm(filmId, { awards: editAwards });
      setEditing(false);
      onSaved();
    } catch {
      // Keep editing on error
    } finally {
      setSaving(false);
    }
  }, [filmId, editAwards, onSaved]);

  const handleCancel = useCallback(() => {
    setEditing(false);
  }, []);

  if (awards.length === 0 && !editing) {
    return (
      <div>
        <SectionHeading title="Awards" />
        <p className="text-sm text-muted-foreground">No awards recorded.</p>
      </div>
    );
  }

  return (
    <div>
      <SectionHeading
        title="Awards"
        onEdit={startEdit}
        editing={editing}
      />

      {!editing ? (
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
      ) : (
        <div className="space-y-2">
          {editAwards.map((award, i) => (
            <div
              key={`edit-${award.festival_name}-${award.category}-${i}`}
              className="flex items-center gap-2 rounded-md bg-muted/30 px-2 py-1.5 text-sm"
            >
              <Trophy
                className={`h-4 w-4 shrink-0 ${
                  award.result === "won" ? "text-amber-400" : "text-muted-foreground"
                }`}
              />
              <div className="min-w-0 flex-1">
                <span className="font-medium text-foreground">{award.festival_name}</span>
                {award.year && (
                  <span className="text-muted-foreground"> ({award.year})</span>
                )}
                {award.category && (
                  <span className="text-muted-foreground"> — {award.category}</span>
                )}
              </div>
              <Badge
                variant="outline"
                className={`cursor-pointer select-none text-xs ${
                  award.result === "won"
                    ? "border-amber-400/50 text-amber-400 hover:bg-amber-400/10"
                    : "text-muted-foreground hover:bg-muted"
                }`}
                onClick={() => handleToggleResult(i)}
              >
                {award.result === "won" ? "Won" : "Nominated"}
              </Badge>
              <button
                onClick={() => handleRemove(i)}
                className="rounded-full p-1 text-muted-foreground hover:bg-destructive/20 hover:text-destructive"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}

          {editAwards.length === 0 && (
            <p className="text-sm text-muted-foreground">All awards removed.</p>
          )}

          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              onClick={handleSave}
              disabled={saving}
              className="h-7 gap-1 px-2 text-xs"
            >
              <Check className="h-3 w-3" />
              Save
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleCancel}
              disabled={saving}
              className="h-7 gap-1 px-2 text-xs"
            >
              <X className="h-3 w-3" />
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
