import { useEffect, useRef, useState } from "react";
import { Check, Copy, Home, Link2, RotateCcw, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { saveGameResult } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import type { GameFilm, GamePoolFilters } from "@/types/api";
import { describeFilters } from "./shareCaption";
import type { GuessBoardState } from "./GuessBoard";

function computeStars(tagsRevealed: number, lives: number, victory: boolean): number {
  if (!victory) return 0;
  const tier = tagsRevealed <= 2 ? [5, 4, 3] : tagsRevealed <= 4 ? [4, 3, 2] : [3, 2, 1];
  return tier[3 - lives] ?? 1;
}

interface GuessResultProps {
  grid: GameFilm[];
  targetFilmId: number;
  state: GuessBoardState;
  victory: boolean;
  mode: "daily" | "free";
  difficulty?: "easy" | "medium" | "hard";
  poolFilters?: GamePoolFilters;
  onPlayAgain: () => void;
  onHome: () => void;
}

export function GuessResult({ grid, targetFilmId, state, victory, mode, difficulty, poolFilters, onPlayAgain, onHome }: GuessResultProps) {
  const { isAuthenticated } = useAuth();
  const target = grid.find((f) => f.film_id === targetFilmId);
  const tagsRevealed = state.revealedTags.length;
  const eliminated = state.removedFilmIds.length;
  const stars = computeStars(tagsRevealed, state.lives, victory);
  const [copied, setCopied] = useState(false);
  const saveRef = useRef(false);

  useEffect(() => { window.scrollTo({ top: 0, behavior: "auto" }); }, []);

  const LAUNCH = "2026-05-15";
  const today = new Date().toISOString().slice(0, 10);
  const dayNumber = Math.max(1, Math.floor((Date.parse(today) - Date.parse(LAUNCH)) / 86_400_000) + 1);
  const hearts = "❤️".repeat(state.lives) + "🖤".repeat(3 - state.lives);
  const starsLine = stars > 0 ? "⭐".repeat(stars) : "💀";
  const status = victory
    ? `🎯 Guessed in ${tagsRevealed} tags (${eliminated} eliminated)`
    : `❌ Game over after ${tagsRevealed} tags`;
  const filtersLine = mode === "free" ? describeFilters(difficulty ?? null, poolFilters) : "";
  const filtersBlock = filtersLine ? `\n${filtersLine}` : "";
  const shareText = mode === "daily"
    ? `🔍 CineTag Guess It #${dayNumber}\n${status}\n${hearts}\n${starsLine}\nhttps://cinetag.eu/game`
    : `🔍 CineTag Guess It — Free Play\n${status}\n${hearts}\n${starsLine}${filtersBlock}\nhttps://cinetag.eu/game`;

  useEffect(() => {
    if (saveRef.current) return;

    if (mode === "daily" && target) {
      try {
        localStorage.setItem(
          "guessit_daily_result",
          JSON.stringify({
            challenge_date: today,
            film_id: target.film_id,
            tags_used: tagsRevealed,
            lives_remaining: state.lives,
            jokers_used: state.jokersUsed,
            stars,
            completed: victory,
          }),
        );
      } catch {}
    }

    if (!isAuthenticated || !target) return;
    saveRef.current = true;
    saveGameResult({
      mode,
      film_id: target.film_id,
      challenge_date: mode === "daily" ? today : null,
      tags_used: tagsRevealed,
      lives_remaining: state.lives,
      jokers_used: state.jokersUsed,
      stars,
      tag_sequence: state.actionLog as any,
      completed: victory,
      difficulty: mode === "free" ? difficulty ?? null : null,
      pool_filters: mode === "free" ? poolFilters ?? null : null,
    }, "guess_it").catch((e) => console.error("[Guess It] save failed", e));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function copyShare() {
    navigator.clipboard.writeText(shareText).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-6 px-4 py-10 text-center">
      <h2 className="text-3xl font-bold sm:text-4xl">
        {victory ? "🎉 You guessed it!" : "💀 Game over"}
      </h2>

      {target?.poster_url && (
        <img
          src={target.poster_url}
          alt={target.title}
          className={cn(
            "h-64 w-44 rounded-lg object-cover shadow-2xl",
            victory ? "animate-victory ring-2 ring-amber-400/60 shadow-amber-400/30" : "opacity-60",
          )}
        />
      )}

      {target && (
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">The hidden film was</div>
          <div className="text-xl font-semibold">{target.title}</div>
          <div className="text-sm text-muted-foreground">{target.year ?? ""}</div>
        </div>
      )}

      {victory && (
        <div className="flex gap-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star key={i} className={cn("h-7 w-7", i < stars ? "fill-amber-400 text-amber-400" : "fill-none text-muted-foreground/30")} />
          ))}
        </div>
      )}

      <div className="grid w-full grid-cols-3 gap-3 rounded-lg border border-border bg-muted/20 p-4 text-sm">
        <div><div className="text-2xl font-bold">{tagsRevealed}</div><div className="text-xs text-muted-foreground">Tags revealed</div></div>
        <div><div className="text-2xl font-bold">{eliminated}</div><div className="text-xs text-muted-foreground">Films eliminated</div></div>
        <div><div className="text-2xl font-bold">{state.lives}/3</div><div className="text-xs text-muted-foreground">Lives left</div></div>
      </div>

      {state.revealedTags.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1">
          {state.revealedTags.map((t, i) => (
            <span key={i} className="rounded-md border border-amber-400/50 bg-amber-400/10 px-2 py-0.5 text-[11px] text-amber-300">
              {t.display}
            </span>
          ))}
        </div>
      )}

      <pre className="w-full whitespace-pre-wrap rounded-md border border-border bg-background px-4 py-3 text-left text-sm font-mono">
        {shareText}
      </pre>

      <div className="flex flex-wrap gap-2">
        <Button onClick={copyShare} variant="outline" className="gap-2">
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          {copied ? "Copied!" : "Copy share"}
        </Button>
        <Button onClick={onPlayAgain} className="gap-2">
          <RotateCcw className="h-4 w-4" /> Play again
        </Button>
        <Button variant="ghost" onClick={onHome} className="gap-2">
          <Home className="h-4 w-4" /> Games
        </Button>
        {isAuthenticated && (
          <Button variant="ghost" onClick={() => (window.location.href = "/game/stats")} className="gap-2">
            <Link2 className="h-4 w-4" /> View all stats →
          </Button>
        )}
      </div>

      {!isAuthenticated && (
        <p className="text-xs text-muted-foreground">Sign in to save your scores and track streaks.</p>
      )}
    </div>
  );
}
