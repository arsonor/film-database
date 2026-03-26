import { useNavigate } from "react-router-dom";
import { User } from "lucide-react";
import { formatPersonName, tmdbImageUrl } from "@/lib/utils";

interface PersonCardProps {
  personId: number;
  firstname: string | null;
  lastname: string;
  role: string;
  photoUrl: string | null;
  size?: "sm" | "md";
}

export function PersonCard({
  firstname,
  lastname,
  role,
  photoUrl,
  size = "md",
}: PersonCardProps) {
  const navigate = useNavigate();
  const fullName = formatPersonName(firstname, lastname);
  const imgUrl = tmdbImageUrl(photoUrl, "w185");
  const imgSize = size === "sm" ? "h-14 w-14" : "h-20 w-20";

  return (
    <button
      onClick={() => navigate(`/browse?q=${encodeURIComponent(fullName)}`)}
      className="flex flex-col items-center gap-1.5 rounded-lg p-2 transition-colors hover:bg-card"
      title={`Browse films with ${fullName}`}
    >
      {imgUrl ? (
        <img
          src={imgUrl}
          alt={fullName}
          className={`${imgSize} rounded-full object-cover shadow-md`}
          loading="lazy"
        />
      ) : (
        <div className={`${imgSize} flex items-center justify-center rounded-full bg-muted`}>
          <User className="h-5 w-5 text-muted-foreground" />
        </div>
      )}
      <span className="max-w-[90px] truncate text-xs font-medium text-foreground">
        {fullName}
      </span>
      <span className="max-w-[90px] truncate text-[10px] text-muted-foreground">
        {role}
      </span>
    </button>
  );
}
