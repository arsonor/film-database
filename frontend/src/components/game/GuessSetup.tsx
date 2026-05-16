import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Calendar, Loader2, Lock, LogIn, Play, Shuffle, Star, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { fetchGuessDaily, fetchGuessRandom, fetchTaxonomy } from "@/api/client";
import type { AlreadyPlayedDaily, GamePoolFilters, GuessSetupResponse } from "@/types/api";
import { cn } from "@/lib/utils";
import {
  buildPoolFilters, DecadeRangePicker, LanguagePicker, NO_RANGE, rangeToFilters, type DecadeRange,
} from "./freePlayFilters";

interface GuessSetupProps {
  onStart: (
    mode: "daily" | "free",
    setup: GuessSetupResponse,
    poolFilters?: GamePoolFilters,
    difficulty?: "easy" | "medium" | "hard",
    decadeLocked?: boolean,
  ) => void;
}

export function GuessSetup({ onStart }: GuessSetupProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [mode, setMode] = useState<"daily" | "free">("daily");
  const [decadeRange, setDecadeRange] = useState<DecadeRange>(NO_RANGE);
  const [language, setLanguage] = useState("");
  const [languages, setLanguages] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [setup, setSetup] = useState<GuessSetupResponse | null>(null);
  const [alreadyPlayed, setAlreadyPlayed] = useState<AlreadyPlayedDaily | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTaxonomy("languages").then((t) => {
      setLanguages(t.items.map((i) => i.name));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (mode !== "daily") return;
    const todayISO = new Date().toISOString().slice(0, 10);
    if (isAuthenticated) {
      fetchGuessDaily().then((s) => {
        if (s.already_played) {
          setAlreadyPlayed(s.already_played);
          setSetup(s);
        }
      }).catch(() => {});
    } else {
      try {
        const raw = localStorage.getItem("guessit_daily_result");
        if (!raw) return;
        const r = JSON.parse(raw);
        if (r?.challenge_date === todayISO) {
          setAlreadyPlayed({
            film_id: r.film_id,
            tags_used: r.tags_used,
            lives_remaining: r.lives_remaining,
            jokers_used: r.jokers_used,
            stars: r.stars,
            tag_sequence: null,
            completed: r.completed,
            played_at: null,
          });
        }
      } catch {}
    }
  }, [mode, isAuthenticated]);

  function checkLocalDaily(): AlreadyPlayedDaily | null {
    try {
      const raw = localStorage.getItem("guessit_daily_result");
      if (!raw) return null;
      const r = JSON.parse(raw);
      const todayISO = new Date().toISOString().slice(0, 10);
      if (r?.challenge_date !== todayISO) return null;
      return {
        film_id: r.film_id, tags_used: r.tags_used, lives_remaining: r.lives_remaining,
        jokers_used: r.jokers_used, stars: r.stars, tag_sequence: null,
        completed: r.completed, played_at: null,
      };
    } catch { return null; }
  }

  async function handleStart() {
    setError(null);
    setLoading(true);
    try {
      if (mode === "daily" && !isAuthenticated) {
        const local = checkLocalDaily();
        if (local) {
          setAlreadyPlayed(local);
          return;
        }
      }
      const filters: GamePoolFilters = mode === "free" ? buildPoolFilters(decadeRange, language) : {};
      const s = mode === "daily" ? await fetchGuessDaily() : await fetchGuessRandom(filters, difficulty);
      if (mode === "daily" && s.already_played) {
        setAlreadyPlayed(s.already_played);
        setSetup(s);
      } else {
        const yearBounds = rangeToFilters(decadeRange);
        const decadeLocked = mode === "free" && (yearBounds.year_min != null || yearBounds.year_max != null);
        onStart(mode, s, mode === "free" ? filters : undefined, mode === "free" ? difficulty : "medium", decadeLocked);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  const freePlayLocked = mode === "free" && !isAuthenticated;

  return (
    <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-4 py-8">
      <Link to="/game" className="self-start inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Games
      </Link>

      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">🔍 Guess It</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Eliminate films as tags are revealed. Find the hidden one.
        </p>
      </div>

      <div className="flex rounded-md border border-border bg-muted/30 p-1">
        <button
          onClick={() => { setMode("daily"); setSetup(null); }}
          className={cn("flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium",
            mode === "daily" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
        >
          <Calendar className="h-4 w-4" /> Daily
        </button>
        <button
          onClick={() => { setMode("free"); setSetup(null); setAlreadyPlayed(null); }}
          className={cn("flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium",
            mode === "free" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
        >
          <Shuffle className="h-4 w-4" /> Free play
          {!isAuthenticated && <Lock className="h-3 w-3 text-amber-500" />}
        </button>
      </div>

      {freePlayLocked && (
        <div className="flex max-w-md flex-col items-center gap-3 rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-center text-sm">
          <p className="font-medium text-amber-300">Free play requires a free account.</p>
          <Button size="sm" onClick={() => navigate("/auth")} className="gap-2">
            <LogIn className="h-4 w-4" /> Sign in / Sign up
          </Button>
        </div>
      )}

      {mode === "free" && isAuthenticated && (
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Difficulty:</span>
            {(["easy", "medium", "hard"] as const).map((d) => (
              <button
                key={d}
                onClick={() => setDifficulty(d)}
                className={cn(
                  "rounded-md border px-3 py-1 text-xs font-medium capitalize",
                  difficulty === d
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border text-muted-foreground hover:text-foreground",
                )}
                title={
                  d === "easy" ? "Less similar decoys — easier to spot the target"
                    : d === "hard" ? "Very similar decoys — close-call eliminations"
                    : "Mixed decoys — balanced"
                }
              >
                {d}
              </button>
            ))}
          </div>
          <DecadeRangePicker range={decadeRange} onChange={setDecadeRange} />
          <LanguagePicker value={language} available={languages} onChange={setLanguage} />
        </div>
      )}

      {alreadyPlayed && (
        <div className="flex w-full max-w-md flex-col items-center gap-3 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-center">
          <Trophy className="h-8 w-8 text-emerald-400" />
          <p className="text-base font-semibold">You've already played today's Guess It!</p>
          <div className="flex items-center gap-3 text-sm">
            <span>{alreadyPlayed.tags_used} tags</span>
            <span className="text-muted-foreground">•</span>
            <span className="flex items-center gap-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star key={i} className={`h-4 w-4 ${i < alreadyPlayed.stars ? "fill-amber-400 text-amber-400" : "fill-none text-muted-foreground/30"}`} />
              ))}
            </span>
          </div>
          <Button onClick={() => { setMode("free"); setSetup(null); setAlreadyPlayed(null); }} variant="outline" size="sm">
            Play Free
          </Button>
        </div>
      )}

      {!alreadyPlayed && !freePlayLocked && (
        <Button size="lg" onClick={handleStart} disabled={loading} className="gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Start
        </Button>
      )}

      {error && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {setup && !alreadyPlayed && (
        <p className="text-xs text-muted-foreground">Loading grid…</p>
      )}
    </div>
  );
}
