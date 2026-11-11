"use client";

import { useEffect, useMemo, useState } from "react";
import { KeyRound, ShieldCheck, ShieldX, Upload } from "lucide-react";

import { getGovernance } from "@/lib/api";
import type { AuditEntry, GovernanceOverview } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, Section, SkeletonBlock } from "@/components/dashboard/primitives";

type CategoryFilter = "all" | "security" | "data";

const CATEGORY_TONE: Record<AuditEntry["category"], "info" | "warning" | "neutral"> = {
  security: "info",
  data: "warning",
  other: "neutral",
};

function CategoryIcon({
  entry,
  className,
}: {
  entry: AuditEntry;
  className?: string;
}) {
  const Icon = entry.action.endsWith(".failed")
    ? ShieldX
    : entry.category === "data"
      ? Upload
      : entry.category === "security"
        ? KeyRound
        : ShieldCheck;
  return <Icon className={className} />;
}

function formatAction(action: string) {
  return action.replace(/[._]/g, " ");
}

function formatTime(at: string | null) {
  if (!at) return "";
  const d = new Date(at);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleString();
}

export default function GovernancePage() {
  const [data, setData] = useState<GovernanceOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<CategoryFilter>("all");

  useEffect(() => {
    let active = true;
    getGovernance()
      .then((d) => active && setData(d))
      .catch(() => active && setError("Failed to load governance."));
    return () => {
      active = false;
    };
  }, []);

  const visible = useMemo(() => {
    if (!data) return [];
    if (filter === "all") return data.trail;
    return data.trail.filter((e) => e.category === filter);
  }, [data, filter]);

  if (error) {
    return (
      <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Audit & Governance"
        subtitle="A tamper-evident record of who did what — and how explainable every AI decision is. Accountability for an autonomous operating system."
      />

      {!data ? (
        <div className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonBlock key={i} className="h-20" />
            ))}
          </div>
          <SkeletonBlock className="h-40" />
          <SkeletonBlock className="h-64" />
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Logged events" value={`${data.stats.total_events}`} />
            <Stat label="Security events" value={`${data.stats.security_events}`} />
            <Stat
              label="Failed logins"
              value={`${data.stats.failed_logins}`}
              tone={data.stats.failed_logins > 0 ? "danger" : "success"}
            />
            <Stat label="Data changes" value={`${data.stats.data_events}`} />
          </div>

          <DecisionGovernanceCard decisions={data.decisions} />

          <Section
            title="Audit trail"
            subtitle="Most recent first. Security and data-changing actions across the organization."
            action={
              <div className="flex gap-1">
                {(["all", "security", "data"] as CategoryFilter[]).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`rounded-md border px-2.5 py-1 text-xs capitalize transition-colors ${
                      filter === f
                        ? "border-primary/50 bg-card text-foreground"
                        : "border-border text-muted hover:bg-card"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            }
          >
            {visible.length === 0 ? (
              <Empty>No events match this filter yet.</Empty>
            ) : (
              <div className="space-y-2">
                {visible.map((e) => (
                  <AuditRow key={e.id} entry={e} />
                ))}
              </div>
            )}
          </Section>
        </>
      )}
    </div>
  );
}

function DecisionGovernanceCard({
  decisions,
}: {
  decisions: GovernanceOverview["decisions"];
}) {
  const { total_decisions: total } = decisions;
  const coverage = decisions.explainability_coverage;
  const coverageTone =
    coverage >= 90 ? "text-success" : coverage >= 60 ? "text-warning" : "text-danger";

  return (
    <Section
      title="AI decision governance"
      subtitle="Every recommendation must carry reasoning, a confidence score, and named data sources. This is how well the engine meets that bar."
    >
      <Card>
        <CardContent className="p-5">
          {total === 0 ? (
            <p className="text-sm text-muted-foreground">
              No AI decisions recorded yet. Recommendations will appear here as the
              engine produces them.
            </p>
          ) : (
            <div className="grid gap-6 sm:grid-cols-[auto_1fr] sm:items-center">
              <div className="text-center sm:pr-6 sm:border-r sm:border-border">
                <p className={`font-mono text-4xl font-semibold ${coverageTone}`}>
                  {coverage.toFixed(0)}%
                </p>
                <p className="mt-1 text-xs uppercase tracking-wider text-muted">
                  Explainability coverage
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {total} decision{total === 1 ? "" : "s"} · avg confidence{" "}
                  {decisions.avg_confidence.toFixed(0)}%
                </p>
              </div>
              <div className="space-y-3">
                <CoverageBar
                  label="With reasoning"
                  count={decisions.with_reasoning}
                  total={total}
                />
                <CoverageBar
                  label="With confidence score"
                  count={decisions.with_confidence}
                  total={total}
                />
                <CoverageBar
                  label="With named data sources"
                  count={decisions.with_data_sources}
                  total={total}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </Section>
  );
}

function CoverageBar({
  label,
  count,
  total,
}: {
  label: string;
  count: number;
  total: number;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-mono text-foreground">
          {count}/{total}
        </span>
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-card">
        <div
          className={`h-full rounded-full ${pct === 100 ? "bg-success" : "bg-primary"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function AuditRow({ entry }: { entry: AuditEntry }) {
  const failed = entry.action.endsWith(".failed");
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-3">
        <CategoryIcon
          entry={entry}
          className={`mt-0.5 size-4 shrink-0 ${
            failed ? "text-danger" : "text-muted-foreground"
          }`}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium capitalize">{formatAction(entry.action)}</p>
            <Badge tone={CATEGORY_TONE[entry.category]}>{entry.category}</Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            <span className="text-foreground">{entry.actor}</span>
            {entry.resource && <> · {entry.resource}</>}
            {entry.detail && <> · {entry.detail}</>}
          </p>
          <p className="mt-1.5 text-[11px] text-muted-foreground">
            {formatTime(entry.at)}
            {entry.ip_address && ` · ${entry.ip_address}`}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "danger" | "warning" | "success";
}) {
  const valueTone =
    tone === "danger"
      ? "text-danger"
      : tone === "warning"
        ? "text-warning"
        : tone === "success"
          ? "text-success"
          : "text-foreground";
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wider text-muted">{label}</p>
        <p className={`mt-1 font-mono text-2xl font-semibold ${valueTone}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
