import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Calendar, Check, Copy, Home, Loader2, Shuffle, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { fetchGameHistory, fetchGameStats } from "@/api/client";
import type {
  GameHistoryItem, GameStats, GameType, GameTypeStats, PaginatedGameHistory,
} from "@/types/api";
import { cn } from "@/lib/utils";
import { dailyNumber, describeFilters } from "@/components/game/shareCaption";

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <div className="text-lg font-bold tabular-nums">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  );
}

function StatsBlocks({ stats }: { stats: GameTypeStats }) {
  if (stats.daily.games === 0 && stats.free.games === 0) {
    return (
      <p className="rounded-lg border border-border bg-card/30 p-4 text-center text-sm text-muted-foreground">
        No games yet — play one to start tracking stats.
      </p>
    );
  }
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
          <Stat label="Streak" value={`🔥 ${stats.daily.current_streak} / 🏆 ${stats.daily.max_streak}`} />
        </div>
      </div>
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
    </div>
  );
}

function buildShareForHistory(item: GameHistoryItem): string {
  const dayNum = item.challenge_date ? dailyNumber(item.game_type as any, item.challenge_date) : null;
  const hearts = "❤️".repeat(item.lives_remaining) + "🖤".repeat(3 - item.lives_remaining);
  const starsLine = item.stars > 0 ? "⭐".repeat(item.stars) : "💀";
  const filters = item.mode === "free" ? describeFilters(item.difficulty, item.pool_filters) : "";
  const filterBlock = filters ? `\n${filters}` : "";

  if (item.game_type === "tag_it") {
    const head = item.mode === "daily" ? `🎬 Tag It Daily #${dayNum}` : "🎬 Tag It — Free Play";
    const status = item.completed && item.stars > 0
      ? `🎯 Found in ${item.tags_used} tags`
      : "🎯 Failed";
    return `${head}\n${status}\n${hearts}\n${starsLine}${filterBlock}\nhttps://cinetag.eu/game`;
  }
  if (item.game_type === "chain_it") {
    const head = item.mode === "daily" ? `🔗 CineTag Chain #${dayNum}` : "🔗 CineTag Chain — Free Play";
    const o = item.origin_film?.title ?? "?";
    const t = item.target_film?.title ?? "?";
    const len = item.chain_length ?? "—";
    return `${head}\n🎬 ${o} → … → ${t}\n📏 ${len} steps | ${hearts} | ${starsLine}${filterBlock}\nhttps://cinetag.eu/game`;
  }
  // guess_it
  const head = item.mode === "daily" ? `🔍 CineTag Guess It #${dayNum}` : "🔍 CineTag Guess It — Free Play";
  const status = item.completed && item.stars > 0
    ? `🎯 Guessed in ${item.tags_used} tags`
    : `❌ Game over after ${item.tags_used} tags`;
  return `${head}\n${status}\n${hearts}\n${starsLine}${filterBlock}\nhttps://cinetag.eu/game`;
}

function HistoryRow({ item }: { item: GameHistoryItem }) {
  const [copied, setCopied] = useState(false);
  const films = item.game_type === "chain_it"
    ? [item.origin_film, item.target_film].filter(Boolean)
    : [item.film].filter(Boolean);

  const filtersChip = item.mode === "free" ? describeFilters(item.difficulty, item.pool_filters) : "";

  function copy() {
    navigator.clipboard.writeText(buildShareForHistory(item)).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <tr className="border-b border-border/60">
      <td className="py-2 pr-2 text-xs text-muted-foreground">
        {item.played_at ? new Date(item.played_at).toLocaleDateString() : ""}
      </td>
      <td className="py-2 pr-2 text-xs">
        <span className={cn(
          "rounded px-1.5 py-0.5",
          item.game_type === "chain_it" ? "bg-amber-500/15 text-amber-300"
            : item.game_type === "guess_it" ? "bg-emerald-500/15 text-emerald-300"
            : "bg-primary/15 text-primary",
        )}>
          {item.game_type === "chain_it" ? "Chain" : item.game_type === "guess_it" ? "Guess" : "Tag"}
        </span>
      </td>
      <td className="py-2 pr-2 text-xs text-muted-foreground">{item.mode}</td>
      <td className="py-2 pr-2">
        <div className="flex items-center gap-1.5">
          {films.map((f) =>
            f ? (
              <Link key={f.film_id} to={`/films/${f.film_id}`} className="flex items-center gap-1.5 hover:text-primary">
                {f.poster_url ? (
                  <img src={f.poster_url} alt={f.title} className="h-10 w-7 rounded object-cover" />
                ) : (
                  <div className="h-10 w-7 rounded bg-muted" />
                )}
                <span className="line-clamp-1 max-w-[140px] text-xs">{f.title}</span>
              </Link>
            ) : null,
          )}
        </div>
      </td>
      <td className="py-2 pr-2 text-xs text-muted-foreground">
        {item.game_type === "chain_it" ? `${item.chain_length ?? "—"} films` : `${item.tags_used} tags`}
      </td>
      <td className="py-2 pr-2 text-xs">❤️×{item.lives_remaining}</td>
      <td className="py-2 pr-2">
        <div className="flex">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              className={cn("h-3 w-3", i < item.stars ? "fill-amber-400 text-amber-400" : "fill-none text-muted-foreground/30")}
            />
          ))}
        </div>
      </td>
      <td className="py-2 pr-2 text-xs">
        {filtersChip ? (
          <span className="rounded bg-muted/40 px-1.5 py-0.5 text-[10px] text-muted-foreground">{filtersChip}</span>
        ) : (
          <span className="text-muted-foreground/40">—</span>
        )}
      </td>
      <td className="py-2 pr-2 text-xs">
        {item.completed && item.stars > 0 ? (
          <span className="text-emerald-400">✓ Win</span>
        ) : (
          <span className="text-muted-foreground">✗ Loss</span>
        )}
      </td>
      <td className="py-2 text-xs">
        <button
          onClick={copy}
          className="inline-flex items-center gap-1 rounded border border-border px-1.5 py-0.5 text-[10px] hover:text-primary"
          title="Copy share caption"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </td>
    </tr>
  );
}

export function GameStatsPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [tab, setTab] = useState<GameType>("tag_it");
  const [stats, setStats] = useState<GameStats | null>(null);
  const [history, setHistory] = useState<PaginatedGameHistory | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) navigate("/auth", { replace: true });
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchGameStats().then(setStats).catch(() => {});
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    setLoading(true);
    fetchGameHistory(tab, page).then(setHistory).catch(() => setHistory(null)).finally(() => setLoading(false));
  }, [isAuthenticated, tab, page]);

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur">
        <button
          onClick={() => navigate("/browse")}
          className="flex items-center gap-2 text-sm font-medium hover:text-primary"
        >
          <img src="/cinetag-logo/cinetag_logo.svg" alt="CineTag" className="h-5 w-5" /> CineTag
        </button>
        <div className="text-sm font-semibold tracking-wide">📊 Game Stats</div>
        <Button variant="ghost" size="icon" onClick={() => navigate("/browse")}>
          <Home className="h-4 w-4" />
        </Button>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6">
        <Link to="/game" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Games
        </Link>

        <div className="flex rounded-md border border-border bg-muted/30 p-1">
          <button
            onClick={() => { setTab("tag_it"); setPage(1); }}
            className={cn("flex-1 rounded px-4 py-2 text-sm font-medium",
              tab === "tag_it" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
          >🎬 Tag It</button>
          <button
            onClick={() => { setTab("chain_it"); setPage(1); }}
            className={cn("flex-1 rounded px-4 py-2 text-sm font-medium",
              tab === "chain_it" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
          >🔗 Chain It</button>
          <button
            onClick={() => { setTab("guess_it"); setPage(1); }}
            className={cn("flex-1 rounded px-4 py-2 text-sm font-medium",
              tab === "guess_it" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
          >🔍 Guess It</button>
        </div>

        {stats && <StatsBlocks stats={stats[tab]} />}

        <div className="rounded-lg border border-border bg-card/30 p-4">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">History</h3>
          {loading ? (
            <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin" /></div>
          ) : !history || history.items.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No games yet — play one!</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-[10px] uppercase tracking-wide text-muted-foreground">
                      <th className="py-2 pr-2">Date</th>
                      <th className="py-2 pr-2">Game</th>
                      <th className="py-2 pr-2">Mode</th>
                      <th className="py-2 pr-2">Film(s)</th>
                      <th className="py-2 pr-2">Length</th>
                      <th className="py-2 pr-2">Lives</th>
                      <th className="py-2 pr-2">Stars</th>
                      <th className="py-2 pr-2">Difficulty / filters</th>
                      <th className="py-2 pr-2">Result</th>
                      <th className="py-2">Share</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.items.map((it) => <HistoryRow key={it.id} item={it} />)}
                  </tbody>
                </table>
              </div>
              {history.total_pages > 1 && (
                <div className="mt-3 flex items-center justify-center gap-2 text-xs">
                  <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
                  <span className="text-muted-foreground">Page {history.page} / {history.total_pages}</span>
                  <Button variant="ghost" size="sm" disabled={page >= history.total_pages} onClick={() => setPage(page + 1)}>Next</Button>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
