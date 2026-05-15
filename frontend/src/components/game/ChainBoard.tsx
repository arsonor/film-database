import { Fragment, useState } from "react";
import { Info, Loader2, Shuffle, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useTagDescriptions } from "@/hooks/useTaxonomy";
import {
  chainCheckTag,
  chainGetFilms,
  chainGetTags,
  chainJokerRevealTag,
  chainJokerSynopsis,
} from "@/api/client";
import { cn } from "@/lib/utils";
import { DIMENSION_LABELS, GAME_DIMENSIONS, type GameDimension } from "./dimensions";
import { JokerButton } from "./JokerButton";
import { LivesDisplay } from "./LivesDisplay";
import { ChainProgress, type ChainStepEntry } from "./ChainProgress";
import { FilmPickList } from "./FilmPickList";
import type { ChainFilm, ChainOrigin, ChainStep, GameFilm, GamePoolFilters } from "@/types/api";

export interface ChainBoardState {
  steps: ChainStepEntry[];
  accumulatedTags: { dimension: string; value: string }[];
  lives: number;
  jokers: { reveal: number };
  chainLength: number;
  sequence: ChainStep[];
}

interface ChainBoardProps {
  origin: ChainOrigin;
  target: ChainFilm;
  poolFilters?: GamePoolFilters;
  difficulty?: "easy" | "medium" | "hard";
  onVictory: (state: ChainBoardState) => void;
  onGameOver: (state: ChainBoardState) => void;
}

export function ChainBoard({ origin, target, poolFilters, difficulty = "medium", onVictory, onGameOver }: ChainBoardProps) {
  const descriptions = useTagDescriptions();
  const [currentFilm, setCurrentFilm] = useState<ChainFilm>(origin);
  const [currentTags, setCurrentTags] = useState<Record<string, string[]>>(origin.tags);
  const [steps, setSteps] = useState<ChainStepEntry[]>([]);
  const [accumulated, setAccumulated] = useState<{ dimension: string; value: string }[]>([]);
  const [sequence, setSequence] = useState<ChainStep[]>([]);
  const [wrongTags, setWrongTags] = useState<{ dimension: string; value: string; filmId: number }[]>([]);
  // Only one green tag at a time on the current film. Picking a new film resets this.
  const [currentStepTag, setCurrentStepTag] = useState<{ dimension: string; value: string } | null>(null);
  const [revealedTag, setRevealedTag] = useState<{ dimension: string; value: string } | null>(null);
  const [lives, setLives] = useState(3);
  const [revealUses, setRevealUses] = useState(3);
  const [films, setFilms] = useState<GameFilm[]>([]);
  const [poolSize, setPoolSize] = useState<number>(0);
  const [targetVisible, setTargetVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  // After picking a new film: right panel goes idle until user picks the next tag.
  const [awaitingTag, setAwaitingTag] = useState(true);
  const [modal, setModal] = useState<null | { kind: "synopsis"; text: string } | { kind: "reveal"; dim: string; tag: string }>(null);

  const excludeIds = [origin.film_id, target.film_id, ...steps.map((s) => s.film.film_id)];

  async function refreshFilms(
    tags: { dimension: string; value: string }[],
    opts: { randomize?: boolean } = {},
  ) {
    if (tags.length === 0) {
      setFilms([]);
      setPoolSize(0);
      setTargetVisible(false);
      return;
    }
    setBusy(true);
    try {
      const r = await chainGetFilms(tags, excludeIds, target.film_id, poolFilters, opts.randomize, difficulty);
      setFilms(r.films);
      setPoolSize(r.pool_size);
      setTargetVisible(r.target_visible);
    } finally {
      setBusy(false);
    }
  }

  async function handleTagClick(dim: string, value: string) {
    if (busy) return;

    // Click on the currently-active green tag → deselect it.
    if (currentStepTag && currentStepTag.dimension === dim && currentStepTag.value === value) {
      const newAcc = accumulated.filter((t) => !(t.dimension === dim && t.value === value));
      setAccumulated(newAcc);
      setCurrentStepTag(null);
      setAwaitingTag(false);
      await refreshFilms(newAcc);
      return;
    }
    // Block other selections while a green tag is active.
    if (currentStepTag) return;
    if (wrongTags.some((t) => t.filmId === currentFilm.film_id && t.dimension === dim && t.value === value)) return;

    setBusy(true);
    setFeedback(null);
    try {
      const r = await chainCheckTag(target.film_id, dim, value);
      const step: ChainStep = {
        step: sequence.length + 1,
        film_id: currentFilm.film_id,
        film_title: currentFilm.title,
        dimension: dim,
        tag: value,
        correct: r.correct,
      };
      setSequence((s) => [...s, step]);
      if (!r.correct) {
        const newLives = lives - 1;
        setLives(newLives);
        setWrongTags((w) => [...w, { dimension: dim, value, filmId: currentFilm.film_id }]);
        setFeedback(`Target doesn't have "${value}" — life lost`);
        if (newLives <= 0) {
          onGameOver({
            steps, accumulatedTags: accumulated, lives: 0, jokers: { reveal: revealUses },
            chainLength: steps.length, sequence: [...sequence, step],
          });
        }
      } else {
        const newAcc = [...accumulated, { dimension: dim, value }];
        setAccumulated(newAcc);
        setCurrentStepTag({ dimension: dim, value });
        setRevealedTag(null);
        setAwaitingTag(false);
        await refreshFilms(newAcc);
      }
    } finally {
      setBusy(false);
    }
  }

  async function handlePickFilm(f: GameFilm) {
    if (busy || awaitingTag) return;
    if (f.film_id === target.film_id) {
      const newSteps: ChainStepEntry[] = [
        ...steps,
        {
          film: { film_id: f.film_id, title: f.title, year: f.year, poster_url: f.poster_url },
          via_tag: currentStepTag,
        },
      ];
      onVictory({
        steps: newSteps, accumulatedTags: accumulated, lives, jokers: { reveal: revealUses },
        chainLength: newSteps.length, sequence,
      });
      return;
    }
    setBusy(true);
    try {
      const tags = await chainGetTags(f.film_id);
      const filmEntry: ChainFilm = { film_id: f.film_id, title: f.title, year: f.year, poster_url: f.poster_url };
      setSteps((s) => [...s, { film: filmEntry, via_tag: currentStepTag }]);
      setCurrentFilm(filmEntry);
      setCurrentTags(tags.tags);
      setCurrentStepTag(null);
      setRevealedTag(null);
      setAwaitingTag(true);
    } finally {
      setBusy(false);
    }
  }

  async function openSynopsis() {
    setBusy(true);
    try {
      const r = await chainJokerSynopsis(target.film_id);
      setModal({ kind: "synopsis", text: r.synopsis ?? "(no synopsis available)" });
    } finally { setBusy(false); }
  }

  async function jokerReveal() {
    if (revealUses <= 0 || currentStepTag) return;
    setBusy(true);
    try {
      const usedDims = Array.from(new Set(accumulated.map((t) => t.dimension)));
      const r = await chainJokerRevealTag(target.film_id, usedDims, currentFilm.film_id, accumulated);
      setRevealUses((n) => n - 1);
      if (r.dimension && r.tag) {
        setRevealedTag({ dimension: r.dimension, value: r.tag });
        setModal({ kind: "reveal", dim: r.dimension, tag: r.tag });
      }
    } finally { setBusy(false); }
  }

  async function doShuffle() {
    if (accumulated.length === 0 || awaitingTag) return;
    await refreshFilms(accumulated, { randomize: true });
  }

  const wrongOnCurrent = wrongTags.filter((w) => w.filmId === currentFilm.film_id);
  const rightPanelActive = !awaitingTag && accumulated.length > 0;

  return (
    <>
      <div className="sticky top-14 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-5xl px-4 py-2">
          <ChainProgress origin={origin} target={target} steps={steps} onTargetInfo={openSynopsis} />
          <div className="mt-1 flex items-center justify-between">
            <LivesDisplay lives={lives} shakeKey={lives} />
            <div className="text-[10px] text-muted-foreground">{steps.length} step{steps.length === 1 ? "" : "s"}</div>
          </div>
          <div className="mt-1 text-center text-[10px] text-muted-foreground">
            🎯 The target film appears in the list only when ≤ 10 films remain in the pool.
          </div>
        </div>
      </div>

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-4">
        <div className="flex items-center justify-center">
          <JokerButton
            icon={Sparkles}
            label="Reveal"
            remaining={revealUses}
            onClick={jokerReveal}
            disabled={busy || !!currentStepTag}
            description="Reveals one tag of the target from a dimension you haven't used yet. 3 uses."
          />
        </div>

        {feedback && (
          <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-center text-xs text-red-400">
            {feedback}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Left: current film + tags */}
          <div
            className={cn(
              "rounded-lg border border-border bg-card/30 p-3 transition-opacity",
              awaitingTag ? "ring-2 ring-primary/40" : "",
            )}
          >
            <div className="mb-2 flex items-center gap-3">
              <div className="h-20 w-14 overflow-hidden rounded bg-muted">
                {currentFilm.poster_url && <img src={currentFilm.poster_url} alt={currentFilm.title} className="h-full w-full object-cover" />}
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Current film</div>
                <div className="text-sm font-medium">{currentFilm.title}</div>
                <div className="text-xs text-muted-foreground">{currentFilm.year ?? ""}</div>
              </div>
            </div>
            <p className="mb-2 text-xs text-muted-foreground">
              {currentStepTag
                ? <>Selected: <span className="text-emerald-300">{currentStepTag.value}</span> · click again to deselect, or pick the next film →</>
                : <>Pick a tag you think the <span className="text-foreground">target</span> also has:</>}
            </p>
            <div className="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
              {([...GAME_DIMENSIONS, "geography"] as string[]).map((dim) => {
                const items = currentTags[dim] || [];
                if (items.length === 0) return null;
                const label = dim === "geography"
                  ? "Locations"
                  : DIMENSION_LABELS[dim as GameDimension];
                return (
                  <div key={dim}>
                    <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                      {label}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {items.map((tag) => {
                        const isCurrentGreen = currentStepTag?.dimension === dim && currentStepTag?.value === tag;
                        const isAccumulated = accumulated.some((t) => t.dimension === dim && t.value === tag);
                        const isWrongHere = wrongOnCurrent.some((t) => t.dimension === dim && t.value === tag);
                        const isRevealed = revealedTag?.dimension === dim && revealedTag?.value === tag;
                        const description = descriptions?.[dim]?.[tag];
                        const lockedByOtherSelection = !!currentStepTag && !isCurrentGreen;

                        return (
                          <Fragment key={tag}>
                            <span className="inline-flex items-center align-top">
                              <button
                                disabled={busy || (isAccumulated && !isCurrentGreen) || isWrongHere || lockedByOtherSelection}
                                onClick={() => handleTagClick(dim, tag)}
                                title={description}
                                className={cn(
                                  "rounded-md border px-2 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed",
                                  description && "rounded-r-none",
                                  isCurrentGreen && "border-emerald-500 bg-emerald-500/20 text-emerald-300 cursor-pointer disabled:cursor-pointer",
                                  !isCurrentGreen && isAccumulated && "border-emerald-500/60 bg-emerald-500/10 text-emerald-300/60",
                                  isWrongHere && "border-red-500 bg-red-500/15 text-red-400 line-through",
                                  isRevealed && !isAccumulated && "border-amber-400 bg-amber-400/15 text-amber-300 ring-2 ring-amber-400/50",
                                  !isCurrentGreen && !isAccumulated && !isWrongHere && !isRevealed &&
                                    "border-border bg-transparent text-muted-foreground hover:border-primary/60 hover:text-foreground",
                                  lockedByOtherSelection && "opacity-40",
                                )}
                              >
                                {tag}
                              </button>
                              {description && (
                                <Popover>
                                  <PopoverTrigger asChild>
                                    <button
                                      onClick={(e) => e.stopPropagation()}
                                      aria-label={`About ${tag}`}
                                      className={cn(
                                        "rounded-md rounded-l-none border border-l-0 px-1 py-1 transition-colors",
                                        isCurrentGreen
                                          ? "border-emerald-500 bg-emerald-500/20 text-emerald-300/70"
                                          : isAccumulated
                                            ? "border-emerald-500/60 bg-emerald-500/10 text-emerald-300/50"
                                            : isWrongHere
                                              ? "border-red-500 bg-red-500/15 text-red-400/60"
                                              : isRevealed
                                                ? "border-amber-400 bg-amber-400/15 text-amber-300/70"
                                                : "border-border text-muted-foreground/60 hover:text-foreground",
                                      )}
                                    >
                                      <Info className="h-3 w-3" />
                                    </button>
                                  </PopoverTrigger>
                                  <PopoverContent side="top" className="w-64 px-3 py-2 text-xs" onOpenAutoFocus={(e) => e.preventDefault()}>
                                    <p className="mb-1 font-medium">{tag}</p>
                                    <p className="text-muted-foreground">{description}</p>
                                  </PopoverContent>
                                </Popover>
                              )}
                            </span>
                          </Fragment>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: film pick list (greyed out when awaiting a tag) */}
          <div
            className={cn(
              "rounded-lg border border-border bg-card/30 p-3 transition-opacity",
              !rightPanelActive && "pointer-events-none opacity-50",
            )}
          >
            <div className="mb-2 flex items-center justify-between">
              <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Possible next films</div>
              <Button
                variant="ghost"
                size="sm"
                onClick={doShuffle}
                disabled={!rightPanelActive || busy || films.length === 0}
                className="h-7 gap-1 text-xs"
                title="Shuffle film list"
              >
                <Shuffle className="h-3.5 w-3.5" /> Shuffle
              </Button>
            </div>

            {accumulated.length === 0 || awaitingTag ? (
              <div className="py-6 text-center text-xs text-muted-foreground">
                Pick a tag from the current film to populate this list.
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <div className="text-xs text-muted-foreground">
                  {poolSize} films matching
                  {targetVisible && <span className="ml-2 text-amber-400">🎯 target is in the list!</span>}
                </div>
                {accumulated.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1 text-[10px]">
                    <span className="text-muted-foreground">Chain tags:</span>
                    {accumulated.map((t, i) => (
                      <span key={i} className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-emerald-300">{t.value}</span>
                    ))}
                  </div>
                )}
                <div className="text-xs text-muted-foreground">Pick the next film in the chain:</div>
                <FilmPickList
                  films={films}
                  poolSize={poolSize}
                  targetFilmId={target.film_id}
                  targetVisible={targetVisible}
                  onPick={handlePickFilm}
                  disabled={busy}
                  hideHeader
                />
              </div>
            )}
          </div>
        </div>

        {busy && (
          <div className="fixed bottom-4 right-4 rounded-md border border-border bg-background px-3 py-1 text-xs text-muted-foreground shadow-lg">
            <Loader2 className="inline h-3 w-3 animate-spin" /> Working…
          </div>
        )}
      </div>

      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setModal(null)}>
          <div className="w-full max-w-lg rounded-lg border border-border bg-background p-4" onClick={(e) => e.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {modal.kind === "synopsis" ? "Target synopsis" : "Revealed tag"}
              </h3>
              <Button variant="ghost" size="icon" onClick={() => setModal(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            {modal.kind === "synopsis" ? (
              <p className="text-sm leading-relaxed text-muted-foreground">{modal.text}</p>
            ) : (
              <p className="text-sm">
                The target has the tag{" "}
                <span className="rounded bg-amber-400/15 px-2 py-0.5 font-medium text-amber-300">{modal.tag}</span>{" "}
                in <span className="text-muted-foreground">{DIMENSION_LABELS[modal.dim as GameDimension] ?? modal.dim}</span>.
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
