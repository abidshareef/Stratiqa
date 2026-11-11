"use client";

import { useEffect, useState } from "react";
import { HeartPulse } from "lucide-react";

import { getCustomers } from "@/lib/api";
import type {
  CustomerHealthOut,
  CustomerOverview,
  CustomerSignal,
} from "@/lib/types";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, Section, SkeletonBlock } from "@/components/dashboard/primitives";

const STATUS_LABEL: Record<CustomerHealthOut["status"], string> = {
  at_risk: "At risk",
  watch: "Watch",
  healthy: "Healthy",
};
const STATUS_TONE: Record<CustomerHealthOut["status"], string> = {
  at_risk: "danger",
  watch: "warning",
  healthy: "success",
};

export default function CustomersPage() {
  const [data, setData] = useState<CustomerOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getCustomers()
      .then((d) => active && setData(d))
      .catch(() => active && setError("Failed to load customer intelligence."));
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

  return (
    <div className="space-y-8">
      <PageHeader
        title="Customer Intelligence"
        subtitle="Account health, churn risk, and support load — every signal grounded in your data."
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
          {/* Stats strip */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Customers" value={`${data.stats.total_customers}`} />
            <Stat
              label="Avg health"
              value={
                data.stats.avg_health_score !== null
                  ? `${data.stats.avg_health_score.toFixed(0)}`
                  : "—"
              }
            />
            <Stat
              label="At risk"
              value={`${data.stats.at_risk_count}`}
              tone={data.stats.at_risk_count > 0 ? "danger" : "success"}
            />
            <Stat
              label="Open tickets"
              value={`${data.stats.open_tickets}`}
              tone={data.stats.open_tickets > 0 ? "warning" : "neutral"}
            />
          </div>

          {/* Grounded signals */}
          <Section
            title="Retention signals"
            subtitle="What the customer base is telling you right now."
          >
            {data.signals.length === 0 ? (
              <Empty>No signals yet.</Empty>
            ) : (
              <div className="grid gap-2 lg:grid-cols-2">
                {data.signals.map((s, i) => (
                  <SignalCard key={i} signal={s} />
                ))}
              </div>
            )}
          </Section>

          {/* Account table */}
          <Section
            title="Accounts"
            subtitle="Ordered by churn risk — the accounts needing attention lead."
          >
            {data.customers.length === 0 ? (
              <Empty>No customers tracked yet.</Empty>
            ) : (
              <Card>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted">
                        <th className="px-4 py-3 font-medium">Account</th>
                        <th className="px-4 py-3 font-medium">Segment</th>
                        <th className="px-4 py-3 font-medium text-right">Health</th>
                        <th className="px-4 py-3 font-medium text-right">Churn risk</th>
                        <th className="px-4 py-3 font-medium text-right">Tickets</th>
                        <th className="px-4 py-3 font-medium text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.customers.map((c) => (
                        <tr
                          key={c.id}
                          className="border-b border-border/50 last:border-0 hover:bg-card/60"
                        >
                          <td className="px-4 py-3 font-medium">{c.customer_name}</td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {c.segment ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {c.health_score !== null ? c.health_score.toFixed(0) : "—"}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {c.churn_risk !== null ? `${c.churn_risk.toFixed(0)}%` : "—"}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {c.open_tickets || "—"}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <Badge tone={STATUS_TONE[c.status] as never}>
                              {STATUS_LABEL[c.status]}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}
          </Section>
        </>
      )}
    </div>
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

function SignalCard({ signal }: { signal: CustomerSignal }) {
  return (
    <Card>
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <HeartPulse className="size-4 text-primary" />
            <p className="text-sm font-medium">{signal.title}</p>
          </div>
          <Badge tone={toneForLevel(signal.severity)}>{signal.severity}</Badge>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{signal.finding}</p>
        {signal.recommended_action && (
          <p className="mt-1.5 text-xs text-info">→ {signal.recommended_action}</p>
        )}
        <p className="mt-2 text-[11px] text-muted-foreground">
          {signal.confidence_score.toFixed(0)}% confidence ·{" "}
          {signal.data_sources.join(", ")}
        </p>
      </CardContent>
    </Card>
  );
}
