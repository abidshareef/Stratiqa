"use client";

import { useState } from "react";

import { apiFetch } from "@/lib/api";
import type { RecommendationOut } from "@/lib/types";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Renders a single recommendation with its full explainability panel —
 * every recommendation must surface why, confidence, data sources, and
 * expected impact (per the STRATIQA spec).
 */
export function RecommendationCard({ rec }: { rec: RecommendationOut }) {
  const [status, setStatus] = useState(rec.status);
  const [busy, setBusy] = useState(false);

  async function act(action: "accept" | "dismiss") {
    setBusy(true);
    try {
      const updated = await apiFetch<RecommendationOut>(
        `/recommendations/${rec.id}/${action}`,
        { method: "POST" },
      );
      setStatus(updated.status);
    } catch {
      /* surfaced globally; keep current state */
    } finally {
      setBusy(false);
    }
  }

  const resolved = status === "accepted" || status === "dismissed";

  return (
    <Card className="animate-rise">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-sm">{rec.title}</CardTitle>
          <div className="flex shrink-0 items-center gap-2">
            <Badge tone={toneForLevel(rec.risk_level)}>{rec.risk_level} risk</Badge>
            <span className="metric text-xs text-muted">
              {rec.confidence_score.toFixed(0)}%
            </span>
          </div>
        </div>
        {rec.description && (
          <p className="text-xs text-muted">{rec.description}</p>
        )}
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Confidence bar */}
        <div className="h-1 w-full overflow-hidden rounded-full bg-surface">
          <div
            className="h-full rounded-full bg-primary"
            style={{ width: `${Math.min(100, Math.max(0, rec.confidence_score))}%` }}
          />
        </div>

        {/* Explainability panel */}
        <dl className="grid gap-2 rounded-md border border-border bg-surface/50 p-3 text-xs">
          {rec.reasoning && (
            <Field label="Why" value={rec.reasoning} />
          )}
          {rec.expected_impact && (
            <Field label="Expected impact" value={rec.expected_impact} />
          )}
          {rec.data_sources && (
            <Field label="Data sources" value={rec.data_sources} mono />
          )}
        </dl>

        {resolved ? (
          <Badge tone={status === "accepted" ? "success" : "neutral"}>
            {status === "accepted" ? "Accepted" : "Dismissed"}
          </Badge>
        ) : (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="success"
              disabled={busy}
              onClick={() => act("accept")}
            >
              Accept
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => act("dismiss")}
            >
              Dismiss
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="grid grid-cols-[7rem_1fr] gap-2">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={mono ? "metric text-muted" : "text-foreground/90"}>{value}</dd>
    </div>
  );
}
