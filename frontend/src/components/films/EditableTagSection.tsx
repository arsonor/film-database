import { useCallback, useEffect, useRef, useState } from "react";
import { Check, Plus, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionHeading } from "./SectionHeading";
import { fetchTaxonomy, updateFilm } from "@/api/client";
import { dimensionLabel } from "@/lib/utils";

interface EditableTagSectionProps {
  filmId: number;
  dimension: string;
  currentValues: string[];
  onSaved: () => void;
  readOnly?: boolean;
}

export function EditableTagSection({
  filmId,
  dimension,
  currentValues,
  onSaved,
  readOnly,
}: EditableTagSectionProps) {
  const [editing, setEditing] = useState(false);
  const [editValues, setEditValues] = useState<string[]>([]);
  const [allOptions, setAllOptions] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load taxonomy options when entering edit mode
  useEffect(() => {
    if (!editing) return;
    setEditValues([...currentValues]);
    fetchTaxonomy(dimension).then((data) => {
      setAllOptions(data.items.map((item) => item.name));
    });
  }, [editing, dimension, currentValues]);

  const availableOptions = allOptions.filter(
    (opt) =>
      !editValues.includes(opt) &&
      opt.toLowerCase().includes(search.toLowerCase()),
  );

  const handleRemoveTag = useCallback((tag: string) => {
    setEditValues((prev) => prev.filter((v) => v !== tag));
  }, []);

  const handleAddTag = useCallback((tag: string) => {
    setEditValues((prev) => [...prev, tag]);
    setSearch("");
    setShowDropdown(false);
    inputRef.current?.focus();
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await updateFilm(filmId, { [dimension]: editValues });
      setEditing(false);
      onSaved();
    } catch {
      // Keep editing on error
    } finally {
      setSaving(false);
    }
  }, [filmId, dimension, editValues, onSaved]);

  const handleCancel = useCallback(() => {
    setEditing(false);
    setSearch("");
    setShowDropdown(false);
  }, []);

  return (
    <div>
      <SectionHeading
        title={dimensionLabel(dimension)}
        onEdit={readOnly ? undefined : () => setEditing(!editing)}
        editing={editing}
      />

      {!editing ? (
        // View mode
        currentValues.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {currentValues.map((val) => (
              <Badge key={val} variant="secondary" className="text-xs">
                {val}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-xs italic text-muted-foreground">No tags yet</p>
        )
      ) : (
        // Edit mode
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1.5">
            {editValues.map((val) => (
              <Badge
                key={val}
                variant="secondary"
                className="gap-1 pr-1 text-xs"
              >
                {val}
                <button
                  onClick={() => handleRemoveTag(val)}
                  className="ml-0.5 rounded-full p-0.5 hover:bg-destructive/20"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>

          {/* Autocomplete input */}
          <div className="relative">
            <Plus className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              ref={inputRef}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              placeholder={`Add ${dimensionLabel(dimension).toLowerCase()}...`}
              className="h-8 pl-8 text-xs"
            />
            {showDropdown && availableOptions.length > 0 && (
              <div className="absolute top-full z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-md border bg-popover shadow-md">
                {availableOptions.map((opt) => (
                  <button
                    key={opt}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => handleAddTag(opt)}
                    className="flex w-full items-center px-3 py-1.5 text-xs hover:bg-accent hover:text-accent-foreground"
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Save / Cancel */}
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
      )}
    </div>
  );
}
