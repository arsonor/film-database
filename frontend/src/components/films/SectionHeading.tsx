import { Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SectionHeadingProps {
  title: string;
  onEdit?: () => void;
  editing?: boolean;
}

export function SectionHeading({ title, onEdit, editing }: SectionHeadingProps) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>
      {onEdit && (
        <Button
          variant="ghost"
          size="icon"
          className={`h-7 w-7 ${editing ? "text-primary" : "text-muted-foreground hover:text-primary"}`}
          onClick={onEdit}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}
