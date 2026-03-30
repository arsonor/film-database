import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  GitMerge,
  Pencil,
  Plus,
  Trash2,
  Check,
  X,
} from "lucide-react";
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
import {
  addTaxonomyValue,
  deleteTaxonomyValue,
  fetchTaxonomy,
  mergeTaxonomyValues,
  renameTaxonomyValue,
} from "@/api/client";
import { TAXONOMY_DIMENSIONS } from "@/types/api";
import type { TaxonomyItem } from "@/types/api";
import { dimensionLabel } from "@/lib/utils";

type Dimension = (typeof TAXONOMY_DIMENSIONS)[number];

export function TaxonomyAdminPage() {
  const [dimension, setDimension] = useState<Dimension>("categories");
  const [items, setItems] = useState<TaxonomyItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Add state
  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState(false);

  // Rename state
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState("");

  // Merge state
  const [mergingId, setMergingId] = useState<number | null>(null);
  const [mergeTargetId, setMergeTargetId] = useState<string>("");

  // Status message
  const [status, setStatus] = useState<{ type: "ok" | "err"; msg: string } | null>(null);

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchTaxonomy(dimension);
      setItems(data.items);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [dimension]);

  useEffect(() => {
    loadItems();
    setRenamingId(null);
    setMergingId(null);
    setNewName("");
    setStatus(null);
  }, [loadItems]);

  const showStatus = (type: "ok" | "err", msg: string) => {
    setStatus({ type, msg });
    setTimeout(() => setStatus(null), 3000);
  };

  // Add
  const handleAdd = async () => {
    if (!newName.trim()) return;
    setAdding(true);
    try {
      await addTaxonomyValue(dimension, newName.trim());
      setNewName("");
      showStatus("ok", `Added "${newName.trim()}"`);
      await loadItems();
    } catch (e: unknown) {
      showStatus("err", e instanceof Error ? e.message : "Add failed");
    } finally {
      setAdding(false);
    }
  };

  // Rename
  const handleRename = async (id: number) => {
    if (!renameValue.trim()) return;
    try {
      await renameTaxonomyValue(dimension, id, renameValue.trim());
      setRenamingId(null);
      showStatus("ok", `Renamed to "${renameValue.trim()}"`);
      await loadItems();
    } catch (e: unknown) {
      showStatus("err", e instanceof Error ? e.message : "Rename failed");
    }
  };

  // Merge
  const handleMerge = async (sourceId: number) => {
    const targetId = parseInt(mergeTargetId, 10);
    if (!targetId || targetId === sourceId) return;
    const source = items.find((i) => i.id === sourceId);
    const target = items.find((i) => i.id === targetId);
    if (
      !window.confirm(
        `Merge "${source?.name}" into "${target?.name}"?\nAll films will be reassigned to "${target?.name}" and "${source?.name}" will be deleted.`,
      )
    )
      return;
    try {
      const result = await mergeTaxonomyValues(dimension, sourceId, targetId);
      setMergingId(null);
      setMergeTargetId("");
      showStatus("ok", `Merged — ${result.films_affected} films reassigned`);
      await loadItems();
    } catch (e: unknown) {
      showStatus("err", e instanceof Error ? e.message : "Merge failed");
    }
  };

  // Delete
  const handleDelete = async (item: TaxonomyItem) => {
    const count = item.film_count ?? 0;
    const msg =
      count > 0
        ? `Delete "${item.name}"? It is used by ${count} films — they will lose this tag.`
        : `Delete "${item.name}"?`;
    if (!window.confirm(msg)) return;
    try {
      await deleteTaxonomyValue(dimension, item.id, count > 0);
      showStatus("ok", `Deleted "${item.name}"`);
      await loadItems();
    } catch (e: unknown) {
      showStatus("err", e instanceof Error ? e.message : "Delete failed");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 flex h-14 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur sm:px-6">
        <Button asChild variant="ghost" size="icon">
          <Link to="/browse">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <h1 className="text-lg font-semibold">Manage Taxonomy</h1>
        {status && (
          <span
            className={`ml-auto text-sm ${status.type === "ok" ? "text-emerald-500" : "text-destructive"}`}
          >
            {status.msg}
          </span>
        )}
      </header>

      <div className="mx-auto flex max-w-5xl gap-6 p-4 sm:p-6">
        {/* Left: dimension selector */}
        <nav className="hidden w-48 shrink-0 space-y-1 sm:block">
          {TAXONOMY_DIMENSIONS.map((dim) => (
            <button
              key={dim}
              onClick={() => setDimension(dim)}
              className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                dim === dimension
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              {dimensionLabel(dim)}
            </button>
          ))}
        </nav>

        {/* Mobile dimension selector */}
        <div className="sm:hidden">
          <Select
            value={dimension}
            onValueChange={(v) => setDimension(v as Dimension)}
          >
            <SelectTrigger className="h-9 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TAXONOMY_DIMENSIONS.map((dim) => (
                <SelectItem key={dim} value={dim}>
                  {dimensionLabel(dim)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Right: values table */}
        <div className="flex-1">
          <h2 className="mb-4 text-xl font-bold">{dimensionLabel(dimension)}</h2>

          {/* Add new value */}
          <div className="mb-4 flex gap-2">
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAdd();
              }}
              placeholder={`Add new ${dimensionLabel(dimension).toLowerCase().replace(/s$/, "")}...`}
              className="h-9 max-w-xs text-sm"
            />
            <Button
              size="sm"
              className="h-9 gap-1"
              onClick={handleAdd}
              disabled={adding || !newName.trim()}
            >
              <Plus className="h-4 w-4" />
              Add
            </Button>
          </div>

          {/* Values list */}
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : (
            <div className="rounded-md border border-border">
              {items.map((item, idx) => (
                <div
                  key={item.id}
                  className={`flex items-center gap-3 px-4 py-2.5 ${
                    idx > 0 ? "border-t border-border" : ""
                  }`}
                >
                  {/* Name (or rename input) */}
                  <div className="min-w-0 flex-1">
                    {renamingId === item.id ? (
                      <div className="flex items-center gap-1.5">
                        <Input
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleRename(item.id);
                            if (e.key === "Escape") setRenamingId(null);
                          }}
                          className="h-7 text-sm"
                          autoFocus
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => handleRename(item.id)}
                        >
                          <Check className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => setRenamingId(null)}
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    ) : (
                      <span className="text-sm text-foreground">{item.name}</span>
                    )}
                  </div>

                  {/* Film count */}
                  <Badge variant="secondary" className="shrink-0 text-[11px]">
                    {item.film_count ?? 0}
                  </Badge>

                  {/* Merge UI */}
                  {mergingId === item.id ? (
                    <div className="flex items-center gap-1.5">
                      <Select
                        value={mergeTargetId}
                        onValueChange={setMergeTargetId}
                      >
                        <SelectTrigger className="h-7 w-40 text-xs">
                          <SelectValue placeholder="Merge into..." />
                        </SelectTrigger>
                        <SelectContent>
                          {items
                            .filter((o) => o.id !== item.id)
                            .map((o) => (
                              <SelectItem
                                key={o.id}
                                value={String(o.id)}
                              >
                                {o.name}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7"
                        onClick={() => handleMerge(item.id)}
                        disabled={!mergeTargetId}
                      >
                        <Check className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7"
                        onClick={() => {
                          setMergingId(null);
                          setMergeTargetId("");
                        }}
                      >
                        <X className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  ) : (
                    /* Action buttons */
                    renamingId !== item.id && (
                      <div className="flex shrink-0 gap-1">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-muted-foreground hover:text-foreground"
                          title="Rename"
                          onClick={() => {
                            setRenamingId(item.id);
                            setRenameValue(item.name);
                            setMergingId(null);
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-muted-foreground hover:text-foreground"
                          title="Merge into another"
                          onClick={() => {
                            setMergingId(item.id);
                            setMergeTargetId("");
                            setRenamingId(null);
                          }}
                        >
                          <GitMerge className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-muted-foreground hover:text-destructive"
                          title="Delete"
                          onClick={() => handleDelete(item)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )
                  )}
                </div>
              ))}
              {items.length === 0 && (
                <div className="px-4 py-6 text-center text-sm text-muted-foreground">
                  No values in this dimension
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
