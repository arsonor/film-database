import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function FilmDetailPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background p-8">
      <h1 className="text-2xl font-semibold text-foreground">Film Detail</h1>
      <p className="text-muted-foreground">
        Film #{id} — Coming soon in Step 7
      </p>
      <Button asChild variant="outline">
        <Link to="/browse">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Browse
        </Link>
      </Button>
    </div>
  );
}
