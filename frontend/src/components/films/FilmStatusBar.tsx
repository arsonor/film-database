import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, Heart, Bookmark, List, StickyNote, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StarRating } from "./StarRating";
import { fetchUserLists, fetchFilmListMemberships, addFilmToList, removeFilmFromList } from "@/api/client";
import type { UserFilmStatus } from "@/types/api";

interface FilmStatusBarProps {
  filmId: number;
  status: UserFilmStatus | null;
  onStatusChange: (updated: Partial<UserFilmStatus>) => void;
}

export function FilmStatusBar({ filmId, status, onStatusChange }: FilmStatusBarProps) {
  const seen = status?.seen ?? false;
  const favorite = status?.favorite ?? false;
  const watchlist = status?.watchlist ?? false;
  const rating = status?.rating ?? null;

  const [notesOpen, setNotesOpen] = useState(false);
  const [notesValue, setNotesValue] = useState(status?.notes ?? "");
  const [saved, setSaved] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>();

  const queryClient = useQueryClient();

  const { data: userLists = [] } = useQuery({
    queryKey: ["user-lists"],
    queryFn: fetchUserLists,
  });

  const { data: filmListIds = [] } = useQuery({
    queryKey: ["film-lists", filmId],
    queryFn: () => fetchFilmListMemberships(filmId),
  });

  const handleToggleList = useCallback(async (listId: number, isMember: boolean) => {
    if (isMember) {
      await removeFilmFromList(listId, filmId);
    } else {
      await addFilmToList(listId, filmId);
    }
    queryClient.invalidateQueries({ queryKey: ["film-lists", filmId] });
    queryClient.invalidateQueries({ queryKey: ["user-lists"] });
    queryClient.invalidateQueries({ queryKey: ["list-films"] });
  }, [filmId, queryClient]);

  useEffect(() => {
    setNotesValue(status?.notes ?? "");
  }, [status?.notes]);

  const handleNotesBlur = useCallback(() => {
    const trimmed = notesValue.trim();
    const original = (status?.notes ?? "").trim();
    if (trimmed !== original) {
      onStatusChange({ notes: trimmed || undefined });
      setSaved(true);
      clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => setSaved(false), 2000);
    }
  }, [notesValue, status?.notes, onStatusChange]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        {/* Seen */}
        <Button
          variant={seen ? "default" : "outline"}
          size="sm"
          className={`gap-1.5 ${seen ? "bg-emerald-600 hover:bg-emerald-700" : ""}`}
          onClick={() => onStatusChange({ seen: !seen })}
        >
          {seen ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
          Seen
        </Button>

        {/* Favorite */}
        <Button
          variant={favorite ? "default" : "outline"}
          size="sm"
          className={`gap-1.5 ${favorite ? "bg-rose-600 hover:bg-rose-700" : ""}`}
          onClick={() => onStatusChange({ favorite: !favorite })}
        >
          <Heart className={`h-4 w-4 ${favorite ? "fill-current" : ""}`} />
          Favorite
        </Button>

        {/* Watchlist */}
        <Button
          variant={watchlist ? "default" : "outline"}
          size="sm"
          className={`gap-1.5 ${watchlist ? "bg-amber-600 hover:bg-amber-700" : ""}`}
          onClick={() => onStatusChange({ watchlist: !watchlist })}
        >
          <Bookmark className={`h-4 w-4 ${watchlist ? "fill-current" : ""}`} />
          Watchlist
        </Button>

        {/* Rating */}
        <div className="flex items-center gap-2 rounded-md border border-border px-2 py-1">
          <StarRating
            value={rating}
            onChange={(v) => onStatusChange({ rating: v })}
          />
        </div>

        {/* Notes toggle */}
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-muted-foreground"
          onClick={() => setNotesOpen(!notesOpen)}
        >
          <StickyNote className="h-4 w-4" />
          {notesOpen ? "Hide notes" : notesValue ? "Edit note" : "Add note..."}
        </Button>

        {/* Add to list */}
        {userLists.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground">
                <List className="h-4 w-4" />
                Lists
                {filmListIds.length > 0 && (
                  <span className="rounded-full bg-primary/20 px-1.5 text-[10px] font-bold text-primary">{filmListIds.length}</span>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-48">
              {userLists.map((list) => {
                const isMember = filmListIds.includes(list.list_id);
                return (
                  <DropdownMenuItem
                    key={list.list_id}
                    onClick={() => handleToggleList(list.list_id, isMember)}
                    className="gap-2"
                  >
                    <Check className={`h-3.5 w-3.5 ${isMember ? "text-primary" : "text-transparent"}`} />
                    {list.list_name}
                  </DropdownMenuItem>
                );
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {saved && (
          <span className="text-xs text-emerald-500">Saved</span>
        )}
      </div>

      {/* Notes textarea */}
      {notesOpen && (
        <textarea
          value={notesValue}
          onChange={(e) => setNotesValue(e.target.value)}
          onBlur={handleNotesBlur}
          placeholder="Write a personal note about this film..."
          className="min-h-[80px] w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        />
      )}
    </div>
  );
}
