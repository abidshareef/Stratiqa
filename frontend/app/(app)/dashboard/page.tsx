"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { ApiError, apiFetch } from "@/lib/api";
import { areaTrend, C, gauge, healthBars } from "@/lib/charts";
import type {
  AnalyticsOverview,
  ExecutiveHome,
  RecommendationOut,
} from "@/lib/types";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EChart } from "@/components/charts/echart";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { Empty, Section, SkeletonBlock } from "@/components/dashboard/primitives";

export default function DashboardPage() {
  const [home, setHome] = useState<ExecutiveHome | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch only — state is set by callers (keeps effects free of setState).
  const fetchAll = useCallback(
    () =>
      Promise.all([
        apiFetch<ExecutiveHome>("/stratiqa-one/home"),
        apiFetch<AnalyticsOverview>("/analytics/overview"),
      ]),
    [],
  );

  useEffect(() => {
    let active = true;
    fetchAll()
      .then(([h, a]) => {
        if (!active) return;
        setHome(h);
        setAnalytics(a);
      })
      .catch(
        (e) =>
          active &&
          setError(e instanceof ApiError ? e.message : "Failed to load dashboard."),
      );
    return () => {
      active = false;
    };
  }, [fetchAll]);

  async function refreshRecs() {
    setRefreshing(true);
    try {
      await apiFetch<RecommendationOut[]>("/recommendations/refresh", {
        method: "POST",
      });
      const [h, a] = await fetchAll();
      setHome(h);
      setAnalytics(a);
    } catch {
      /* surfaced on next load */
    } finally {
      setRefreshing(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }

  if (!home || !analytics) {
    return (
      <div className="space-y-6">
        <SkeletonBlock className="h-16" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonBlock key={i} className="h-28" />
          ))}
        </div>
        <SkeletonBlock className="h-56" />
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Briefing line */}
      <section className="animate-rise space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">{home.welcome}</h1>
        <p className="text-sm text-muted">{home.summary}</p>
      </section>

      {/* ===================== INTELLIGENCE FIRST ===================== */}

      <Section title="Today's priorities">
        {home.todays_priorities.length === 0 ? (
          <Empty>Nothing urgent. You&apos;re clear.</Empty>
        ) : (
          <div className="space-y-2">
            {home.todays_priorities.map((p, i) => (
              <Card key={i} className="animate-rise">
                <CardContent className="flex items-start justify-between gap-3 p-4">
                  <div className="flex items-start gap-3">
                    <span
                      className="mt-1 h-2 w-2 shrink-0 rounded-full"
                      style={{
                        backgroundColor:
                          p.severity === "danger"
                            ? C.danger
                            : p.severity === "warning"
                              ? C.warning
                              : C.info,
                      }}
                    />
                    <div>
                      <p className="text-sm font-medium">{p.title}</p>
                      <p className="text-xs text-muted">{p.detail}</p>
                    </div>
                  </div>
                  <Badge tone="neutral">{p.source}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </Section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Critical risks">
          {home.risks.length === 0 ? (
            <Empty>No elevated risks detected.</Empty>
          ) : (
            <div className="space-y-2">
              {home.risks.map((r, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">{r.title}</p>
                      <Badge tone={toneForLevel(r.level)}>{r.level}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted">{r.context}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </Section>

        <Section title="Opportunities">
          {home.opportunities.length === 0 ? (
            <Empty>No new opportunities surfaced.</Empty>
          ) : (
            <div className="space-y-2">
              {home.opportunities.map((o, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <p className="text-sm font-medium">{o.title}</p>
                    {o.estimated_impact && (
                      <p className="mt-1 metric text-xs text-success">
                        {o.estimated_impact}
                      </p>
                    )}
                    {o.recommendation && (
                      <p className="mt-1 text-xs text-muted">{o.recommendation}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </Section>
      </div>

      <Section
        title="Recommendations"
        subtitle="Grounded in your data — review and act"
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={refreshRecs}
            disabled={refreshing}
          >
            <RefreshCw className={refreshing ? "animate-spin" : ""} />
            Refresh
          </Button>
        }
      >
        {home.recommendations.length === 0 ? (
          <Empty>No recommendations pending.</Empty>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {home.recommendations.map((rec) => (
              <RecommendationCard key={rec.id} rec={rec} />
            ))}
          </div>
        )}
      </Section>

      {/* ===================== ANALYTICS BELOW ===================== */}

      <div className="border-t border-border pt-8">
        <Section title="Performance" subtitle="Live KPIs from your operating data">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {analytics.kpis.map((k) => (
              <KpiCard key={k.key} kpi={k} />
            ))}
          </div>
        </Section>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Monthly revenue trend</CardTitle>
          </CardHeader>
          <CardContent>
            <EChart
              option={areaTrend(
                analytics.revenue_trend.labels,
                analytics.revenue_trend.values,
              )}
              height={240}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Project health</CardTitle>
          </CardHeader>
          <CardContent>
            <EChart
              option={healthBars(
                analytics.project_health.map((p) => ({
                  name: p.name,
                  score: p.score,
                })),
              )}
              height={Math.max(120, analytics.project_health.length * 56)}
            />
          </CardContent>
        </Card>
      </div>

      <Section title="Strategic goals">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {analytics.goal_progress.map((g, i) => {
            const color =
              g.progress >= 66 ? C.success : g.progress >= 33 ? C.warning : C.danger;
            return (
              <Card key={i} className="animate-rise">
                <CardContent className="flex items-center gap-4 p-4">
                  <div className="size-24 shrink-0">
                    <EChart option={gauge(g.progress, color)} height={96} />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{g.title}</p>
                    {g.target_date && (
                      <p className="text-xs text-muted-foreground">
                        Target {g.target_date}
                      </p>
                    )}
                    <Badge tone={toneForLevel(g.status)} className="mt-2">
                      {g.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </Section>
    </div>
  );
}
