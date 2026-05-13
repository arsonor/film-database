import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Calendar, Loader2, Lock, LogIn, Play, Shuffle, Star, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/context/AuthContext";
import { fetchDailyChallenge, fetchGameStats, fetchRandomFilms, fetchTaxonomy } from "@/api/client";
import type {
  AlreadyPlayedDaily, GameFilm, GamePoolFilters, GameSetupResponse, GameStats,
} from "@/types/api";
import { cn } from "@/lib/utils";

interface GameSetupProps {
  onStart: (mode: "daily" | "free", setup: GameSetupResponse, target: GameFilm, poolFilters?: GamePoolFilters) => void;
}

const DECADES = [
  { label: "All", min: null, max: null },
  { label: "1950s", min: 1950, max: 1959 },
  { label: "1960s", min: 1960, max: 1969 },
  { label: "1970s", min: 1970, max: 1979 },
  { label: "1980s", min: 1980, max: 1989 },
  { label: "1990s", min: 1990, max: 1999 },
  { label: "2000s", min: 2000, max: 2009 },
  { label: "2010s", min: 2010, max: 2019 },
  { label: "2020s", min: 2020, max: 2029 },
] as const;

export function GameSetup({ onStart }: GameSetupProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [mode, setMode] = useState<"daily" | "free">("daily");
  const [decadeIdx, setDecadeIdx] = useState(0);
  const [language, setLanguage] = useState<string>("");
  const [languages, setLanguages] = useState<{ name: string; code: string }[]>([]);
  const [setup, setSetup] = useState<GameSetupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alreadyPlayed, setAlreadyPlayed] = useState<AlreadyPlayedDaily | null>(null);
  const [stats, setStats] = useState<GameStats | null>(null);

  useEffect(() => {
    fetchTaxonomy("languages").then((t) => {
      setLanguages(t.items.slice(0, 30).map((i) => ({ name: i.name, code: i.name })));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchGameStats().then(setStats).catch(() => {});
    } else {
      setStats(null);
    }
  }, [isAuthenticated]);

  // On mount: if the user already played today's daily, show the panel immediately.
  // Anonymous → localStorage; Authenticated → backend already_played.
  useEffect(() => {
    if (mode !== "daily") return;
    const todayISO = new Date().toISOString().slice(0, 10);

    if (isAuthenticated) {
      fetchDailyChallenge().then((s) => {
        if (s.already_played) {
          setAlreadyPlayed(s.already_played);
          setSetup(s);
        }
      }).catch(() => {});
    } else {
      try {
        const raw = localStorage.getItem("tagit_daily_result");
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

  const poolFilters: GamePoolFilters | undefined = useMemo(() => {
    if (mode !== "free") return undefined;
    const d = DECADES[decadeIdx];
    const f: GamePoolFilters = {};
    if (!d) return f;
    if (d.min != null) f.year_min = d.min;
    if (d.max != null) f.year_max = d.max;
    if (language) f.language = language;
    return f;
  }, [mode, decadeIdx, language]);

  function checkLocalDaily(): AlreadyPlayedDaily | null {
    try {
      const raw = localStorage.getItem("tagit_daily_result");
      if (!raw) return null;
      const r = JSON.parse(raw);
      const todayISO = new Date().toISOString().slice(0, 10);
      if (r?.challenge_date !== todayISO) return null;
      return {
        film_id: r.film_id,
        tags_used: r.tags_used,
        lives_remaining: r.lives_remaining,
        jokers_used: r.jokers_used,
        stars: r.stars,
        tag_sequence: null,
        completed: r.completed,
        played_at: null,
      };
    } catch { return null; }
  }

  async function handleStart() {
    setError(null);
    setLoading(true);
    try {
      // Anonymous daily — block via localStorage even if user navigated back here
      if (mode === "daily" && !isAuthenticated) {
        const local = checkLocalDaily();
        if (local) {
          setAlreadyPlayed(local);
          setSetup({ films: [], pool_size: 0, mode: "daily" });
          return;
        }
      }
      const s = mode === "daily"
        ? await fetchDailyChallenge()
        : await fetchRandomFilms(poolFilters ?? {});
      if (mode === "daily" && s.already_played) {
        setAlreadyPlayed(s.already_played);
        setSetup(s);
      } else {
        setAlreadyPlayed(null);
        setSetup(s);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load films";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function handlePickTarget(film: GameFilm) {
    if (!setup) return;
    onStart(mode, setup, film, poolFilters);
  }

  const freePlayLocked = mode === "free" && !isAuthenticated;

  return (
    <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-4 py-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">🎬 Tag It</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Isolate the film using as few tags as possible.
        </p>
      </div>

      {/* Stats — two clean blocks: Daily / Free */}
      {isAuthenticated && stats && (stats.daily.games > 0 || stats.free.games > 0) && (
        <div className="grid w-full max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2">
          {stats.daily.games > 0 && (
            <div className="rounded-lg border border-border bg-muted/20 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Calendar className="h-3.5 w-3.5" /> Daily
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <Stat label="Played" value={stats.daily.games} />
                <Stat label="Wins" value={stats.daily.wins} />
                <Stat label="Avg ⭐" value={stats.daily.avg_stars.toFixed(1)} />
                <Stat label="Best ⭐" value={stats.daily.best_stars} />
                <Stat label="Best tags" value={stats.daily.best_tags ?? "—"} />
                <Stat label="Streak" value={`🔥 ${stats.daily.current_streak}`} />
              </div>
              {stats.daily.max_streak > stats.daily.current_streak && (
                <div className="mt-2 text-center text-[10px] text-muted-foreground">
                  Best streak: 🏆 {stats.daily.max_streak}
                </div>
              )}
            </div>
          )}
          {stats.free.games > 0 && (
            <div className="rounded-lg border border-border bg-muted/20 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Shuffle className="h-3.5 w-3.5" /> Free play
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <Stat label="Played" value={stats.free.games} />
                <Stat label="Wins" value={stats.free.wins} />
                <Stat label="Avg ⭐" value={stats.free.avg_stars.toFixed(1)} />
                <Stat label="Best ⭐" value={stats.free.best_stars} />
                <Stat label="Best tags" value={stats.free.best_tags ?? "—"} />
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex rounded-md border border-border bg-muted/30 p-1">
        <button
          onClick={() => {
            setMode("daily");
            setSetup(null);
            // do NOT clear alreadyPlayed — mount-useEffect will refresh it
          }}
          className={cn(
            "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
            mode === "daily" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          <Calendar className="h-4 w-4" /> Daily
        </button>
        <button
          onClick={() => { setMode("free"); setSetup(null); setAlreadyPlayed(null); }}
          className={cn(
            "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
            mode === "free" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          <Shuffle className="h-4 w-4" /> Free play
          {!isAuthenticated && <Lock className="h-3 w-3 text-amber-500" />}
        </button>
      </div>

      {freePlayLocked && (
        <div className="flex max-w-md flex-col items-center gap-3 rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-center text-sm">
          <p className="font-medium text-amber-300">Free play requires a free account.</p>
          <p className="text-xs text-muted-foreground">
            Sign up for free to unlock unlimited rounds, decade & language filters, and stats tracking.
          </p>
          <Button size="sm" onClick={() => navigate("/auth")} className="gap-2">
            <LogIn className="h-4 w-4" /> Sign in / Sign up
          </Button>
        </div>
      )}

      {mode === "free" && isAuthenticated && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          <div className="flex flex-wrap gap-1">
            {DECADES.map((d, i) => (
              <button
                key={d.label}
                onClick={() => setDecadeIdx(i)}
                className={cn(
                  "rounded-md border px-2 py-1 text-xs font-medium",
                  decadeIdx === i
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border text-muted-foreground hover:text-foreground",
                )}
              >
                {d.label}
              </button>
            ))}
          </div>
          <Select value={language || "any"} onValueChange={(v) => setLanguage(v === "any" ? "" : v)}>
            <SelectTrigger className="h-9 w-44 text-xs">
              <SelectValue placeholder="Any language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Any language</SelectItem>
              {languages.map((l) => (
                <SelectItem key={l.code} value={l.code}>{l.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {alreadyPlayed && (
        <div className="flex w-full max-w-md flex-col items-center gap-3 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-center">
          <Trophy className="h-8 w-8 text-emerald-400" />
          <p className="text-base font-semibold">You've already played today's daily!</p>
          <div className="flex items-center gap-3 text-sm">
            <span>{alreadyPlayed.tags_used} tags</span>
            <span className="text-muted-foreground">•</span>
            <span className="flex items-center gap-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`h-4 w-4 ${i < alreadyPlayed.stars ? "fill-amber-400 text-amber-400" : "fill-none text-muted-foreground/30"}`}
                />
              ))}
            </span>
          </div>
          <Button onClick={() => { setMode("free"); setSetup(null); setAlreadyPlayed(null); }} variant="outline" size="sm">
            Play Free
          </Button>
        </div>
      )}

      {!setup && !alreadyPlayed && !freePlayLocked && (
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
        <div className="w-full">
          <p className="mb-4 text-center text-sm text-muted-foreground">
            Pick the film you know best — pool size: {setup.pool_size.toLocaleString()}
          </p>
          <div className="grid grid-cols-3 gap-4">
            {setup.films.map((f) => (
              <button
                key={f.film_id}
                onClick={() => handlePickTarget(f)}
                className="group flex flex-col overflow-hidden rounded-lg border border-border bg-muted/20 transition-all hover:border-primary hover:shadow-lg hover:shadow-primary/20"
              >
                <div className="aspect-[2/3] w-full overflow-hidden bg-muted">
                  {f.poster_url && (
                    <img
                      src={f.poster_url}
                      alt={f.title}
                      className="h-full w-full object-cover transition-transform group-hover:scale-105"
                    />
                  )}
                </div>
                <div className="p-2 text-left">
                  <div className="line-clamp-2 text-sm font-medium">{f.title}</div>
                  <div className="text-xs text-muted-foreground">{f.year ?? ""}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {!isAuthenticated && mode === "daily" && (
        <p className="text-xs text-muted-foreground">
          Anonymous play — sign in to save scores and unlock free play.
        </p>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <div className="text-lg font-bold tabular-nums">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  );
}
