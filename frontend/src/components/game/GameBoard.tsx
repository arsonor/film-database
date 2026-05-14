import { Fragment, useState } from "react";
import {
  ChevronDown, ChevronRight, Eye, FileText, Info, Lightbulb, Loader2, X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useTaxonomy, useTagDescriptions } from "@/hooks/useTaxonomy";
import { cn } from "@/lib/utils";
import {
  checkGameTags,
  useJokerHint,
  useJokerRemaining,
  useJokerSynopsis,
} from "@/api/client";
import type {
  GameFilm,
  GamePoolFilters,
  GameTag,
} from "@/types/api";
import {
  DIMENSION_LABELS,
  GAME_DIMENSIONS,
  GROUP_TITLES,
  TIME_PERIOD_GROUPS,
  timePeriodBucket,
  type GameDimension,
} from "./dimensions";
import { LivesDisplay } from "./LivesDisplay";
import { RemainingCounter } from "./RemainingCounter";
import { JokerButton } from "./JokerButton";

export interface PlayedTag {
  dimension: GameDimension;
  value: string;
  remaining: number;
  correct: boolean;
}

interface GameBoardProps {
  target: GameFilm;
  poolSize: number;
  poolFilters?: GamePoolFilters;
  onVictory: (state: GameState) => void;
  onGameOver: (state: GameState) => void;
}

export interface GameState {
  played: PlayedTag[];
  lives: number;
  jokers: { remaining: number; hint: number; synopsis: number };
  remaining: number;
}

export function GameBoard({ target, poolSize, poolFilters, onVictory, onGameOver }: GameBoardProps) {
  const { taxonomies } = useTaxonomy();
  const descriptions = useTagDescriptions();
  const [played, setPlayed] = useState<PlayedTag[]>([]);
  const [lives, setLives] = useState(3);
  const [jokers, setJokers] = useState({ remaining: 1, hint: 1, synopsis: 1 });
  const [remaining, setRemaining] = useState(poolSize);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [hintTag, setHintTag] = useState<{ dim: string; val: string } | null>(null);
  const [modal, setModal] = useState<null | { kind: "remaining"; films: GameFilm[] } | { kind: "synopsis"; text: string }>(null);
  const [shakeKey, setShakeKey] = useState(0);
  const [counterKey, setCounterKey] = useState(0);
  const [feedback, setFeedback] = useState<string | null>(null);

  function correctTags(): GameTag[] {
    return played.filter((t) => t.correct).map((t) => ({ dimension: t.dimension, value: t.value }));
  }

  async function handleClickTag(dim: GameDimension, value: string) {
    if (busy) return;
    if (played.some((t) => t.dimension === dim && t.value === value)) return;

    setBusy(true);
    setFeedback(null);
    try {
      const newTags = [...correctTags(), { dimension: dim, value }];
      const res = await checkGameTags(target.film_id, newTags, poolFilters);

      if (!res.target_included) {
        const newLives = lives - 1;
        setLives(newLives);
        setShakeKey((k) => k + 1);
        setPlayed((p) => [...p, { dimension: dim, value, remaining: remaining, correct: false }]);
        setFeedback(`${value} eliminates the film — life lost`);
        if (newLives <= 0) {
          onGameOver({
            played: [...played, { dimension: dim, value, remaining, correct: false }],
            lives: 0,
            jokers,
            remaining,
          });
        }
      } else {
        setRemaining(res.remaining_count);
        setCounterKey((k) => k + 1);
        const newPlayed: PlayedTag[] = [...played, { dimension: dim, value, remaining: res.remaining_count, correct: true }];
        setPlayed(newPlayed);
        setHintTag(null);
        if (res.victory) {
          onVictory({ played: newPlayed, lives, jokers, remaining: 1 });
        }
      }
    } finally {
      setBusy(false);
    }
  }

  async function jokerShowRemaining() {
    if (jokers.remaining <= 0) return;
    setBusy(true);
    try {
      const res = await useJokerRemaining(correctTags(), poolFilters);
      setJokers((j) => ({ ...j, remaining: j.remaining - 1 }));
      setModal({ kind: "remaining", films: res.films });
    } finally { setBusy(false); }
  }

  async function jokerShowHint() {
    if (jokers.hint <= 0) return;
    setBusy(true);
    try {
      const res = await useJokerHint(target.film_id, correctTags(), poolFilters);
      if (res.dimension && res.tag) {
        setHintTag({ dim: res.dimension, val: res.tag });
        setExpanded((e) => ({ ...e, [res.dimension!]: true }));
      }
      setJokers((j) => ({ ...j, hint: j.hint - 1 }));
    } finally { setBusy(false); }
  }

  async function jokerShowSynopsis() {
    if (jokers.synopsis <= 0) return;
    setBusy(true);
    try {
      const res = await useJokerSynopsis(target.film_id);
      setJokers((j) => ({ ...j, synopsis: j.synopsis - 1 }));
      setModal({ kind: "synopsis", text: res.synopsis ?? "(no synopsis available)" });
    } finally { setBusy(false); }
  }

  return (
    <>
      {/* Sticky top info bar (target + counter + lives) */}
      <div className="sticky top-14 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3 lg:pr-44">
          <div className="flex items-center gap-3">
            {target.poster_url && (
              <img src={target.poster_url} alt={target.title} className="h-14 w-10 rounded object-cover" />
            )}
            <div>
              <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Target</div>
              <div className="text-sm font-medium leading-tight">{target.title}</div>
              <div className="text-xs text-muted-foreground">{target.year ?? ""}</div>
            </div>
          </div>
          <div key={counterKey} className="animate-counter">
            <RemainingCounter count={remaining} poolSize={poolSize} />
          </div>
          <div className="flex flex-col items-end gap-1">
            <LivesDisplay lives={lives} shakeKey={shakeKey} />
            <div className="text-[10px] text-muted-foreground">{played.filter((t) => t.correct).length} tags</div>
          </div>
        </div>
      </div>

      {/* Desktop fixed lifelines column — placed below the sticky top bar so it never overlaps it */}
      <aside className="fixed right-8 top-56 z-10 hidden flex-col gap-2 lg:flex">
        <div className="mb-1 text-center text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
          Lifelines
        </div>
        <JokerButton icon={Eye} label="Remaining" remaining={jokers.remaining} onClick={jokerShowRemaining} disabled={busy} description="Reveal the films still matching your correct tags so far." />
        <JokerButton icon={Lightbulb} label="Hint" remaining={jokers.hint} onClick={jokerShowHint} disabled={busy} description="Highlights one tag that significantly reduces the remaining count." />
        <JokerButton icon={FileText} label="Synopsis" remaining={jokers.synopsis} onClick={jokerShowSynopsis} disabled={busy} description="Shows the film's synopsis as a clue." />
      </aside>

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-4 lg:pr-40">
        {/* Mobile lifelines row */}
        <div className="flex items-center justify-center gap-2 lg:hidden">
          <JokerButton icon={Eye} label="Remaining" remaining={jokers.remaining} onClick={jokerShowRemaining} disabled={busy} />
          <JokerButton icon={Lightbulb} label="Hint" remaining={jokers.hint} onClick={jokerShowHint} disabled={busy} />
          <JokerButton icon={FileText} label="Synopsis" remaining={jokers.synopsis} onClick={jokerShowSynopsis} disabled={busy} />
        </div>

        {feedback && (
          <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-center text-xs text-red-400">
            {feedback}
          </div>
        )}

        {played.length > 0 && (
          <div className="flex flex-wrap items-center gap-1 text-xs">
            <span className="text-muted-foreground">Path:</span>
            {played.map((t, i) => (
              <span
                key={i}
                className={cn(
                  "rounded px-1.5 py-0.5",
                  t.correct ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-400 line-through",
                )}
              >
                {t.value}
              </span>
            ))}
          </div>
        )}

        <div className="space-y-1">
          {GAME_DIMENSIONS.map((dim) => {
            const items = taxonomies[dim] || [];
            const isOpen = expanded[dim] ?? false;
            return (
              <div key={dim} className="rounded-md border border-border bg-card/30">
                <button
                  onClick={() => setExpanded((e) => ({ ...e, [dim]: !isOpen }))}
                  className="flex w-full items-center justify-between px-3 py-2 text-sm font-medium hover:text-primary"
                >
                  <span>{DIMENSION_LABELS[dim]}</span>
                  {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </button>
                {isOpen && (
                  <div className="flex flex-wrap items-center px-3 pb-3">
                    {items.map((item, idx) => {
                      const playedTag = played.find((t) => t.dimension === dim && t.value === item.name);
                      const isHint = hintTag?.dim === dim && hintTag?.val === item.name;
                      const description = descriptions?.[dim]?.[item.name];
                      let cls =
                        "border-border bg-transparent text-muted-foreground hover:border-primary/60 hover:text-foreground";
                      if (playedTag?.correct) cls = "border-emerald-500 bg-emerald-500/20 text-emerald-300";
                      else if (playedTag && !playedTag.correct) cls = "border-red-500 bg-red-500/15 text-red-400 line-through";
                      else if (isHint) cls = "border-amber-400 bg-amber-400/15 text-amber-300 ring-2 ring-amber-400/50";

                      // Group header: insert before this tag if its bucket differs from the previous tag's bucket
                      const bucketOf = (so: number | null | undefined) =>
                        dim === "time_periods" ? timePeriodBucket(so) : (so == null ? 0 : Math.floor(so / 100));
                      const myBucket = bucketOf(item.sort_order);
                      const prevBucket = idx > 0 ? bucketOf(items[idx - 1]!.sort_order) : null;
                      const showGroupHeader = idx === 0 || myBucket !== prevBucket;
                      const groupTitle = dim === "time_periods"
                        ? TIME_PERIOD_GROUPS[myBucket]
                        : GROUP_TITLES[dim]?.[myBucket];

                      return (
                        <Fragment key={item.id}>
                        {showGroupHeader && groupTitle && (
                          <div className="mt-2 mb-1.5 w-full basis-full text-[10px] font-semibold uppercase tracking-wide text-muted-foreground/70">
                            {groupTitle}
                          </div>
                        )}
                        <span className="mr-2 mb-2 inline-flex items-center align-top sm:mr-1.5 sm:mb-1.5">
                          <button
                            disabled={busy || !!playedTag}
                            onClick={() => handleClickTag(dim, item.name)}
                            title={description}
                            className={cn(
                              "rounded-md border px-3 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed sm:px-2 sm:py-1 sm:text-xs",
                              description && "rounded-r-none",
                              cls,
                            )}
                          >
                            {item.name}
                          </button>
                          {description && (
                            <Popover>
                              <PopoverTrigger asChild>
                                <button
                                  onClick={(e) => e.stopPropagation()}
                                  className={cn(
                                    "rounded-md rounded-l-none border border-l-0 px-2 py-2 transition-colors sm:px-1 sm:py-1",
                                    playedTag?.correct
                                      ? "border-emerald-500 bg-emerald-500/20 text-emerald-300/70"
                                      : playedTag
                                        ? "border-red-500 bg-red-500/15 text-red-400/60"
                                        : isHint
                                          ? "border-amber-400 bg-amber-400/15 text-amber-300/70"
                                          : "border-border text-muted-foreground/60 hover:text-foreground",
                                  )}
                                >
                                  <Info className="h-4 w-4 sm:h-3 sm:w-3" />
                                </button>
                              </PopoverTrigger>
                              <PopoverContent
                                side="top"
                                className="w-64 px-3 py-2 text-xs"
                                onOpenAutoFocus={(e) => e.preventDefault()}
                              >
                                <p className="mb-1 font-medium">{item.name}</p>
                                <p className="text-muted-foreground">{description}</p>
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
            );
          })}
        </div>

        {busy && (
          <div className="fixed bottom-4 right-4 rounded-md border border-border bg-background px-3 py-1 text-xs text-muted-foreground shadow-lg">
            <Loader2 className="inline h-3 w-3 animate-spin" /> Checking…
          </div>
        )}
      </div>

      {modal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setModal(null)}
        >
          <div
            className="max-h-[80vh] w-full max-w-2xl overflow-auto rounded-lg border border-border bg-background p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {modal.kind === "remaining" ? "Remaining films" : "Synopsis"}
              </h3>
              <Button variant="ghost" size="icon" onClick={() => setModal(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            {modal.kind === "remaining" ? (
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
                {modal.films.map((f) => (
                  <div key={f.film_id} className="overflow-hidden rounded border border-border">
                    <div className="aspect-[2/3] bg-muted">
                      {f.poster_url && <img src={f.poster_url} alt={f.title} className="h-full w-full object-cover" />}
                    </div>
                    <div className="p-1.5 text-[11px] line-clamp-2">{f.title}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm leading-relaxed text-muted-foreground">{modal.text}</p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
