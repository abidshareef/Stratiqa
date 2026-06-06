"use client";

import { useState } from "react";
import { FileText, Sparkles, Sun, Moon } from "lucide-react";

import { apiFetch } from "@/lib/api";
import { areaTrend } from "@/lib/charts";
import type { BriefOut, ReportOut, ReportSummary } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EChart } from "@/components/charts/echart";
import { PageHeader } from "@/components/layout/page-header";
import { Empty } from "@/components/dashboard/primitives";
import { cn } from "@/lib/utils";

type Tab = "reports" | "briefs";

export default function ReportsPage() {
  const [tab, setTab] = useState<Tab>("reports");

  return (
    <div>
      <PageHeader
        title="Intelligence Reports"
        subtitle="Generate consulting-grade reports and executive briefs on demand."
      />

      <div className="mb-5 flex gap-2">
        {(["reports", "briefs"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "rounded-md px-3 py-1 text-sm font-medium capitalize transition-colors",
              tab === t ? "bg-card text-foreground" : "text-muted hover:text-foreground",
            )}
          >
            {t === "reports" ? "Reports" : "Executive Briefs"}
          </button>
        ))}
      </div>

      {tab === "reports" ? <ReportsTab /> : <BriefsTab />}
    </div>
  );
}

function ReportsTab() {
  const { data, reload } = useApi<ReportSummary[]>("/reports");
  const [selected, setSelected] = useState<ReportOut | null>(null);
  const [busy, setBusy] = useState(false);

  async function generate(type: string) {
    setBusy(true);
    try {
      const r = await apiFetch<ReportOut>(`/reports/generate?report_type=${type}`, {
        method: "POST",
      });
      setSelected(r);
      reload();
    } finally {
      setBusy(false);
    }
  }

  async function open(id: string) {
    setSelected(await apiFetch<ReportOut>(`/reports/${id}`));
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
      <div className="space-y-3">
        <Card>
          <CardContent className="space-y-2 p-3">
            <p className="px-1 text-xs text-muted-foreground">Generate</p>
            {["weekly", "monthly", "executive"].map((t) => (
              <Button
                key={t}
                variant="outline"
                size="sm"
                className="w-full justify-start capitalize"
                disabled={busy}
                onClick={() => generate(t)}
              >
                <Sparkles /> {t} report
              </Button>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-2">
          {data?.length === 0 && <Empty>No reports yet.</Empty>}
          {data?.map((r) => (
            <button
              key={r.id}
              onClick={() => open(r.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-md border border-border p-3 text-left text-sm transition-colors hover:bg-card",
                selected?.id === r.id ? "bg-card" : "bg-surface/40",
              )}
            >
              <FileText className="size-4 text-primary" />
              <div className="min-w-0">
                <p className="truncate font-medium">{r.title ?? r.report_type}</p>
                <p className="text-[11px] text-muted-foreground">
                  {new Date(r.created_at).toLocaleString()}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {selected ? (
        <ReportView report={selected} />
      ) : (
        <Card>
          <CardContent className="flex h-48 items-center justify-center text-sm text-muted-foreground">
            Select or generate a report to view it.
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ReportView({ report }: { report: ReportOut }) {
  const c = report.content as Record<string, unknown>;
  const kpis = (c.kpis as { name: string; value: number }[]) ?? [];
  const risks = (c.risk_analysis as { title: string; level: string }[]) ?? [];
  const recs =
    (c.recommendations as { title: string; confidence_score: number }[]) ?? [];

  return (
    <Card className="animate-rise">
      <CardHeader>
        <CardTitle className="text-base">{report.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5 text-sm">
        {typeof c.executive_summary === "string" && (
          <p className="leading-relaxed text-muted">{c.executive_summary}</p>
        )}

        {kpis.length > 0 && (
          <div>
            <SectionLabel>KPIs</SectionLabel>
            <EChart
              option={areaTrend(
                kpis.map((k) => k.name),
                kpis.map((k) => k.value),
              )}
              height={200}
            />
          </div>
        )}

        {risks.length > 0 && (
          <div>
            <SectionLabel>Risk analysis</SectionLabel>
            <div className="space-y-1.5">
              {risks.map((r, i) => (
                <div key={i} className="flex items-center justify-between gap-2">
                  <span>{r.title}</span>
                  <Badge tone="danger">{r.level}</Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {recs.length > 0 && (
          <div>
            <SectionLabel>Recommendations</SectionLabel>
            <div className="space-y-1.5">
              {recs.map((r, i) => (
                <div key={i} className="flex items-center justify-between gap-2">
                  <span>{r.title}</span>
                  <span className="metric text-xs text-muted-foreground">
                    {r.confidence_score.toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BriefsTab() {
  const { data, reload } = useApi<BriefOut[]>("/briefs");
  const [busy, setBusy] = useState(false);

  async function generate(type: string) {
    setBusy(true);
    try {
      await apiFetch(`/briefs/generate?brief_type=${type}`, { method: "POST" });
      reload();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={busy} onClick={() => generate("morning")}>
          <Sun /> Morning brief
        </Button>
        <Button variant="outline" size="sm" disabled={busy} onClick={() => generate("evening")}>
          <Moon /> Evening brief
        </Button>
      </div>

      {data?.length === 0 && <Empty>No briefs yet.</Empty>}

      <div className="grid gap-4 md:grid-cols-2">
        {data?.map((b) => (
          <Card key={b.id} className="animate-rise">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 capitalize">
                {b.brief_type === "evening" ? (
                  <Moon className="size-4 text-info" />
                ) : (
                  <Sun className="size-4 text-warning" />
                )}
                {b.brief_type} brief
              </CardTitle>
              <p className="text-[11px] text-muted-foreground">
                {new Date(b.generated_at).toLocaleString()}
              </p>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {Object.entries(b.content)
                .filter(([k]) => k !== "generated_at")
                .map(([key, value]) => (
                  <div key={key}>
                    <SectionLabel>{key.replace(/_/g, " ")}</SectionLabel>
                    <ul className="space-y-1 text-muted">
                      {(Array.isArray(value) ? value : [value]).map((item, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />
                          {typeof item === "object" && item !== null
                            ? ((item as Record<string, unknown>).title as string) ??
                              JSON.stringify(item)
                            : String(item)}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </p>
  );
}
