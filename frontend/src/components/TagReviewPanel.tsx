import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Download,
  FlaskConical,
  Loader2,
  Plus,
  Minus,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  applyTagReview,
  fetchPendingReviews,
  fetchReviewResults,
  getAuthHeadersRaw,
  fetchTaxonomy,
} from "@/api/client";
import { TAXONOMY_DIMENSIONS } from "@/types/api";
import type { TaxonomyItem } from "@/types/api";
import { dimensionLabel } from "@/lib/utils";

const BASE = import.meta.env.VITE_API_URL || "/api";

type Dimension = (typeof TAXONOMY_DIMENSIONS)[number];

interface FilmChange {
  film_id: number;
  title: string;
  year: number | null;
}

interface ReviewResult {
  total_reviewed: number;
  currently_tagged: number;
  should_be_tagged: number;
  to_add: FilmChange[];
  to_remove: FilmChange[];
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
}

type Phase = "idle" | "running" | "done" | "applying" | "applied";

export function TagReviewPanel() {
  const [open, setOpen] = useState(false);

  // Form state
  const [dimension, setDimension] = useState<Dimension>("categories");
  const [tag, setTag] = useState("");
  const [description, setDescription] = useState("");
  const [model, setModel] = useState("haiku");

  // Tag suggestions from taxonomy
  const [tagItems, setTagItems] = useState<TaxonomyItem[]>([]);
  const [tagError, setTagError] = useState("");

  // Progress state
  const [phase, setPhase] = useState<Phase>("idle");
  const [progressPct, setProgressPct] = useState(0);
  const [progressLabel, setProgressLabel] = useState("");

  // Result state
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [applyResult, setApplyResult] = useState<{ added: number; removed: number } | null>(null);
  const [error, setError] = useState("");

  // Pending reviews from server
  const [pendingReviews, setPendingReviews] = useState<
    { dimension: string; tag: string }[]
  >([]);
  const [loadingPending, setLoadingPending] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  const loadTagsForDimension = useCallback(async (dim: Dimension) => {
    try {
      const data = await fetchTaxonomy(dim);
      setTagItems(data.items);
    } catch {
      setTagItems([]);
    }
  }, []);

  const checkPendingReviews = useCallback(async () => {
    try {
      const data = await fetchPendingReviews();
      setPendingReviews(data.pending);
    } catch {
      setPendingReviews([]);
    }
  }, []);

  const loadPendingResult = useCallback(
    async (dim: string, t: string) => {
      setLoadingPending(true);
      setError("");
      try {
        const data = await fetchReviewResults(dim, t);
        setDimension(dim as Dimension);
        setTag(t);
        setResult(data);
        setPhase("done");
        loadTagsForDimension(dim as Dimension);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load results");
      } finally {
        setLoadingPending(false);
      }
    },
    [loadTagsForDimension],
  );

  const handleDimensionChange = useCallback(
    (dim: Dimension) => {
      setDimension(dim);
      setTag("");
      setTagError("");
      loadTagsForDimension(dim);
    },
    [loadTagsForDimension],
  );

  const handleOpenToggle = useCallback(() => {
    const next = !open;
    setOpen(next);
    if (next) {
      if (tagItems.length === 0) loadTagsForDimension(dimension);
      checkPendingReviews();
    }
  }, [open, tagItems.length, loadTagsForDimension, dimension, checkPendingReviews]);

  // Check for pending reviews on mount
  useEffect(() => {
    checkPendingReviews();
  }, [checkPendingReviews]);

  const validateTag = useCallback(() => {
    if (!tag.trim()) {
      setTagError("Tag name is required");
      return false;
    }
    const exists = tagItems.some(
      (item) => item.name.toLowerCase() === tag.trim().toLowerCase(),
    );
    if (!exists) {
      setTagError(
        `Tag "${tag}" not found in ${dimensionLabel(dimension)}. Check spelling.`,
      );
      return false;
    }
    setTagError("");
    return true;
  }, [tag, tagItems, dimension]);

  const handleRun = useCallback(async () => {
    if (!validateTag()) return;

    setPhase("running");
    setProgressPct(0);
    setProgressLabel("Starting review...");
    setResult(null);
    setApplyResult(null);
    setError("");

    const params = new URLSearchParams({
      dimension,
      tag: tag.trim(),
      model,
      batch_size: "10",
    });
    if (description.trim()) {
      params.set("description", description.trim());
    }

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const auth = await getAuthHeadersRaw();
      const res = await fetch(`${BASE}/tag-review/run?${params}`, {
        headers: auth,
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n\n");
        buffer = parts.pop()!;

        for (const part of parts) {
          const lines = part.split("\n");
          let eventType = "";
          let eventData = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) eventType = line.slice(7);
            else if (line.startsWith("data: ")) eventData = line.slice(6);
          }
          if (!eventType || !eventData) continue;

          const data = JSON.parse(eventData);

          if (eventType === "progress") {
            const pct = Math.round(
              (data.films_reviewed / data.total_films) * 100,
            );
            setProgressPct(pct);
            setProgressLabel(
              `Batch ${data.batch}/${data.total_batches} — ${data.films_reviewed}/${data.total_films} films — ${Math.round(data.input_tokens / 1000)}K tokens`,
            );
          } else if (eventType === "started") {
            const resumed = data.resumed_from
              ? ` (resumed, ${data.resumed_from} already done)`
              : "";
            setProgressLabel(
              `Reviewing ${data.total_films} films (${data.total_batches} batches)${resumed}...`,
            );
          } else if (eventType === "result") {
            setResult(data);
            setPhase("done");
          } else if (eventType === "error") {
            setError(data.message);
            setPhase("idle");
          }
        }
      }

      if (phase === "running") setPhase("done");
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError") {
        setError(e instanceof Error ? e.message : "Review failed");
        setPhase("idle");
      }
    }
  }, [dimension, tag, description, model, validateTag, phase]);

  const handleApply = useCallback(async () => {
    setPhase("applying");
    setError("");
    try {
      const res = await applyTagReview(dimension, tag.trim());
      setApplyResult(res);
      setPhase("applied");
      checkPendingReviews();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Apply failed");
      setPhase("done");
    }
  }, [dimension, tag, checkPendingReviews]);

  const handleReset = useCallback(() => {
    setPhase("idle");
    setResult(null);
    setApplyResult(null);
    setError("");
    setProgressPct(0);
    setProgressLabel("");
  }, []);

  const hasChanges =
    result && (result.to_add.length > 0 || result.to_remove.length > 0);

  return (
    <div className="mt-8 rounded-lg border border-border">
      {/* Header toggle */}
      <button
        onClick={handleOpenToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-accent/50 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">Tag Review (AI)</span>
          {pendingReviews.length > 0 && !open && (
            <span className="rounded-full bg-amber-500 px-1.5 py-0.5 text-[10px] font-medium text-white">
              {pendingReviews.length} pending
            </span>
          )}
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {open && (
        <div className="border-t border-border px-4 py-4 space-y-4">
          {/* Pending reviews banner */}
          {pendingReviews.length > 0 && phase === "idle" && (
            <div className="rounded-md border border-amber-500/30 bg-amber-500/5 px-4 py-3 space-y-2">
              <p className="text-xs font-medium flex items-center gap-1.5">
                <Download className="h-3.5 w-3.5 text-amber-500" />
                Pending review results found:
              </p>
              <div className="flex flex-wrap gap-2">
                {pendingReviews.map((p) => (
                  <div key={`${p.dimension}_${p.tag}`} className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs gap-1"
                      disabled={loadingPending}
                      onClick={() => loadPendingResult(p.dimension, p.tag)}
                    >
                      <Download className="h-3 w-3" />
                      {dimensionLabel(p.dimension)}: {p.tag}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs gap-1"
                      disabled={loadingPending}
                      onClick={() => {
                        setDimension(p.dimension as Dimension);
                        setTag(p.tag);
                        loadTagsForDimension(p.dimension as Dimension);
                      }}
                    >
                      <FlaskConical className="h-3 w-3" />
                      Resume
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Form */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {/* Dimension */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                Dimension
              </label>
              <Select
                value={dimension}
                onValueChange={(v) => handleDimensionChange(v as Dimension)}
                disabled={phase === "running"}
              >
                <SelectTrigger className="h-9 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TAXONOMY_DIMENSIONS.map((dim) => (
                    <SelectItem key={dim} value={dim}>
                      {dimensionLabel(dim)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Tag */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                Tag
              </label>
              <div className="relative">
                <Input
                  value={tag}
                  onChange={(e) => {
                    setTag(e.target.value);
                    setTagError("");
                  }}
                  placeholder="Type tag name..."
                  className={`h-9 text-sm ${tagError ? "border-destructive" : ""}`}
                  disabled={phase === "running"}
                  list="tag-suggestions"
                />
                <datalist id="tag-suggestions">
                  {tagItems.map((item) => (
                    <option key={item.id} value={item.name} />
                  ))}
                </datalist>
              </div>
              {tagError && (
                <p className="text-xs text-destructive">{tagError}</p>
              )}
            </div>

            {/* Model */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                Model
              </label>
              <Select
                value={model}
                onValueChange={setModel}
                disabled={phase === "running"}
              >
                <SelectTrigger className="h-9 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="haiku">Haiku 4.5 (fast, cheap)</SelectItem>
                  <SelectItem value="sonnet">Sonnet 4.6 (accurate)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Description */}
            <div className="space-y-1 sm:col-span-2">
              <label className="text-xs font-medium text-muted-foreground">
                Tag description (optional — helps Claude understand the intent)
              </label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={`e.g. "films with strong sensuality, eroticism, or sexually explicit scenes"`}
                className="min-h-[60px] text-sm"
                disabled={phase === "running"}
              />
            </div>
          </div>

          {/* Run button */}
          {(phase === "idle" || phase === "applied") && (
            <Button
              onClick={handleRun}
              className="gap-2"
              disabled={!tag.trim()}
            >
              <FlaskConical className="h-4 w-4" />
              Run Review
            </Button>
          )}

          {/* Progress */}
          {phase === "running" && (
            <div className="space-y-2">
              <Progress value={progressPct} className="h-2" />
              <p className="text-xs text-muted-foreground">{progressLabel}</p>
              <p className="text-xs text-amber-500 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Stay on this page until review completes. Progress is saved after each batch.
              </p>
            </div>
          )}

          {/* Error */}
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          {/* Results */}
          {result && (phase === "done" || phase === "applying" || phase === "applied") && (
            <div className="space-y-3">
              {/* Summary */}
              <div className="rounded-md bg-muted/50 px-4 py-3 text-sm space-y-1">
                <p>
                  Reviewed <strong>{result.total_reviewed}</strong> films
                </p>
                <p>
                  Currently tagged: <strong>{result.currently_tagged}</strong> —
                  Should be: <strong>{result.should_be_tagged}</strong>
                </p>
                <p>
                  To add: <strong className="text-emerald-500">{result.to_add.length}</strong> —
                  To remove: <strong className="text-destructive">{result.to_remove.length}</strong>
                </p>
                <p className="text-xs text-muted-foreground">
                  Tokens: {(result.input_tokens / 1000).toFixed(0)}K in + {(result.output_tokens / 1000).toFixed(0)}K out — Est. cost: ${result.estimated_cost}
                </p>
              </div>

              {/* Films to add */}
              {result.to_add.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-emerald-500 mb-1">
                    Films to ADD ({result.to_add.length})
                  </h4>
                  <div className="max-h-48 overflow-y-auto rounded border border-border text-xs">
                    {result.to_add.map((f) => (
                      <div
                        key={f.film_id}
                        className="flex items-center gap-2 px-3 py-1.5 border-b border-border last:border-b-0"
                      >
                        <Plus className="h-3 w-3 shrink-0 text-emerald-500" />
                        <span>
                          {f.title} ({f.year ?? "?"})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Films to remove */}
              {result.to_remove.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-destructive mb-1">
                    Films to REMOVE ({result.to_remove.length})
                  </h4>
                  <div className="max-h-48 overflow-y-auto rounded border border-border text-xs">
                    {result.to_remove.map((f) => (
                      <div
                        key={f.film_id}
                        className="flex items-center gap-2 px-3 py-1.5 border-b border-border last:border-b-0"
                      >
                        <Minus className="h-3 w-3 shrink-0 text-destructive" />
                        <span>
                          {f.title} ({f.year ?? "?"})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Apply / Reset buttons */}
              <div className="flex gap-2">
                {phase === "done" && hasChanges && (
                  <Button onClick={handleApply} className="gap-2">
                    <Check className="h-4 w-4" />
                    Apply Changes
                  </Button>
                )}
                {phase === "applying" && (
                  <Button disabled className="gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Applying...
                  </Button>
                )}
                {phase === "applied" && (
                  <p className="text-sm text-emerald-500">
                    Applied: {applyResult?.added} added, {applyResult?.removed} removed
                  </p>
                )}
                {(phase === "done" || phase === "applied") && (
                  <Button variant="outline" onClick={handleReset}>
                    New Review
                  </Button>
                )}
              </div>

              {!hasChanges && phase === "done" && (
                <p className="text-sm text-muted-foreground">
                  No changes needed — tagging is already correct.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
