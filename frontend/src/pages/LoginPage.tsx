import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/AuthContext";

export function LoginPage() {
  const navigate = useNavigate();
  const { isAdmin, login } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAdmin) navigate("/browse", { replace: true });
  }, [isAdmin, navigate]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError("");
      setSubmitting(true);
      try {
        await login(password);
        navigate("/browse");
      } catch {
        setError("Invalid password");
      } finally {
        setSubmitting(false);
      }
    },
    [password, login, navigate],
  );

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-8">
        <div className="text-center">
          <LogIn className="mx-auto h-8 w-8 text-primary" />
          <h1 className="mt-3 text-xl font-semibold text-foreground">Admin Login</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
          <Button type="submit" className="w-full" disabled={submitting || !password}>
            {submitting ? "Logging in..." : "Login"}
          </Button>
        </form>
      </div>
    </div>
  );
}
