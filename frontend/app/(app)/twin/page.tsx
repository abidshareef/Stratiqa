"use client";

import { useState } from "react";
import {
  Activity,
  Brain,
  Gauge,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";

import { apiFetch } from "@/lib/api";
import type { SimulationOutcome, SimulationResultOut } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/layout/page-header";

interface Levers {
  marketing_spend_change: number;
  hiring_change: number;
  price_change: number;
  market_expansion: number;
  new_product_launch: boolean;
}

const SLIDERS: { key: keyof Levers; label: string }[] = [
  { key: "marketing_spend_change", label: "Marketing spend" },
  { key: "hiring_change", label: "Hiring" },
  { key: "price_change", label: "Pricing" },
  { key: "market_expansion", label: "Market expansion" },
];

export default function TwinPage() {
  const [scenario, setScenario] = useState("Aggressive growth play");
  const [levers, setLevers] = useState<Levers>({
    marketing_spend_change: 25,
    hiring_change: 10,
    price_change: 0,
    market_expansion: 15,
    new_product_launch: false,
  });
  const [result, setResult] = useState<SimulationOutcome | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setLever(key: keyof Levers, value: number | boolean) {
    setLevers((l) => ({ ...l, [key]: value }));
  }

  async function run() {
    setRunning(true);
    setError(null);
    try {
      const res = await apiFetch<SimulationResultOut>("/twin/simulate", {
        method: "POST",
        body: { scenario_name: scenario || "Scenario", ...levers },
      });
      setResult(res.outcome);
    } catch {
      setError("Simulation failed. Try again.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Business Twin"
        subtitle="Pressure-test a strategic move before you commit. Levers are % changes."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Levers */}
        <Card>
          <CardHeader>
            <CardTitle>Scenario levers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <label className="text-xs text-muted">Scenario name</label>
              <Input
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                className="mt-1"
              />
            </div>

            {SLIDERS.map(({ key, label }) => (
              <div key={key}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-muted">{label}</span>
                  <span className="metric font-semibold">
                    {(levers[key] as number) > 0 ? "+" : ""}
                    {levers[key] as number}%
                  </span>
                </div>
                <input
                  type="range"
                  min={-50}
                  max={50}
                  step={5}
                  value={levers[key] as number}
                  onChange={(e) => setLever(key, Number(e.target.value))}
                  className="w-full accent-[var(--primary)]"
                />
              </div>
            ))}

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={levers.new_product_launch}
                onChange={(e) => setLever("new_product_launch", e.target.checked)}
                className="size-4 accent-[var(--primary)]"
              />
              New product launch
            </label>

            <Button onClick={run} disabled={running} className="w-full">
              {running ? "Running simulation…" : "Run simulation"}
            </Button>
            {error && <p className="text-xs text-danger">{error}</p>}
          </CardContent>
        </Card>

        {/* Outcome */}
        <Card>
          <CardHeader>
            <CardTitle>Projected impact</CardTitle>
          </CardHeader>
          <CardContent>
            {!result ? (
              <div className="flex h-full min-h-48 flex-col items-center justify-center text-center text-sm text-muted-foreground">
                <Brain className="mb-2 size-8 text-muted-foreground/50" />
                Adjust the levers and run a simulation.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <Impact
                    icon={TrendingUp}
                    label="Revenue"
                    value={result.revenue_impact}
                  />
                  <Impact
                    icon={Gauge}
                    label="Profit"
                    value={result.profit_impact}
                  />
                  <Impact
                    icon={TriangleAlert}
                    label="Risk"
                    value={result.risk_impact}
                    invert
                  />
                  <Impact
                    icon={Activity}
                    label="Growth"
                    value={result.growth_impact}
                  />
                </div>

                <div className="rounded-md border border-border bg-surface/50 p-3">
                  <p className="text-sm leading-relaxed text-foreground/90">
                    {result.narrative}
                  </p>
                </div>

                <Badge tone="info">
                  {result.confidence_score.toFixed(0)}% model confidence
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Impact({
  icon: Icon,
  label,
  value,
  invert,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  invert?: boolean;
}) {
  // For most metrics up is good; for risk, up is bad (invert).
  const good = invert ? value <= 0 : value >= 0;
  const color = good ? "text-success" : "text-danger";
  return (
    <div className="rounded-md border border-border bg-surface/50 p-3">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </div>
      <p className={`metric mt-1 text-2xl font-semibold ${color}`}>
        {value > 0 ? "+" : ""}
        {value.toFixed(1)}%
      </p>
    </div>
  );
}
