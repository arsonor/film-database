import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, Pencil, Plus, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionHeading } from "./SectionHeading";
import { fetchTaxonomy, updateFilm } from "@/api/client";
import type { TaxonomyItem } from "@/types/api";
import { TAXONOMY_GROUPS, groupItems } from "@/lib/taxonomyGroups";
import { dimensionLabel } from "@/lib/utils";

interface EditableTagSectionProps {
  filmId: number;
  dimension: string;
  currentValues: string[];
  onSaved: () => void;
  readOnly?: boolean;
  allowCustom?: boolean;
  hideTitle?: boolean;
  /**
   * Full taxonomy for this dimension. When given, view mode groups the film's
   * tags under their sub-dimension names (and orders them by sort_order).
   */
  taxonomyItems?: TaxonomyItem[];
}

export function EditableTagSection({
  filmId,
  dimension,
  currentValues,
  onSaved,
  readOnly,
  allowCustom,
  hideTitle,
  taxonomyItems,
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
    if (taxonomyItems) {
      setAllOptions(taxonomyItems.map((item) => item.name));
      return;
    }
    fetchTaxonomy(dimension).then((data) => {
      setAllOptions(data.items.map((item) => item.name));
    });
  }, [editing, dimension, currentValues, taxonomyItems]);

  // View mode: split the film's tags into their sub-dimension groups, in
  // taxonomy order. Tags unknown to the taxonomy keep their original order in a
  // trailing unlabelled run.
  const groupedValues = useMemo(() => {
    if (!taxonomyItems || !TAXONOMY_GROUPS[dimension]) return null;
    const selected = new Set(currentValues);
    const known = taxonomyItems.filter((item) => selected.has(item.name));
    if (known.length === 0) return null;
    const knownNames = new Set(known.map((i) => i.name));
    const unknown = currentValues.filter((v) => !knownNames.has(v));
    return {
      groups: groupItems(dimension, known, (item) => item.sort_order),
      unknown,
    };
  }, [taxonomyItems, dimension, currentValues]);

  const availableOptions = allOptions.filter(
    (opt) =>
      !editValues.includes(opt) &&
      opt.toLowerCase().includes(search.toLowerCase()),
  );

  const canAddCustom =
    allowCustom &&
    search.trim() !== "" &&
    !editValues.includes(search.trim()) &&
    !allOptions.some((opt) => opt.toLowerCase() === search.trim().toLowerCase());

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
      {!hideTitle && (
        <SectionHeading
          title={dimensionLabel(dimension)}
          onEdit={readOnly ? undefined : () => setEditing(!editing)}
          editing={editing}
        />
      )}

      {!editing ? (
        // View mode
        currentValues.length > 0 ? (
          groupedValues ? (
            <div className="space-y-2">
              {groupedValues.groups.map((group, index) => {
                const label = group.group?.label;
                const parent = group.group?.parent;
                const prevParent = groupedValues.groups[index - 1]?.group?.parent;
                return (
                  <Fragment key={group.block ?? `g-${index}`}>
                    {parent !== undefined && parent !== prevParent && (
                      <p className="pt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
                        {parent}
                      </p>
                    )}
                    <div>
                      {label && (
                        <p className="mb-1 text-[11px] font-semibold text-muted-foreground">
                          {label}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {group.items.map((item) => (
                          <Badge key={item.name} variant="secondary" className="text-xs">
                            {item.name}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </Fragment>
                );
              })}
              {groupedValues.unknown.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  {groupedValues.unknown.map((val) => (
                    <Badge key={val} variant="secondary" className="text-xs">
                      {val}
                    </Badge>
                  ))}
                </div>
              )}
              {hideTitle && !readOnly && (
                <button onClick={() => setEditing(true)} className="rounded p-0.5 text-muted-foreground hover:text-foreground">
                  <Pencil className="h-3 w-3" />
                </button>
              )}
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-1.5">
              {currentValues.map((val) => (
                <Badge key={val} variant="secondary" className="text-xs">
                  {val}
                </Badge>
              ))}
              {hideTitle && !readOnly && (
                <button onClick={() => setEditing(true)} className="rounded p-0.5 text-muted-foreground hover:text-foreground">
                  <Pencil className="h-3 w-3" />
                </button>
              )}
            </div>
          )
        ) : hideTitle && !readOnly ? (
          <button onClick={() => setEditing(true)} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
            <Plus className="h-3 w-3" />
            Add {dimensionLabel(dimension).toLowerCase()}
          </button>
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
              onKeyDown={(e) => {
                if (e.key === "Enter" && canAddCustom) {
                  e.preventDefault();
                  handleAddTag(search.trim());
                }
              }}
              placeholder={`Add ${dimensionLabel(dimension).toLowerCase()}...`}
              className="h-8 pl-8 text-xs"
            />
            {showDropdown && (availableOptions.length > 0 || canAddCustom) && (
              <div className="absolute top-full z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-md border bg-popover shadow-md">
                {canAddCustom && (
                  <button
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => handleAddTag(search.trim())}
                    className="flex w-full items-center px-3 py-1.5 text-xs font-medium text-primary hover:bg-accent hover:text-accent-foreground"
                  >
                    <Plus className="mr-1.5 h-3 w-3" /> Add "{search.trim()}"
                  </button>
                )}
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
