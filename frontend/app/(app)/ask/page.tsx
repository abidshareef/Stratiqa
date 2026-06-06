"use client";

import { useRef, useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";

import { apiFetch, ApiError } from "@/lib/api";
import type { AskResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Turn {
  query: string;
  response: AskResponse | null;
  error?: string;
}

const SUGGESTIONS = [
  "What are my biggest risks right now?",
  "How are my strategic goals tracking?",
  "What should I do next?",
  "Show me my active projects.",
];

export default function AskPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function ask(q: string) {
    const text = q.trim();
    if (!text || busy) return;
    setQuery("");
    setBusy(true);
    const idx = turns.length;
    setTurns((t) => [...t, { query: text, response: null }]);
    try {
      const res = await apiFetch<AskResponse>("/stratiqa-one/ask", {
        method: "POST",
        body: { query: text },
      });
      setTurns((t) =>
        t.map((turn, i) => (i === idx ? { ...turn, response: res } : turn)),
      );
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Something went wrong.";
      setTurns((t) =>
        t.map((turn, i) => (i === idx ? { ...turn, error: msg } : turn)),
      );
    } finally {
      setBusy(false);
      requestAnimationFrame(() =>
        scrollRef.current?.scrollTo({
          top: scrollRef.current.scrollHeight,
          behavior: "smooth",
        }),
      );
    }
  }

  return (
    <div className="flex h-[calc(100vh-7.5rem)] flex-col">
      <section className="animate-rise mb-4 flex items-center gap-3">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary/15">
          <Sparkles className="size-5 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            Ask STRATIQA One
          </h1>
          <p className="text-sm text-muted">
            Grounded answers from your operating data.
          </p>
        </div>
      </section>

      <div ref={scrollRef} className="flex-1 space-y-6 overflow-y-auto pb-4">
        {turns.length === 0 && (
          <div className="grid gap-2 sm:grid-cols-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                className="rounded-lg border border-border bg-card p-3 text-left text-sm text-muted transition-colors hover:border-primary/40 hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {turns.map((turn, i) => (
          <div key={i} className="space-y-3">
            {/* user */}
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-lg rounded-br-sm bg-primary px-4 py-2 text-sm text-primary-foreground">
                {turn.query}
              </div>
            </div>

            {/* assistant */}
            <div className="flex gap-3">
              <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary/15">
                <Sparkles className="size-4 text-primary" />
              </div>
              <div className="min-w-0 flex-1 space-y-2">
                {turn.error ? (
                  <p className="text-sm text-danger">{turn.error}</p>
                ) : !turn.response ? (
                  <p className="text-sm text-muted-foreground">
                    <span className="inline-block animate-pulse">Thinking…</span>
                  </p>
                ) : (
                  <>
                    <p className="text-sm leading-relaxed">
                      {turn.response.answer}
                    </p>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="info">
                        {turn.response.confidence_score.toFixed(0)}% confidence
                      </Badge>
                      {turn.response.data_sources.map((s) => (
                        <span
                          key={s}
                          className="metric rounded border border-border bg-surface px-1.5 py-0.5 text-[11px] text-muted-foreground"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                    {turn.response.related_recommendations.length > 0 && (
                      <div className="space-y-1 pt-1">
                        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                          Related recommendations
                        </p>
                        {turn.response.related_recommendations.map((r) => (
                          <div
                            key={r.id}
                            className="rounded-md border border-border bg-card px-3 py-2 text-xs"
                          >
                            <span className="font-medium">{r.title}</span>
                            <span className="metric ml-2 text-muted-foreground">
                              {r.confidence_score.toFixed(0)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(query);
        }}
        className="flex items-center gap-2 border-t border-border pt-4"
      >
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about risks, goals, projects, or what to do next…"
          disabled={busy}
        />
        <Button type="submit" size="icon" disabled={busy || !query.trim()}>
          <ArrowUp />
        </Button>
      </form>
    </div>
  );
}
