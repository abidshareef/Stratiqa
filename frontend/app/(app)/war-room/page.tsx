"use client";

import { useEffect, useState } from "react";
import { Activity, Brain, Lightbulb, Target, TriangleAlert } from "lucide-react";

import { ApiError, apiFetch } from "@/lib/api";
import type { WarRoom } from "@/lib/types";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { Empty, Section, SkeletonBlock } from "@/components/dashboard/primitives";

export default function WarRoomPage() {
  const [data, setData] = useState<WarRoom | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiFetch<WarRoom>("/stratiqa-one/war-room")
      .then((d) => active && setData(d))
      .catch(
        (e) =>
          active &&
          setError(e instanceof ApiError ? e.message : "Failed to load war room."),
      );
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return (
      <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="space-y-4">
        <SkeletonBlock className="h-10 w-64" />
        <div className="grid gap-4 lg:grid-cols-2">
          <SkeletonBlock className="h-48" />
          <SkeletonBlock className="h-48" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="animate-rise flex items-center gap-3">
        <TriangleAlert className="size-6 text-danger" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Executive War Room
          </h1>
          <p className="text-sm text-muted">
            Single-screen command center — what needs your attention now.
          </p>
        </div>
      </section>

      {/* Top row: critical risks + activity timeline */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Critical risks">
          {data.critical_risks.length === 0 ? (
            <Empty>No critical risks.</Empty>
          ) : (
            <div className="space-y-2">
              {data.critical_risks.map((r, i) => (
                <Card key={i}>
                  <CardContent className="flex items-start gap-3 p-4">
                    <TriangleAlert className="mt-0.5 size-4 shrink-0 text-danger" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">{r.title}</p>
                        <Badge tone={toneForLevel(r.level)}>{r.level}</Badge>
                      </div>
                      <p className="mt-0.5 text-xs text-muted">{r.context}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </Section>

        <Section title="Business events">
          <Card>
            <CardContent className="p-4">
              {data.business_events.length === 0 ? (
                <p className="text-xs text-muted-foreground">No recent events.</p>
              ) : (
                <ol className="relative space-y-4 border-l border-border pl-4">
                  {data.business_events.map((e, i) => (
                    <li key={i} className="relative">
                      <span className="absolute -left-[21px] top-1 flex size-3 items-center justify-center rounded-full border border-border bg-primary/20">
                        <Activity className="size-2 text-primary" />
                      </span>
                      <p className="text-sm">{e.title}</p>
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        {e.type.replace(/_/g, " ")}
                        {e.at ? ` · ${new Date(e.at).toLocaleDateString()}` : ""}
                      </p>
                    </li>
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>
        </Section>
      </div>

      {/* Goals + Projects quick status */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Strategic goals">
          <div className="space-y-2">
            {data.goals.map((g) => (
              <Card key={g.id}>
                <CardContent className="flex items-center justify-between gap-2 p-4">
                  <div className="flex items-center gap-2">
                    <Target className="size-4 text-info" />
                    <span className="text-sm font-medium">{g.title}</span>
                  </div>
                  <Badge tone={toneForLevel(g.status)}>{g.status}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </Section>

        <Section title="Active projects">
          <div className="space-y-2">
            {data.projects.map((p) => (
              <Card key={p.id}>
                <CardContent className="flex items-center justify-between gap-2 p-4">
                  <span className="text-sm font-medium">{p.name}</span>
                  <Badge tone={toneForLevel(p.status)}>{p.status}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </Section>
      </div>

      {/* Opportunities + Twin insights */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Opportunities">
          <div className="space-y-2">
            {data.opportunities.map((o, i) => (
              <Card key={i}>
                <CardContent className="flex items-start gap-3 p-4">
                  <Lightbulb className="mt-0.5 size-4 shrink-0 text-warning" />
                  <div>
                    <p className="text-sm font-medium">{o.title}</p>
                    {o.estimated_impact && (
                      <p className="metric mt-0.5 text-xs text-success">
                        {o.estimated_impact}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </Section>

        <Section title="Business Twin insights">
          <Card>
            <CardContent className="space-y-3 p-4">
              {data.twin_insights.map((t, i) => (
                <div key={i} className="flex items-start gap-3">
                  <Brain className="mt-0.5 size-4 shrink-0 text-primary" />
                  <p className="text-sm text-muted">{t}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </Section>
      </div>

      <Section title="Recommendations">
        {data.recommendations.length === 0 ? (
          <Empty>No recommendations pending.</Empty>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {data.recommendations.map((rec) => (
              <RecommendationCard key={rec.id} rec={rec} />
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
