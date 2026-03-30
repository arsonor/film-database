import { useCallback, useState } from "react";
import { Check, Pencil, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { updateFilm } from "@/api/client";

interface EditableFinancialsProps {
  filmId: number;
  budget: number | null;
  revenue: number | null;
  onSaved: () => void;
}

export function EditableFinancials({
  filmId,
  budget,
  revenue,
  onSaved,
}: EditableFinancialsProps) {
  const [editing, setEditing] = useState(false);
  const [editBudget, setEditBudget] = useState("");
  const [editRevenue, setEditRevenue] = useState("");
  const [saving, setSaving] = useState(false);

  const startEdit = useCallback(() => {
    setEditBudget(budget != null ? String(budget) : "");
    setEditRevenue(revenue != null ? String(revenue) : "");
    setEditing(true);
  }, [budget, revenue]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await updateFilm(filmId, {
        budget: editBudget ? parseInt(editBudget, 10) : null,
        revenue: editRevenue ? parseInt(editRevenue, 10) : null,
      });
      setEditing(false);
      onSaved();
    } catch {
      // Keep editing on error
    } finally {
      setSaving(false);
    }
  }, [filmId, editBudget, editRevenue, onSaved]);

  const handleCancel = useCallback(() => {
    setEditing(false);
  }, []);

  if (!editing) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className="h-5 w-5 text-muted-foreground hover:text-primary"
        onClick={startEdit}
        title="Edit financials"
      >
        <Pencil className="h-3 w-3" />
      </Button>
    );
  }

  return (
    <div className="flex flex-wrap items-end gap-2">
      <div>
        <label className="text-[10px] text-muted-foreground">Budget (USD)</label>
        <Input
          type="number"
          value={editBudget}
          onChange={(e) => setEditBudget(e.target.value)}
          placeholder="160000000"
          className="h-7 w-36 text-xs"
        />
      </div>
      <div>
        <label className="text-[10px] text-muted-foreground">Revenue (USD)</label>
        <Input
          type="number"
          value={editRevenue}
          onChange={(e) => setEditRevenue(e.target.value)}
          placeholder="830000000"
          className="h-7 w-36 text-xs"
        />
      </div>
      <Button
        size="icon"
        onClick={handleSave}
        disabled={saving}
        className="h-7 w-7"
      >
        <Check className="h-3 w-3" />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        onClick={handleCancel}
        disabled={saving}
        className="h-7 w-7"
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
}
