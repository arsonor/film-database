import { useNavigate } from "react-router-dom";
import { BarChart3, Home, Link2, Search, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";

interface GameCardProps {
  icon: typeof Target;
  title: string;
  emoji: string;
  tagline: string;
  description: string;
  onPlay: () => void;
  accent: string;
}

function GameCard({ icon: Icon, title, emoji, tagline, description, onPlay, accent }: GameCardProps) {
  return (
    <button
      onClick={onPlay}
      className={`group flex flex-col items-center gap-4 rounded-2xl border-2 ${accent} bg-card/40 p-8 text-center transition-all hover:scale-[1.02] hover:shadow-xl`}
    >
      <div className="text-5xl">{emoji}</div>
      <div className="flex items-center gap-2 text-2xl font-bold tracking-tight">
        <Icon className="h-6 w-6" /> {title}
      </div>
      <p className="text-base font-medium text-foreground/90">{tagline}</p>
      <p className="text-sm text-muted-foreground">{description}</p>
      <span className="mt-2 rounded-md bg-primary px-6 py-2 text-sm font-semibold text-primary-foreground group-hover:bg-primary/90">
        Play
      </span>
    </button>
  );
}

export function GameHubPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

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
        <div className="text-sm font-semibold tracking-wide">🎮 Games</div>
        <div className="flex items-center gap-1">
          {isAuthenticated && (
            <button
              onClick={() => navigate("/game/stats")}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
              title="Stats & History"
            >
              <BarChart3 className="h-3.5 w-3.5" /> <span className="hidden sm:inline">Stats & History</span>
            </button>
          )}
          <Button variant="ghost" size="icon" onClick={() => navigate("/browse")}>
            <Home className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col items-center gap-8 px-4 py-10">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Choose your game</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Three ways to test your cinema knowledge. Daily challenges and free play.
          </p>
        </div>

        <div className="grid w-full grid-cols-1 gap-6 md:grid-cols-3">
          <GameCard
            icon={Target}
            title="Tag It"
            emoji="🎬"
            tagline="Isolate a film using as few tags as possible"
            description="Pick a film, narrow down to it with the smallest number of correct tags. 3 lives, 3 lifelines."
            onPlay={() => navigate("/game/tag-it")}
            accent="border-primary/40 hover:border-primary"
          />
          <GameCard
            icon={Link2}
            title="Chain It"
            emoji="🔗"
            tagline="Connect two distant films through shared tags"
            description="Build a chain of films linked by shared tags from origin to target. 3 lives, 3 lifelines."
            onPlay={() => navigate("/game/chain-it")}
            accent="border-amber-500/40 hover:border-amber-500"
          />
          <GameCard
            icon={Search}
            title="Guess It"
            emoji="🔍"
            tagline="Eliminate films as tags are revealed"
            description="Find the hidden film by removing decoys one by one. Wrong removals cost lives. 3 lives, 3 lifelines."
            onPlay={() => navigate("/game/guess-it")}
            accent="border-emerald-500/40 hover:border-emerald-500"
          />
        </div>

      </main>
    </div>
  );
}
