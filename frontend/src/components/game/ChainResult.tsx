import { useEffect, useRef, useState } from "react";
import { Check, ChevronRight, Copy, Home, Link2, RotateCcw, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { saveChainResult } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import type { ChainFilm, ChainOrigin } from "@/types/api";
import type { ChainBoardState } from "./ChainBoard";

function computeStars(chainLen: number, lives: number, victory: boolean): number {
  if (!victory) return 0;
  const tier = chainLen <= 3 ? [5, 4, 3] : chainLen <= 5 ? [4, 3, 2] : [3, 2, 1];
  return tier[3 - lives] ?? 1;
}

interface ChainResultProps {
  origin: ChainOrigin;
  target: ChainFilm;
  state: ChainBoardState;
  victory: boolean;
  mode: "daily" | "free";
  onPlayAgain: () => void;
  onHome: () => void;
}

export function ChainResult({ origin, target, state, victory, mode, onPlayAgain, onHome }: ChainResultProps) {
  const { isAuthenticated } = useAuth();
  const chainLen = state.steps.length;
  const stars = computeStars(chainLen, state.lives, victory);
  const jokersUsed = 3 - state.jokers.reveal;
  const [copied, setCopied] = useState(false);
  const saveRef = useRef(false);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, []);

  const LAUNCH = "2026-05-15";
  const today = new Date().toISOString().slice(0, 10);
  const dayNumber = Math.max(1, Math.floor((Date.parse(today) - Date.parse(LAUNCH)) / 86_400_000) + 1);
  const hearts = "❤️".repeat(state.lives) + "🖤".repeat(3 - state.lives);
  const starsLine = stars > 0 ? "⭐".repeat(stars) : "💀";
  const chainTitles = [origin.title, ...state.steps.map((s) => s.film.title), ...(victory ? [target.title] : [])];
  const shareText = mode === "daily"
    ? `🔗 CineTag Chain #${dayNumber}\n🎬 ${chainTitles.join(" → ")}\n📏 ${chainLen} steps | ${hearts} | ${starsLine}\nhttps://cinetag.eu/game`
    : `🔗 CineTag Chain — Free Play\n🎬 ${chainTitles.join(" → ")}\n📏 ${chainLen} steps | ${hearts} | ${starsLine}\nhttps://cinetag.eu/game`;

  useEffect(() => {
    if (saveRef.current) return;

    // Anonymous daily: record locally so the player can't replay today.
    if (mode === "daily") {
      try {
        localStorage.setItem(
          "chainit_daily_result",
          JSON.stringify({
            challenge_date: today,
            origin_film_id: origin.film_id,
            target_film_id: target.film_id,
            chain_length: chainLen,
            lives_remaining: state.lives,
            jokers_used: jokersUsed,
            stars,
            completed: victory,
          }),
        );
      } catch {}
    }

    if (!isAuthenticated) return;
    saveRef.current = true;
    saveChainResult({
      mode,
      origin_film_id: origin.film_id,
      target_film_id: target.film_id,
      chain_length: chainLen,
      lives_remaining: state.lives,
      jokers_used: jokersUsed,
      stars,
      tag_sequence: state.sequence,
      completed: victory,
    }).catch((e) => console.error("[Chain It] save failed", e));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function copyShare() {
    navigator.clipboard.writeText(shareText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-4 py-10 text-center">
      <h2 className="text-3xl font-bold sm:text-4xl">
        {victory ? "🎉 Chain complete!" : "💀 Out of lives"}
      </h2>

      <div className="w-full overflow-x-auto">
        <div className="mx-auto flex w-max items-center gap-2 px-1 py-2">
        <ChainPoster film={origin} label="Origin" />
        {state.steps.map((s, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <div className="flex flex-col items-center">
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              {s.via_tag && (
                <span className="rounded bg-emerald-500/15 px-1 text-[10px] text-emerald-300">{s.via_tag.value}</span>
              )}
            </div>
            <ChainPoster film={s.film} />
          </div>
        ))}
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
        <ChainPoster film={target} label="Target" dim={!victory} />
        </div>
        <div className="mt-1 text-center text-[10px] text-muted-foreground sm:hidden">← swipe to see the full chain →</div>
      </div>

      {victory && (
        <div className="flex gap-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star key={i} className={cn("h-7 w-7", i < stars ? "fill-amber-400 text-amber-400" : "fill-none text-muted-foreground/30")} />
          ))}
        </div>
      )}

      <div className="grid w-full grid-cols-3 gap-3 rounded-lg border border-border bg-muted/20 p-4 text-sm">
        <div><div className="text-2xl font-bold">{chainLen}</div><div className="text-xs text-muted-foreground">Steps</div></div>
        <div><div className="text-2xl font-bold">{state.lives}/3</div><div className="text-xs text-muted-foreground">Lives left</div></div>
        <div><div className="text-2xl font-bold">{jokersUsed}/3</div><div className="text-xs text-muted-foreground">Jokers used</div></div>
      </div>

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

function ChainPoster({ film, label, dim }: { film: ChainFilm; label?: string; dim?: boolean }) {
  return (
    <div className={cn("flex flex-col items-center gap-1", dim && "opacity-60")}>
      {label && <span className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</span>}
      <div className="h-24 w-16 overflow-hidden rounded border border-border bg-muted">
        {film.poster_url && <img src={film.poster_url} alt={film.title} className="h-full w-full object-cover" />}
      </div>
      <div className="line-clamp-2 max-w-[80px] text-center text-[10px]">{film.title}</div>
    </div>
  );
}
