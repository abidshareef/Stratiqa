"use client";

import { useCallback, useEffect, useState } from "react";
import { Send, Sparkles } from "lucide-react";

import { askAgent, getAgent, getAgents } from "@/lib/api";
import type {
  AgentAskResponse,
  AgentDetail,
  AgentInsight,
  AgentRoster,
} from "@/lib/types";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, SkeletonBlock } from "@/components/dashboard/primitives";

const sevTone = (s: string) => toneForLevel(s);
const statusDot = "inline-block size-2 rounded-full bg-success";

export default function AgentsPage() {
  const [roster, setRoster] = useState<AgentRoster | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<AgentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState<AgentAskResponse | null>(null);

  useEffect(() => {
    let active = true;
    getAgents()
      .then((r) => {
        if (!active) return;
        setRoster(r);
        setSelected(r.agents[0]?.agent_type ?? null);
      })
      .catch(() => active && setError("Failed to load the agent team."));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selected) return;
    let active = true;
    getAgent(selected)
      .then((d) => active && setDetail(d))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [selected]);

  // Reset is driven by the user action, never synchronously inside an effect.
  function select(agentType: string) {
    setSelected(agentType);
    setAnswer(null);
    setQuery("");
  }

  // Only show detail once it matches the selected agent (avoids stale flashes).
  const shownDetail = detail && detail.agent_type === selected ? detail : null;

  const ask = useCallback(async () => {
    if (!selected || !query.trim()) return;
    setAsking(true);
    try {
      setAnswer(await askAgent(selected, query.trim()));
    } catch {
      /* ignore */
    } finally {
      setAsking(false);
    }
  }, [selected, query]);

  if (error) {
    return (
      <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="AI Agents"
        subtitle="A team of specialist agents, each reasoning over its own domain. Every finding is grounded in your data and explainable."
      />

      {!roster ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonBlock key={i} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          {/* Roster */}
          <div className="grid gap-3 sm:grid-cols-2">
            {roster.agents.map((a) => {
              const active = a.agent_type === selected;
              return (
                <button
                  key={a.agent_type}
                  onClick={() => select(a.agent_type)}
                  className={`rounded-lg border p-4 text-left transition-colors ${
                    active
                      ? "border-primary/50 bg-card"
                      : "border-border bg-card/60 hover:bg-card"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={statusDot} />
                      <span className="text-sm font-medium">{a.name}</span>
                    </div>
                    <Badge tone={sevTone(a.top_severity)}>
                      {a.insight_count}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{a.domain}</p>
                  <p className="mt-2 line-clamp-2 text-xs text-foreground/80">
                    {a.headline}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Detail panel */}
          <div className="space-y-4">
            {!shownDetail ? (
              <SkeletonBlock className="h-64" />
            ) : (
              <>
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles className="size-4 text-primary" />
                    <h2 className="text-sm font-semibold">{shownDetail.name}</h2>
                  </div>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {shownDetail.domain}
                  </p>
                </div>

                {shownDetail.insights.length === 0 ? (
                  <Empty>No signals in your data yet.</Empty>
                ) : (
                  <div className="space-y-2">
                    {shownDetail.insights.map((ins, i) => (
                      <InsightCard key={i} insight={ins} />
                    ))}
                  </div>
                )}

                {/* Ask this agent */}
                <Card>
                  <CardContent className="space-y-2 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                      Ask {shownDetail.name}
                    </p>
                    <div className="flex gap-2">
                      <Input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && ask()}
                        placeholder="Ask a question…"
                      />
                      <Button size="sm" onClick={ask} disabled={asking}>
                        <Send className="size-4" />
                      </Button>
                    </div>
                    {answer && (
                      <div className="rounded-md border border-border bg-surface/50 p-3">
                        <p className="text-sm leading-relaxed text-foreground/90">
                          {answer.answer}
                        </p>
                        <p className="mt-2 text-[11px] text-muted-foreground">
                          {answer.confidence_score.toFixed(0)}% confidence ·{" "}
                          {answer.data_sources.join(", ") || "no sources"}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function InsightCard({ insight }: { insight: AgentInsight }) {
  return (
    <Card>
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-medium">{insight.title}</p>
          <Badge tone={sevTone(insight.severity)}>{insight.severity}</Badge>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{insight.finding}</p>
        {insight.recommended_action && (
          <p className="mt-1.5 text-xs text-info">→ {insight.recommended_action}</p>
        )}
        <p className="mt-2 text-[11px] text-muted-foreground">
          {insight.confidence_score.toFixed(0)}% confidence ·{" "}
          {insight.data_sources.join(", ")}
        </p>
      </CardContent>
    </Card>
  );
}
