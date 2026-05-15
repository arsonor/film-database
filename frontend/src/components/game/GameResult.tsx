import { useEffect, useRef, useState } from "react";
import { Check, Copy, Home, RotateCcw, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchFilmDetail, saveGameResult } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import type { FilmDetail, GameFilm } from "@/types/api";
import { DIMENSION_LABELS, DIMENSION_SQUARES, GAME_DIMENSIONS, type GameDimension } from "./dimensions";
import type { GameState } from "./GameBoard";

interface GameResultProps {
  target: GameFilm;
  state: GameState;
  victory: boolean;
  mode: "daily" | "free";
  onPlayAgain: () => void;
  onHome: () => void;
}

function computeStars(tagsUsed: number, lives: number, victory: boolean): number {
  if (!victory) return 0;
  // 3-4 tags: 5/4/3, 5-6 tags: 4/3/2, 7+: 3/2/1
  const tier = tagsUsed <= 4 ? [5, 4, 3] : tagsUsed <= 6 ? [4, 3, 2] : [3, 2, 1];
  return tier[3 - lives] ?? 1;
}

export function GameResult({ target, state, victory, mode, onPlayAgain, onHome }: GameResultProps) {
  const { isAuthenticated } = useAuth();
  const correctTags = state.played.filter((t) => t.correct);
  const tagsUsed = correctTags.length;
  const jokersUsed = 3 - (state.jokers.remaining + state.jokers.hint + state.jokers.synopsis);
  const stars = computeStars(tagsUsed, state.lives, victory);
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const saveStartedRef = useRef(false);
  const [revealed, setRevealed] = useState<FilmDetail | null>(null);

  useEffect(() => {
    fetchFilmDetail(target.film_id).then(setRevealed).catch(() => {});
  }, [target.film_id]);

  // Build share text. Day #1 = launch date 2026-05-13.
  const today = new Date().toISOString().slice(0, 10);
  const LAUNCH = "2026-05-13";
  const dayNumber = Math.max(1, Math.floor((Date.parse(today) - Date.parse(LAUNCH)) / 86_400_000) + 1);
  const heartsLine = "❤️".repeat(state.lives) + "🖤".repeat(3 - state.lives);
  const starsLine = "⭐".repeat(stars) + (stars > 0 ? "" : "💀");
  const dimSquaresLine = correctTags
    .map((t) => DIMENSION_SQUARES[t.dimension as GameDimension] ?? "⬛")
    .join("");
  const lifelinesLine = `💡 ${jokersUsed}/3 lifelines used`;
  const shareText =
    mode === "daily"
      ? `🎬 Tag It Daily #${dayNumber}\n🎯 ${victory ? `Found in ${tagsUsed} tags` : "Failed"}\n${heartsLine}\n${starsLine}\n${lifelinesLine}\n${dimSquaresLine}\nhttps://cinetag.eu/game`
      : `🎬 Tag It — Free Play\n🎯 ${victory ? `Found "${target.title}" in ${tagsUsed} tags` : "Failed"}\n${heartsLine}\n${starsLine}\n${lifelinesLine}\n${dimSquaresLine}\nhttps://cinetag.eu/game`;

  // Save result exactly once per mount. useRef survives React strict-mode
  // double-invocation (state guards don't, because both closures capture saved=false).
  useEffect(() => {
    if (saveStartedRef.current) return;

    // Always record anonymous daily result in localStorage so we can block replay.
    if (mode === "daily") {
      try {
        localStorage.setItem(
          "tagit_daily_result",
          JSON.stringify({
            challenge_date: today,
            film_id: target.film_id,
            tags_used: tagsUsed,
            lives_remaining: state.lives,
            jokers_used: jokersUsed,
            stars,
            completed: victory,
          }),
        );
      } catch {}
    }

    if (!isAuthenticated) return;
    saveStartedRef.current = true;
    const payload = {
      mode,
      film_id: target.film_id,
      challenge_date: mode === "daily" ? today : null,
      tags_used: tagsUsed,
      lives_remaining: state.lives,
      jokers_used: jokersUsed,
      stars,
      tag_sequence: state.played.map((t) => ({
        dimension: t.dimension,
        value: t.value,
        remaining: t.remaining,
        correct: t.correct,
      })),
      completed: victory,
    };
    console.log("[Tag It] saving result", payload);
    saveGameResult(payload)
      .then((r) => {
        console.log("[Tag It] save OK", r);
        setSaved(true);
      })
      .catch((err) => {
        console.error("[Tag It] save FAILED", err?.status, err?.message, err);
        if (err?.status === 409) setSaved(true);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function copyShare() {
    navigator.clipboard.writeText(shareText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-6 px-4 py-10 text-center">
      <h2 className="text-3xl font-bold sm:text-4xl">
        {victory ? "🎉 You got it!" : "💀 Game over"}
      </h2>

      {target.poster_url && (
        <img
          src={target.poster_url}
          alt={target.title}
          className={`h-64 w-44 rounded-lg object-cover shadow-2xl ${
            victory ? "animate-victory ring-2 ring-amber-400/60 shadow-amber-400/30" : "opacity-50 grayscale"
          }`}
        />
      )}

      <div>
        <div className="text-xl font-semibold">{target.title}</div>
        <div className="text-sm text-muted-foreground">{target.year ?? ""}</div>
      </div>

      {victory && (
        <div className="flex gap-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              className={`h-7 w-7 ${i < stars ? "fill-amber-400 text-amber-400" : "fill-none text-muted-foreground/30"}`}
            />
          ))}
        </div>
      )}

      <div className="grid w-full grid-cols-3 gap-3 rounded-lg border border-border bg-muted/20 p-4 text-sm">
        <div>
          <div className="text-2xl font-bold">{tagsUsed}</div>
          <div className="text-xs text-muted-foreground">Tags used</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{state.lives}/3</div>
          <div className="text-xs text-muted-foreground">Lives left</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{jokersUsed}/3</div>
          <div className="text-xs text-muted-foreground">Jokers used</div>
        </div>
      </div>

      <pre className="whitespace-pre-wrap rounded-md border border-border bg-background px-4 py-3 text-sm font-mono">
        {shareText}
      </pre>

      {/* Reveal all of the target film's tags */}
      {revealed && (
        <div className="w-full text-left">
          <h3 className="mb-3 text-center text-base font-semibold">
            All tags for <span className="text-primary">{target.title}</span>
          </h3>
          <div className="space-y-2">
            {GAME_DIMENSIONS.map((dim) => {
              const filmTags = (revealed[dim as keyof FilmDetail] as string[] | undefined) ?? [];
              const wrongTags = state.played
                .filter((t) => !t.correct && t.dimension === dim)
                .map((t) => t.value);
              // Show the dimension row if the film has tags OR the user picked wrong ones in it
              if (filmTags.length === 0 && wrongTags.length === 0) return null;
              const playedCorrect = new Set(
                state.played.filter((t) => t.correct && t.dimension === dim).map((t) => t.value),
              );
              const wrongNotInFilm = wrongTags.filter((t) => !filmTags.includes(t));
              return (
                <div key={dim} className="rounded-md border border-border bg-muted/20 p-2">
                  <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {DIMENSION_LABELS[dim as GameDimension]}
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {filmTags.map((tag) => {
                      const isCorrect = playedCorrect.has(tag);
                      return (
                        <span
                          key={tag}
                          className={cn(
                            "rounded-md border px-2 py-0.5 text-xs",
                            isCorrect
                              ? "border-emerald-500 bg-emerald-500/20 text-emerald-300"
                              : "border-border bg-background text-muted-foreground",
                          )}
                        >
                          {tag}
                        </span>
                      );
                    })}
                    {wrongNotInFilm.map((tag) => (
                      <span
                        key={`wrong-${tag}`}
                        className="rounded-md border border-red-500 bg-red-500/15 px-2 py-0.5 text-xs text-red-400 line-through"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
          <p className="mt-3 text-center text-[10px] text-muted-foreground">
            <span className="text-emerald-400">●</span> picked correctly &nbsp;·&nbsp;
            <span className="text-red-400">●</span> picked wrong (target didn't have it) &nbsp;·&nbsp;
            <span className="text-muted-foreground">●</span> never picked
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Button onClick={copyShare} variant="outline" className="gap-2">
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          {copied ? "Copied!" : "Copy share"}
        </Button>
        <Button onClick={onPlayAgain} className="gap-2">
          <RotateCcw className="h-4 w-4" /> Play again
        </Button>
        <Button variant="ghost" onClick={onHome} className="gap-2">
          <Home className="h-4 w-4" /> Home
        </Button>
      </div>

      {!isAuthenticated && (
        <p className="text-xs text-muted-foreground">Sign in to save your scores and track streaks.</p>
      )}
    </div>
  );
}
