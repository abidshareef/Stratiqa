"use client";

import { useEffect, useMemo, useState } from "react";
import { ShieldAlert } from "lucide-react";

import { getAlerts } from "@/lib/api";
import type { AlertItem, MonitoringOverview } from "@/lib/types";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, Section, SkeletonBlock } from "@/components/dashboard/primitives";

const CATEGORY_LABEL: Record<AlertItem["category"], string> = {
  risk: "Risk",
  customer: "Customer",
  inventory: "Inventory",
  kpi: "KPI",
  goal: "Goal",
  delivery: "Delivery",
  system: "System",
};

type Filter = "all" | "danger" | "warning";

export default function AlertsPage() {
  const [data, setData] = useState<MonitoringOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    let active = true;
    getAlerts()
      .then((d) => active && setData(d))
      .catch(() => active && setError("Failed to load monitoring."));
    return () => {
      active = false;
    };
  }, []);

  const visible = useMemo(() => {
    if (!data) return [];
    if (filter === "all") return data.alerts;
    return data.alerts.filter((a) => a.severity === filter);
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
        title="Alerts & Monitoring"
        subtitle="A single live feed across every domain — risk, churn, inventory, KPIs, goals, delivery — plus system incidents."
      />

      {!data ? (
        <div className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonBlock key={i} className="h-20" />
            ))}
          </div>
          <SkeletonBlock className="h-64" />
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat
              label="Open alerts"
              value={`${data.stats.total_open}`}
              tone={data.stats.total_open > 0 ? "warning" : "success"}
            />
            <Stat
              label="Critical"
              value={`${data.stats.critical}`}
              tone={data.stats.critical > 0 ? "danger" : "success"}
            />
            <Stat
              label="Open incidents"
              value={`${data.stats.incidents_open}`}
              tone={data.stats.incidents_open > 0 ? "warning" : "neutral"}
            />
            <Stat label="Anomalies" value={`${data.stats.anomalies}`} />
          </div>

          <Section
            title="Live alert feed"
            subtitle="Derived from your business data and persisted system alerts. Most severe first."
            action={
              <div className="flex gap-1">
                {(["all", "danger", "warning"] as Filter[]).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`rounded-md border px-2.5 py-1 text-xs capitalize transition-colors ${
                      filter === f
                        ? "border-primary/50 bg-card text-foreground"
                        : "border-border text-muted hover:bg-card"
                    }`}
                  >
                    {f === "danger" ? "critical" : f}
                  </button>
                ))}
              </div>
            }
          >
            {visible.length === 0 ? (
              <Empty>No alerts match this filter — all clear.</Empty>
            ) : (
              <div className="space-y-2">
                {visible.map((a, i) => (
                  <AlertRow key={i} alert={a} />
                ))}
              </div>
            )}
          </Section>

          {data.incidents.length > 0 && (
            <Section title="Incidents" subtitle="Operational incidents and their state.">
              <div className="grid gap-2 lg:grid-cols-2">
                {data.incidents.map((inc) => (
                  <Card key={inc.id}>
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium capitalize">
                          {inc.incident_type.replace(/_/g, " ")}
                        </p>
                        <Badge tone={inc.resolved ? "success" : "warning"}>
                          {inc.resolved ? "resolved" : "open"}
                        </Badge>
                      </div>
                      {inc.description && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          {inc.description}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function AlertRow({ alert }: { alert: AlertItem }) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-3">
        <ShieldAlert
          className={`mt-0.5 size-4 shrink-0 ${
            alert.severity === "danger"
              ? "text-danger"
              : alert.severity === "warning"
                ? "text-warning"
                : "text-info"
          }`}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium">{alert.title}</p>
            <div className="flex shrink-0 items-center gap-1.5">
              <Badge tone="neutral">{CATEGORY_LABEL[alert.category]}</Badge>
              <Badge tone={toneForLevel(alert.severity)}>{alert.severity}</Badge>
            </div>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{alert.detail}</p>
          <p className="mt-1.5 text-[11px] text-muted-foreground">
            {alert.derived ? "live · " : "system · "}
            {alert.source}
            {alert.status === "resolved" && " · resolved"}
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
