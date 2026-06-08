"use client";

import { useEffect, useState } from "react";
import { Boxes, TrendingDown, TrendingUp } from "lucide-react";

import { getProducts } from "@/lib/api";
import type { ProductOut, ProductOverview, ProductSignal } from "@/lib/types";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, Section, SkeletonBlock } from "@/components/dashboard/primitives";

const STOCK_LABEL: Record<ProductOut["stock_status"], string> = {
  ok: "In stock",
  low: "Low",
  out: "Out",
};
const STOCK_TONE: Record<ProductOut["stock_status"], string> = {
  ok: "success",
  low: "warning",
  out: "danger",
};

function money(n: number | null): string {
  if (n === null) return "—";
  return `$${Math.round(n).toLocaleString()}`;
}

export default function ProductsPage() {
  const [data, setData] = useState<ProductOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getProducts()
      .then((d) => active && setData(d))
      .catch(() => active && setError("Failed to load product intelligence."));
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
        title="Product Intelligence"
        subtitle="Catalog, inventory, and demand — stockout and concentration signals grounded in your data."
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
            <Stat label="Products" value={`${data.stats.total_products}`} />
            <Stat label="Line revenue" value={money(data.stats.total_revenue)} />
            <Stat
              label="Low stock"
              value={`${data.stats.low_stock_count}`}
              tone={data.stats.low_stock_count > 0 ? "warning" : "success"}
            />
            <Stat label="Top product" value={data.stats.top_product ?? "—"} small />
          </div>

          <Section
            title="Demand & stock signals"
            subtitle="What the product line is telling you right now."
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

          <Section
            title="Catalog"
            subtitle="Ordered by revenue — the products that drive the business lead."
          >
            {data.products.length === 0 ? (
              <Empty>No products tracked yet.</Empty>
            ) : (
              <Card>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted">
                        <th className="px-4 py-3 font-medium">Product</th>
                        <th className="px-4 py-3 font-medium">Category</th>
                        <th className="px-4 py-3 font-medium text-right">Units sold</th>
                        <th className="px-4 py-3 font-medium text-right">Revenue</th>
                        <th className="px-4 py-3 font-medium text-right">On hand</th>
                        <th className="px-4 py-3 font-medium text-right">Demand</th>
                        <th className="px-4 py-3 font-medium text-right">Stock</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.products.map((p) => (
                        <tr
                          key={p.id}
                          className="border-b border-border/50 last:border-0 hover:bg-card/60"
                        >
                          <td className="px-4 py-3 font-medium">{p.product_name}</td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {p.category ?? "—"}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {p.sales_count.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {money(p.revenue)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono">
                            {p.quantity}
                            <span className="text-muted-foreground">
                              {" "}
                              / {p.reorder_level}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <DemandTrend trend={p.demand_trend} />
                          </td>
                          <td className="px-4 py-3 text-right">
                            <Badge tone={STOCK_TONE[p.stock_status] as never}>
                              {STOCK_LABEL[p.stock_status]}
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

function DemandTrend({ trend }: { trend: ProductOut["demand_trend"] }) {
  if (trend === "up")
    return (
      <span className="inline-flex items-center gap-1 text-success">
        <TrendingUp className="size-4" /> Up
      </span>
    );
  if (trend === "down")
    return (
      <span className="inline-flex items-center gap-1 text-danger">
        <TrendingDown className="size-4" /> Down
      </span>
    );
  return <span className="text-muted-foreground">Flat</span>;
}

function Stat({
  label,
  value,
  tone = "neutral",
  small = false,
}: {
  label: string;
  value: string;
  tone?: "neutral" | "danger" | "warning" | "success";
  small?: boolean;
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
        <p
          className={`mt-1 font-mono font-semibold ${small ? "text-sm" : "text-2xl"} ${valueTone}`}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}

function SignalCard({ signal }: { signal: ProductSignal }) {
  return (
    <Card>
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Boxes className="size-4 text-primary" />
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
