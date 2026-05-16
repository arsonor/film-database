import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, Calendar, Loader2, Lock, LogIn, Play, Shuffle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { fetchChainDaily, fetchChainRandom } from "@/api/client";
import type { ChainSetupResponse } from "@/types/api";
import { cn } from "@/lib/utils";

interface ChainSetupProps {
  onStart: (
    mode: "daily" | "free",
    setup: ChainSetupResponse,
    difficulty?: "easy" | "medium" | "hard",
  ) => void;
}

export function ChainSetup({ onStart }: ChainSetupProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [mode, setMode] = useState<"daily" | "free">("daily");
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [setup, setSetup] = useState<ChainSetupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "daily") return;
    const todayISO = new Date().toISOString().slice(0, 10);
    if (isAuthenticated) {
      fetchChainDaily().then((s) => {
        if (s.already_played) setSetup(s);
      }).catch(() => {});
    } else {
      try {
        const raw = localStorage.getItem("chainit_daily_result");
        if (!raw) return;
        const r = JSON.parse(raw);
        if (r?.challenge_date !== todayISO) return;
        fetchChainDaily().then((s) => {
          setSetup({
            ...s,
            already_played: {
              id: 0,
              chain_length: r.chain_length ?? null,
              lives_remaining: r.lives_remaining ?? 0,
              jokers_used: r.jokers_used ?? 0,
              stars: r.stars ?? 0,
              tag_sequence: null,
              completed: !!r.completed,
              played_at: null,
              origin_film_id: r.origin_film_id ?? null,
              target_film_id: r.target_film_id ?? null,
            },
          });
        }).catch(() => {});
      } catch {}
    }
  }, [mode, isAuthenticated]);

  function checkLocalDaily() {
    try {
      const raw = localStorage.getItem("chainit_daily_result");
      if (!raw) return null;
      const r = JSON.parse(raw);
      const todayISO = new Date().toISOString().slice(0, 10);
      return r?.challenge_date === todayISO ? r : null;
    } catch { return null; }
  }

  const freePlayLocked = mode === "free" && !isAuthenticated;

  async function handleLoad() {
    setError(null);
    setLoading(true);
    try {
      if (mode === "daily" && !isAuthenticated) {
        const local = checkLocalDaily();
        if (local) {
          const s = await fetchChainDaily();
          setSetup({
            ...s,
            already_played: {
              id: 0,
              chain_length: local.chain_length ?? null,
              lives_remaining: local.lives_remaining ?? 0,
              jokers_used: local.jokers_used ?? 0,
              stars: local.stars ?? 0,
              tag_sequence: null,
              completed: !!local.completed,
              played_at: null,
              origin_film_id: local.origin_film_id ?? null,
              target_film_id: local.target_film_id ?? null,
            },
          });
          return;
        }
      }
      const s = mode === "daily" ? await fetchChainDaily() : await fetchChainRandom({}, difficulty);
      setSetup(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load pair");
    } finally {
      setLoading(false);
    }
  }

  function handleStart() {
    if (!setup || setup.already_played) return;
    onStart(mode, setup, mode === "free" ? difficulty : "medium");
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-4 py-8">
      <Link to="/game" className="self-start inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Games
      </Link>

      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">🔗 Chain It</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Connect two distant films through shared tags.
        </p>
      </div>

      <div className="flex rounded-md border border-border bg-muted/30 p-1">
        <button
          onClick={() => { setMode("daily"); setSetup(null); }}
          className={cn(
            "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
            mode === "daily" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          <Calendar className="h-4 w-4" /> Daily
        </button>
        <button
          onClick={() => { setMode("free"); setSetup(null); }}
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
                  d === "easy" ? "Films share many tags — short chains"
                    : d === "hard" ? "Films share very few tags — long chains"
                    : "Balanced — moderate similarity"
                }
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      )}

      {!setup && !freePlayLocked && (
        <Button size="lg" onClick={handleLoad} disabled={loading} className="gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Load pair
        </Button>
      )}

      {error && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {setup && setup.already_played && (
        <div className="flex w-full max-w-md flex-col items-center gap-3 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-center">
          <p className="text-base font-semibold">You've already played today's chain!</p>
          <div className="text-sm text-muted-foreground">
            Chain length: {setup.already_played.chain_length ?? "—"} · Stars: {setup.already_played.stars}
          </div>
          <Button onClick={() => { setMode("free"); setSetup(null); }} variant="outline" size="sm">
            Play Free
          </Button>
        </div>
      )}

      {setup && !setup.already_played && (
        <div className="flex w-full flex-col items-center gap-4">
          <p className="text-sm text-muted-foreground">Connect these films:</p>
          <div className="flex w-full items-center justify-center gap-4">
            <FilmCard film={setup.origin} label="Origin" />
            <ArrowRight className="h-6 w-6 text-muted-foreground" />
            <FilmCard film={setup.target} label="Target" />
          </div>
          <Button size="lg" onClick={handleStart} className="gap-2">
            <Play className="h-4 w-4" /> Start chain
          </Button>
        </div>
      )}
    </div>
  );
}

function FilmCard({ film, label }: { film: { title: string; year: number | null; poster_url: string | null }; label: string }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</span>
      <div className="aspect-[2/3] w-32 overflow-hidden rounded-lg border border-border bg-muted">
        {film.poster_url && <img src={film.poster_url} alt={film.title} className="h-full w-full object-cover" />}
      </div>
      <div className="max-w-[140px] text-center text-sm font-medium">{film.title}</div>
      <div className="text-xs text-muted-foreground">{film.year ?? ""}</div>
    </div>
  );
}
