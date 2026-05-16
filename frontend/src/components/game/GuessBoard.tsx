import { Fragment, useState } from "react";
import { Calendar, FileText, Info, Loader2, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useTagDescriptions } from "@/hooks/useTaxonomy";
import {
  guessEarlyGuess, guessJokerDecade, guessJokerSynopsis,
  guessRemoveFilm, guessRevealTag,
} from "@/api/client";
import { cn } from "@/lib/utils";
import { JokerButton } from "./JokerButton";
import { LivesDisplay } from "./LivesDisplay";
import { FilmGridCell } from "./FilmGridCell";
import type { GameFilm, GameTag, GuessAction } from "@/types/api";

export interface GuessBoardState {
  revealedTags: { dimension: string; value: string; display: string }[];
  removedFilmIds: number[];
  lives: number;
  jokersUsed: number;
  actionLog: GuessAction[];
  finalGuessFilmId?: number;
  wrongGuess?: boolean;
}

interface GuessBoardProps {
  grid: GameFilm[];
  targetFilmId: number;
  decadeLocked?: boolean;
  difficulty?: "easy" | "medium" | "hard";
  onVictory: (state: GuessBoardState) => void;
  onGameOver: (state: GuessBoardState) => void;
}

export function GuessBoard({ grid, targetFilmId, decadeLocked, difficulty = "medium", onVictory, onGameOver }: GuessBoardProps) {
  const descriptions = useTagDescriptions();
  const [revealedTags, setRevealedTags] = useState<{ dimension: string; value: string; display: string }[]>([]);
  const [removedFilmIds, setRemovedFilmIds] = useState<Set<number>>(new Set());
  const [lives, setLives] = useState(3);
  // Synopsis × 2, Decade × 1 (locked if decade filter is active).
  const [jokers, setJokers] = useState({ synopsis: 2, decade: decadeLocked ? 0 : 1 });
  const [synopsisUsedFor, setSynopsisUsedFor] = useState<Set<number>>(new Set());
  const [synopsisModal, setSynopsisModal] = useState<null | { filmId: number; text: string }>(null);
  const [shakeId, setShakeId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [actionLog, setActionLog] = useState<GuessAction[]>([]);
  const [decadeModal, setDecadeModal] = useState<string | null>(null);

  const totalJokers = 2 + (decadeLocked ? 0 : 1);
  const jokersUsed = totalJokers - (jokers.synopsis + jokers.decade);
  const remainingFilms = grid.filter((f) => !removedFilmIds.has(f.film_id));

  async function handleReveal() {
    if (busy) return;
    setBusy(true);
    setFeedback(null);
    try {
      const tags: GameTag[] = revealedTags.map((t) => ({ dimension: t.dimension, value: t.value }));
      const remaining = remainingFilms.map((f) => f.film_id);
      const r = await guessRevealTag(targetFilmId, tags, remaining, difficulty);
      if (!r.dimension || !r.tag) {
        setFeedback("No more useful tags to reveal.");
        return;
      }
      const entry = { dimension: r.dimension, value: r.tag, display: r.display ?? `${r.dimension}: ${r.tag}` };
      setRevealedTags((t) => [...t, entry]);
      setActionLog((a) => [...a, { action: "reveal", dimension: r.dimension!, tag: r.tag! }]);
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove(filmId: number) {
    if (busy) return;
    const film = grid.find((f) => f.film_id === filmId);
    setBusy(true);
    setFeedback(null);
    try {
      const tags: GameTag[] = revealedTags.map((t) => ({ dimension: t.dimension, value: t.value }));
      const r = await guessRemoveFilm(targetFilmId, filmId, tags);

      if (r.is_target) {
        const newLog: GuessAction[] = [...actionLog, { action: "remove", film_id: filmId, film_title: film?.title }];
        setActionLog(newLog);
        onGameOver({
          revealedTags, removedFilmIds: Array.from(removedFilmIds), lives, jokersUsed, actionLog: newLog,
        });
        return;
      }

      if (!r.correct) {
        const newLives = lives - 1;
        setLives(newLives);
        setShakeId(filmId);
        setTimeout(() => setShakeId(null), 600);
        setFeedback("This film matches all revealed tags — it stays!");
        const newLog: GuessAction[] = [...actionLog, { action: "wrong_remove", film_id: filmId, film_title: film?.title }];
        setActionLog(newLog);
        if (newLives <= 0) {
          onGameOver({
            revealedTags, removedFilmIds: Array.from(removedFilmIds), lives: 0, jokersUsed, actionLog: newLog,
          });
        }
        return;
      }

      const newRemoved = new Set(removedFilmIds);
      newRemoved.add(filmId);
      setRemovedFilmIds(newRemoved);
      const newLog: GuessAction[] = [...actionLog, { action: "remove", film_id: filmId, film_title: film?.title }];
      setActionLog(newLog);

      const remainingNow = grid.filter((f) => !newRemoved.has(f.film_id));
      if (remainingNow.length === 1 && remainingNow[0]?.film_id === targetFilmId) {
        onVictory({
          revealedTags, removedFilmIds: Array.from(newRemoved), lives, jokersUsed, actionLog: newLog,
        });
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleGuess(filmId: number) {
    if (busy) return;
    setBusy(true);
    setFeedback(null);
    try {
      const r = await guessEarlyGuess(targetFilmId, filmId);
      const film = grid.find((f) => f.film_id === filmId);
      const newLog: GuessAction[] = [...actionLog, { action: "guess", film_id: filmId, film_title: film?.title }];
      setActionLog(newLog);
      if (r.correct) {
        onVictory({
          revealedTags, removedFilmIds: Array.from(removedFilmIds), lives, jokersUsed, actionLog: newLog,
        });
      } else {
        onGameOver({
          revealedTags, removedFilmIds: Array.from(removedFilmIds), lives, jokersUsed,
          actionLog: newLog, finalGuessFilmId: filmId, wrongGuess: true,
        });
      }
    } finally {
      setBusy(false);
    }
  }

  async function jokerSynopsis() {
    if (busy || jokers.synopsis <= 0) return;
    setBusy(true);
    try {
      const remaining = remainingFilms.map((f) => f.film_id);
      const r = await guessJokerSynopsis(remaining, Array.from(synopsisUsedFor));
      if (!r.film_id) {
        setFeedback("No film available for synopsis.");
        return;
      }
      setSynopsisUsedFor((s) => new Set(s).add(r.film_id!));
      setJokers((j) => ({ ...j, synopsis: j.synopsis - 1 }));
      setSynopsisModal({ filmId: r.film_id, text: r.synopsis ?? "(no synopsis available)" });
    } finally { setBusy(false); }
  }

  async function jokerDecade() {
    if (busy || jokers.decade <= 0) return;
    setBusy(true);
    try {
      const r = await guessJokerDecade(targetFilmId);
      setJokers((j) => ({ ...j, decade: j.decade - 1 }));
      setDecadeModal(r.decade ?? "(unknown)");
    } finally { setBusy(false); }
  }

  const synopsisFilmInModal = synopsisModal ? grid.find((f) => f.film_id === synopsisModal.filmId) : null;

  return (
    <>
      <div className="sticky top-14 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-5xl px-4 py-2">
          <div className="flex items-center justify-between gap-3">
            <Button onClick={handleReveal} disabled={busy} className="gap-2">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Reveal tag ({revealedTags.length})
            </Button>
            <LivesDisplay lives={lives} shakeKey={lives} />
          </div>
          {revealedTags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {revealedTags.map((t, i) => {
                const desc = descriptions?.[t.dimension]?.[t.value];
                return (
                  <Fragment key={i}>
                    <span className="inline-flex items-center">
                      <span className={cn(
                        "rounded-md border border-amber-400/50 bg-amber-400/10 px-2 py-0.5 text-[11px] text-amber-300",
                        desc && "rounded-r-none",
                      )}>
                        {t.display}
                      </span>
                      {desc && (
                        <Popover>
                          <PopoverTrigger asChild>
                            <button
                              onClick={(e) => e.stopPropagation()}
                              aria-label={`About ${t.value}`}
                              className="rounded-md rounded-l-none border border-l-0 border-amber-400/50 bg-amber-400/10 px-1 py-0.5 text-amber-300/70 hover:text-amber-300"
                            >
                              <Info className="h-3 w-3" />
                            </button>
                          </PopoverTrigger>
                          <PopoverContent side="bottom" className="w-64 px-3 py-2 text-xs" onOpenAutoFocus={(e) => e.preventDefault()}>
                            <p className="mb-1 font-medium">{t.value}</p>
                            <p className="text-muted-foreground">{desc}</p>
                          </PopoverContent>
                        </Popover>
                      )}
                    </span>
                  </Fragment>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-4">
        <div className="flex items-center justify-center gap-2">
          <JokerButton icon={FileText} label="Synopsis" remaining={jokers.synopsis} onClick={jokerSynopsis} disabled={busy}
            description="Reveal the synopsis of a random remaining film (could be the target or a decoy). 2 uses." />
          <JokerButton icon={Calendar} label="Decade" remaining={jokers.decade} onClick={jokerDecade}
            disabled={busy || decadeLocked}
            description={decadeLocked
              ? "Disabled — you've already filtered by decade."
              : "Reveal the target's decade. 1 use."} />
        </div>

        {feedback && (
          <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-center text-xs text-red-400">
            {feedback}
          </div>
        )}

        <p className="text-center text-xs text-muted-foreground">
          Click a film: <span className="text-red-400">Remove</span> if you think it doesn't match — or guess <span className="text-amber-400">This is it!</span>
        </p>

        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-4">
          {grid.map((f) => (
            <div key={f.film_id} className="relative">
              <FilmGridCell
                film={f}
                removed={removedFilmIds.has(f.film_id)}
                shake={shakeId === f.film_id}
                disabled={busy}
                onRemove={handleRemove}
                onGuess={handleGuess}
              />
              {synopsisUsedFor.has(f.film_id) && !removedFilmIds.has(f.film_id) && (
                <button
                  onClick={() => {
                    // Re-open the synopsis for that film from local cache? We need to re-fetch.
                    // Simpler: stash the text via setSynopsisModal when joker was used; for re-view,
                    // re-trigger the modal with the same content via state.
                  }}
                  className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-white shadow"
                  title="Synopsis revealed for this film"
                >
                  <FileText className="h-3 w-3" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {synopsisModal && synopsisFilmInModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setSynopsisModal(null)}>
          <div className="w-full max-w-lg rounded-lg border border-border bg-background p-4" onClick={(e) => e.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                {synopsisFilmInModal.poster_url && (
                  <img src={synopsisFilmInModal.poster_url} alt="" className="h-10 w-7 rounded object-cover" />
                )}
                <div>
                  <div className="text-xs uppercase tracking-wide text-muted-foreground">Synopsis of</div>
                  <h3 className="text-base font-semibold">{synopsisFilmInModal.title}</h3>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setSynopsisModal(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">{synopsisModal.text}</p>
            <p className="mt-3 text-[10px] text-muted-foreground">
              ⚠️ This may or may not be the target film.
            </p>
          </div>
        </div>
      )}

      {decadeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setDecadeModal(null)}>
          <div className="w-full max-w-sm rounded-lg border border-border bg-background p-4 text-center" onClick={(e) => e.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">Target's decade</h3>
              <Button variant="ghost" size="icon" onClick={() => setDecadeModal(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-3xl font-bold text-amber-300">{decadeModal}</p>
          </div>
        </div>
      )}
    </>
  );
}
