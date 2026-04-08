import { useCallback, useState } from "react";
import { Check, Plus, Trash2, Trophy, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AwardOut } from "@/types/api";
import { SectionHeading } from "./SectionHeading";
import { updateFilm } from "@/api/client";

const FESTIVALS = [
  "Academy Awards",
  "Cannes Film Festival",
  "Venice Film Festival",
  "Berlin International Film Festival",
  "César Awards",
  "BAFTA Awards",
  "Golden Globes",
  "Sundance Film Festival",
  "Toronto International Film Festival",
  "Palme d'Or",
  "SAG Awards",
  "Emmy Awards",
  "Independent Spirit Awards",
  "Locarno Film Festival",
  "San Sebastián Film Festival",
  "Lumières Awards",
] as const;

interface AwardsTableProps {
  awards: AwardOut[];
  filmId: number;
  onSaved: () => void;
  readOnly?: boolean;
}

interface EditableAward {
  festival_name: string;
  category: string | null;
  year: number | null;
  result: "won" | "nominated";
}

export function AwardsTable({ awards, filmId, onSaved, readOnly }: AwardsTableProps) {
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

  const handleChange = useCallback(
    (index: number, field: keyof EditableAward, value: string | number | null) => {
      setEditAwards((prev) =>
        prev.map((a, i) => (i === index ? { ...a, [field]: value } : a)),
      );
    },
    [],
  );

  const handleAdd = useCallback(() => {
    setEditAwards((prev) => [
      ...prev,
      { festival_name: FESTIVALS[0], category: null, year: null, result: "nominated" as const },
    ]);
  }, []);

  return (
    <div>
      <SectionHeading
        title="Awards"
        onEdit={readOnly ? undefined : startEdit}
        editing={editing}
      />

      {!editing ? (
        awards.length > 0 ? (
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
          <p className="text-sm text-muted-foreground">No awards recorded.</p>
        )
      ) : (
        <div className="space-y-2">
          {editAwards.map((award, i) => (
            <div
              key={`edit-${i}`}
              className="flex flex-wrap items-center gap-1.5 rounded-md border border-border px-2 py-1.5"
            >
              {/* Festival */}
              <Select
                value={award.festival_name}
                onValueChange={(v) => handleChange(i, "festival_name", v)}
              >
                <SelectTrigger className="h-7 w-52 shrink-0 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FESTIVALS.map((f) => (
                    <SelectItem key={f} value={f}>{f}</SelectItem>
                  ))}
                  {/* Keep current value if not in list */}
                  {!FESTIVALS.includes(award.festival_name as typeof FESTIVALS[number]) && (
                    <SelectItem value={award.festival_name}>{award.festival_name}</SelectItem>
                  )}
                </SelectContent>
              </Select>
              {/* Category */}
              <Input
                value={award.category || ""}
                onChange={(e) => handleChange(i, "category", e.target.value || null)}
                placeholder="Category"
                className="h-7 flex-1 min-w-[120px] text-xs"
              />
              {/* Year */}
              <Input
                type="number"
                value={award.year ?? ""}
                onChange={(e) =>
                  handleChange(i, "year", e.target.value ? parseInt(e.target.value, 10) : null)
                }
                placeholder="Year"
                className="h-7 w-20 shrink-0 text-center text-xs"
              />
              {/* Result toggle */}
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
              {/* Delete */}
              <button
                onClick={() => handleRemove(i)}
                className="rounded-full p-0.5 text-muted-foreground hover:bg-destructive/20 hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}

          {editAwards.length === 0 && (
            <p className="text-sm text-muted-foreground">All awards removed.</p>
          )}

          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1 text-xs"
            onClick={handleAdd}
          >
            <Plus className="h-3 w-3" /> Add award
          </Button>

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
