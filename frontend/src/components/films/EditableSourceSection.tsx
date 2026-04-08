import { useCallback, useState } from "react";
import { Check, Pencil, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { updateFilm } from "@/api/client";
import type { SourceOut } from "@/types/api";

const SOURCE_TYPES = [
  "original screenplay",
  "novel",
  "comic",
  "TV series",
  "true story",
  "play",
  "video game",
  "poem",
  "short story",
  "remake",
] as const;

interface EditEntry {
  source_type: string;
  source_title: string;
  author: string;
}

interface EditableSourceSectionProps {
  filmId: number;
  sources: SourceOut[];
  onSaved: () => void;
  readOnly?: boolean;
}

function sourceLabel(src: { source_type: string; source_title: string | null; author: string | null }) {
  let label = src.source_type;
  if (src.source_title) label += `: ${src.source_title}`;
  if (src.author) label += ` by ${src.author}`;
  return label;
}

export function EditableSourceSection({
  filmId,
  sources,
  onSaved,
  readOnly,
}: EditableSourceSectionProps) {
  const [editing, setEditing] = useState(false);
  const [entries, setEntries] = useState<EditEntry[]>([]);
  const [saving, setSaving] = useState(false);

  const startEditing = useCallback(() => {
    setEntries(
      sources.map((s) => ({
        source_type: s.source_type,
        source_title: s.source_title || "",
        author: s.author || "",
      })),
    );
    setEditing(true);
  }, [sources]);

  const handleCancel = useCallback(() => {
    setEditing(false);
  }, []);

  const handleRemove = useCallback((index: number) => {
    setEntries((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleChange = useCallback(
    (index: number, field: keyof EditEntry, value: string) => {
      setEntries((prev) =>
        prev.map((e, i) => (i === index ? { ...e, [field]: value } : e)),
      );
    },
    [],
  );

  const handleAdd = useCallback(() => {
    setEntries((prev) => [
      ...prev,
      { source_type: "original screenplay", source_title: "", author: "" },
    ]);
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await updateFilm(filmId, {
        sources: entries
          .filter((e) => e.source_type)
          .map((e) => ({
            source_type: e.source_type,
            source_title: e.source_title || null,
            author: e.author || null,
          })),
      });
      setEditing(false);
      onSaved();
    } catch {
      // keep editing
    } finally {
      setSaving(false);
    }
  }, [filmId, entries, onSaved]);

  if (!editing) {
    return (
      <div className="flex items-start gap-1">
        <div className="flex-1">
          {sources.length > 0 ? (
            <div className="space-y-0.5 text-sm text-muted-foreground">
              {sources.map((src, i) => (
                <div key={i}>{sourceLabel(src)}</div>
              ))}
            </div>
          ) : (
            <p className="text-xs italic text-muted-foreground">No source info</p>
          )}
        </div>
        {!readOnly && (
          <button
            onClick={startEditing}
            className="mt-0.5 rounded p-0.5 text-muted-foreground hover:text-primary"
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="space-y-2">
        {entries.map((entry, i) => (
          <div
            key={i}
            className="flex items-start gap-1.5 rounded-md border border-border px-2 py-1.5"
          >
            <Select
              value={entry.source_type}
              onValueChange={(v) => handleChange(i, "source_type", v)}
            >
              <SelectTrigger className="h-7 w-36 shrink-0 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SOURCE_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              value={entry.source_title}
              onChange={(e) => handleChange(i, "source_title", e.target.value)}
              placeholder="Title (optional)"
              className="h-7 flex-1 text-xs"
            />
            <Input
              value={entry.author}
              onChange={(e) => handleChange(i, "author", e.target.value)}
              placeholder="Author (optional)"
              className="h-7 w-28 shrink-0 text-xs"
            />
            <button
              onClick={() => handleRemove(i)}
              className="mt-1 rounded-full p-0.5 text-muted-foreground hover:bg-destructive/20 hover:text-destructive"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}

        <Button
          variant="outline"
          size="sm"
          className="h-7 gap-1 text-xs"
          onClick={handleAdd}
        >
          <Plus className="h-3 w-3" /> Add source
        </Button>

        <div className="flex gap-2">
          <Button
            size="sm"
            className="h-7 gap-1 text-xs"
            onClick={handleSave}
            disabled={saving}
          >
            <Check className="h-3 w-3" />
            {saving ? "Saving..." : "Save"}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={handleCancel}
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
