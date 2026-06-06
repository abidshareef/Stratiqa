"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { formatDelta, formatKpi } from "@/lib/format";
import { C, sparkline } from "@/lib/charts";
import type { KpiCard as KpiCardType } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { CountUp } from "@/components/ui/count-up";
import { EChart } from "@/components/charts/echart";

export function KpiCard({ kpi }: { kpi: KpiCardType }) {
  const trendColor = kpi.positive ? C.success : C.danger;
  const DeltaIcon =
    kpi.direction === "up"
      ? ArrowUpRight
      : kpi.direction === "down"
        ? ArrowDownRight
        : Minus;

  return (
    <Card className="animate-rise overflow-hidden">
      <div className="flex items-start justify-between p-4 pb-0">
        <div className="min-w-0">
          <p className="truncate text-xs text-muted-foreground">{kpi.label}</p>
          <CountUp
            value={kpi.value}
            format={(n) => formatKpi({ ...kpi, value: n })}
            className="metric mt-1 block text-xl font-semibold"
          />
        </div>
        <span
          className={cn(
            "flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-medium",
            kpi.positive
              ? "bg-success/10 text-success"
              : "bg-danger/10 text-danger",
          )}
        >
          <DeltaIcon className="size-3" />
          {formatDelta(kpi.delta_pct)}
        </span>
      </div>
      <EChart
        option={sparkline(kpi.series, trendColor)}
        height={44}
        className="mt-2 w-full"
      />
    </Card>
  );
}
