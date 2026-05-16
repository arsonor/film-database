import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, BarChart3, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GameSetup } from "@/components/game/GameSetup";
import { GameBoard, type GameState } from "@/components/game/GameBoard";
import { GameResult } from "@/components/game/GameResult";
import type { GameFilm, GamePoolFilters, GameSetupResponse } from "@/types/api";

type Phase = "setup" | "playing" | "result";

export function TagItPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("setup");
  const [mode, setMode] = useState<"daily" | "free">("daily");
  const [setup, setSetup] = useState<GameSetupResponse | null>(null);
  const [target, setTarget] = useState<GameFilm | null>(null);
  const [poolFilters, setPoolFilters] = useState<GamePoolFilters | undefined>();
  const [finalState, setFinalState] = useState<GameState | null>(null);
  const [victory, setVictory] = useState(false);

  useEffect(() => {
    if (phase === "result") {
      window.scrollTo({ top: 0, behavior: "auto" });
    }
  }, [phase]);

  function handleStart(
    m: "daily" | "free",
    s: GameSetupResponse,
    t: GameFilm,
    pf?: GamePoolFilters,
  ) {
    setMode(m);
    setSetup(s);
    setTarget(t);
    setPoolFilters(pf);
    setPhase("playing");
  }

  function handleVictory(state: GameState) {
    setFinalState(state);
    setVictory(true);
    setPhase("result");
  }

  function handleGameOver(state: GameState) {
    setFinalState(state);
    setVictory(false);
    setPhase("result");
  }

  function handlePlayAgain() {
    setPhase("setup");
    setSetup(null);
    setTarget(null);
    setFinalState(null);
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
        <div className="text-sm font-semibold tracking-wide">🎬 Tag It</div>
        <div className="flex items-center gap-1">
          <Link
            to="/game/stats"
            className="hidden items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground sm:inline-flex"
          >
            <BarChart3 className="h-3.5 w-3.5" /> Stats
          </Link>
          <Button variant="ghost" size="icon" onClick={() => navigate("/browse")}>
            <Home className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {phase === "setup" && (
        <>
          <div className="mx-auto flex max-w-4xl px-4 pt-4">
            <Link
              to="/game"
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Back to Games
            </Link>
          </div>
          <GameSetup onStart={handleStart} />
        </>
      )}
      {phase === "playing" && target && setup && (
        <GameBoard
          target={target}
          poolSize={setup.pool_size}
          poolFilters={poolFilters}
          onVictory={handleVictory}
          onGameOver={handleGameOver}
        />
      )}
      {phase === "result" && target && finalState && (
        <GameResult
          target={target}
          state={finalState}
          victory={victory}
          mode={mode}
          poolFilters={poolFilters}
          onPlayAgain={handlePlayAgain}
          onHome={() => navigate("/game")}
        />
      )}
    </div>
  );
}
