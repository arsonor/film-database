import { useCallback, useState } from "react";
import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionHeading } from "./SectionHeading";
import { updateFilm } from "@/api/client";
import { formatCurrency } from "@/lib/utils";

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

  return (
    <div>
      <SectionHeading
        title="Financials"
        onEdit={startEdit}
        editing={editing}
      />

      {!editing ? (
        <div className="space-y-1 text-sm">
          <p>
            <span className="text-muted-foreground">Budget: </span>
            <span className="text-foreground">{formatCurrency(budget)}</span>
          </p>
          <p>
            <span className="text-muted-foreground">Revenue: </span>
            <span className="text-foreground">{formatCurrency(revenue)}</span>
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground">Budget (USD)</label>
            <Input
              type="number"
              value={editBudget}
              onChange={(e) => setEditBudget(e.target.value)}
              placeholder="e.g. 160000000"
              className="h-8"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground">Revenue (USD)</label>
            <Input
              type="number"
              value={editRevenue}
              onChange={(e) => setEditRevenue(e.target.value)}
              placeholder="e.g. 830000000"
              className="h-8"
            />
          </div>
          <div className="flex gap-2">
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
