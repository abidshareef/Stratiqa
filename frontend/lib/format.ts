import type { KpiCard } from "./types";

/** Format a KPI value according to its declared format + unit. */
export function formatKpi(card: Pick<KpiCard, "value" | "fmt" | "unit">): string {
  const { value, fmt, unit } = card;
  if (fmt === "currency") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      notation: Math.abs(value) >= 10000 ? "compact" : "standard",
      maximumFractionDigits: Math.abs(value) >= 10000 ? 1 : 0,
    }).format(value);
  }
  if (fmt === "percent") {
    return `${value.toFixed(1)}%`;
  }
  const n = new Intl.NumberFormat("en-US", {
    notation: Math.abs(value) >= 10000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
  return unit ? `${n} ${unit}` : n;
}

export function formatDelta(pct: number | null): string {
  if (pct == null) return "—";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}
