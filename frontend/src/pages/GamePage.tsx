import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Film, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GameSetup } from "@/components/game/GameSetup";
import { GameBoard, type GameState } from "@/components/game/GameBoard";
import { GameResult } from "@/components/game/GameResult";
import type { GameFilm, GamePoolFilters, GameSetupResponse } from "@/types/api";

type Phase = "setup" | "playing" | "result";

export function GamePage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("setup");
  const [mode, setMode] = useState<"daily" | "free">("daily");
  const [setup, setSetup] = useState<GameSetupResponse | null>(null);
  const [target, setTarget] = useState<GameFilm | null>(null);
  const [poolFilters, setPoolFilters] = useState<GamePoolFilters | undefined>();
  const [finalState, setFinalState] = useState<GameState | null>(null);
  const [victory, setVictory] = useState(false);

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
          <Film className="h-4 w-4 text-primary" />
          Film Database
        </button>
        <div className="text-sm font-semibold tracking-wide">🎬 Tag It</div>
        <Button variant="ghost" size="icon" onClick={() => navigate("/browse")}>
          <Home className="h-4 w-4" />
        </Button>
      </header>

      {phase === "setup" && <GameSetup onStart={handleStart} />}
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
          onPlayAgain={handlePlayAgain}
          onHome={() => navigate("/browse")}
        />
      )}
    </div>
  );
}
