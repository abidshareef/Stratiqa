"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { apiFetch } from "@/lib/api";
import { C, gauge } from "@/lib/charts";
import type { GoalDetail } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EChart } from "@/components/charts/echart";
import { SkeletonBlock } from "@/components/dashboard/primitives";

export default function GoalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, setData } = useApi<GoalDetail>(`/goals/${id}`);
  const [pct, setPct] = useState("");
  const [saving, setSaving] = useState(false);

  async function recordProgress() {
    const value = Number(pct);
    if (Number.isNaN(value) || value < 0 || value > 100) return;
    setSaving(true);
    try {
      const updated = await apiFetch<GoalDetail>(
        `/goals/${id}/progress?percentage=${value}`,
        { method: "POST" },
      );
      setData(updated);
      setPct("");
    } catch {
      /* ignore; reload would surface */
    } finally {
      setSaving(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }
  if (!data) return <SkeletonBlock className="h-64" />;

  const progress = data.latest_progress;
  const color = progress >= 66 ? C.success : progress >= 33 ? C.warning : C.danger;

  return (
    <div className="space-y-6">
      <Link
        href="/goals"
        className="inline-flex items-center gap-1 text-xs text-muted hover:text-foreground"
      >
        <ArrowLeft className="size-3" /> Goals
      </Link>

      <div className="animate-rise flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{data.title}</h1>
          {data.description && (
            <p className="mt-1 max-w-2xl text-sm text-muted">{data.description}</p>
          )}
        </div>
        <Badge tone={toneForLevel(data.risk_indicator)}>
          {data.risk_indicator.replace(/_/g, " ")}
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <EChart option={gauge(progress, color)} height={150} />
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Forecast</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Completion forecast" value={data.completion_forecast ?? "—"} />
            <Row label="Target value" value={data.target_value?.toLocaleString() ?? "—"} />
            <Row label="Target date" value={data.target_date ?? "—"} />
            <Row label="Type" value={data.goal_type ?? "—"} />
            <Row label="Status" value={data.status} />

            <div className="flex items-end gap-2 border-t border-border pt-3">
              <div className="flex-1">
                <label className="text-xs text-muted">Record progress (%)</label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={pct}
                  onChange={(e) => setPct(e.target.value)}
                  placeholder={`${progress.toFixed(0)}`}
                  className="mt-1"
                />
              </div>
              <Button onClick={recordProgress} disabled={saving || !pct}>
                {saving ? "Saving…" : "Update"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
