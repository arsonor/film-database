import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart3, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GuessSetup } from "@/components/game/GuessSetup";
import { GuessBoard, type GuessBoardState } from "@/components/game/GuessBoard";
import { GuessResult } from "@/components/game/GuessResult";
import type { GameFilm, GamePoolFilters, GuessSetupResponse } from "@/types/api";

type Phase = "setup" | "playing" | "result";

export function GuessItPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("setup");
  const [mode, setMode] = useState<"daily" | "free">("daily");
  const [grid, setGrid] = useState<GameFilm[]>([]);
  const [targetFilmId, setTargetFilmId] = useState<number>(0);
  const [poolFilters, setPoolFilters] = useState<GamePoolFilters | undefined>();
  const [decadeLocked, setDecadeLocked] = useState(false);
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [finalState, setFinalState] = useState<GuessBoardState | null>(null);
  const [victory, setVictory] = useState(false);

  useEffect(() => {
    if (phase === "result") window.scrollTo({ top: 0, behavior: "auto" });
  }, [phase]);

  function handleStart(
    m: "daily" | "free",
    s: GuessSetupResponse,
    pf?: GamePoolFilters,
    diff?: "easy" | "medium" | "hard",
    decLocked?: boolean,
  ) {
    setMode(m);
    setGrid(s.grid);
    setTargetFilmId(s.target_film_id);
    setPoolFilters(pf);
    setDifficulty(diff ?? "medium");
    setDecadeLocked(!!decLocked);
    setPhase("playing");
  }

  function handleVictory(state: GuessBoardState) {
    setFinalState(state); setVictory(true); setPhase("result");
  }
  function handleGameOver(state: GuessBoardState) {
    setFinalState(state); setVictory(false); setPhase("result");
  }
  function handlePlayAgain() {
    setPhase("setup"); setGrid([]); setTargetFilmId(0); setFinalState(null);
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur">
        <button
          onClick={() => navigate("/browse")}
          className="flex items-center gap-2 text-sm font-medium hover:text-primary"
        >
          <img src="/cinetag-logo/cinetag_logo.svg" alt="CineTag" className="h-5 w-5" />
          CineTag
        </button>
        <div className="text-sm font-semibold tracking-wide">🔍 Guess It</div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => navigate("/game/stats")}
            className="hidden items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground sm:inline-flex"
          >
            <BarChart3 className="h-3.5 w-3.5" /> Stats
          </button>
          <Button variant="ghost" size="icon" onClick={() => navigate("/browse")}>
            <Home className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {phase === "setup" && <GuessSetup onStart={handleStart} />}
      {phase === "playing" && grid.length > 0 && (
        <GuessBoard
          grid={grid}
          targetFilmId={targetFilmId}
          decadeLocked={decadeLocked}
          difficulty={difficulty}
          onVictory={handleVictory}
          onGameOver={handleGameOver}
        />
      )}
      {phase === "result" && finalState && (
        <GuessResult
          grid={grid}
          targetFilmId={targetFilmId}
          state={finalState}
          victory={victory}
          mode={mode}
          difficulty={difficulty}
          poolFilters={poolFilters}
          onPlayAgain={handlePlayAgain}
          onHome={() => navigate("/game")}
        />
      )}
    </div>
  );
}
