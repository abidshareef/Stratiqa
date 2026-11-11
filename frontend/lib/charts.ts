import type { EChartsCoreOption } from "echarts";

/** Design-system palette (hex mirrors of the CSS tokens). */
export const C = {
  primary: "#2563eb",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#38bdf8",
  border: "#262626",
  card: "#171717",
  surface: "#111111",
  muted: "#71717a",
  text: "#ededed",
} as const;

const AXIS_LABEL = { color: C.muted, fontSize: 10 };
const SPLIT_LINE = { lineStyle: { color: C.border, type: "dashed" as const } };

/** Minimal sparkline — no axes, subtle area fill. */
export function sparkline(values: number[], color: string): EChartsCoreOption {
  return {
    animationDuration: 600,
    grid: { top: 4, bottom: 4, left: 2, right: 2 },
    xAxis: { type: "category", show: false, data: values.map((_, i) => i) },
    yAxis: { type: "value", show: false, scale: true },
    series: [
      {
        type: "line",
        data: values,
        smooth: true,
        symbol: "none",
        lineStyle: { width: 2, color },
        areaStyle: { color, opacity: 0.08 },
      },
    ],
  };
}

/** Area trend with axes + tooltip — the dashboard's headline chart. */
export function areaTrend(
  labels: string[],
  values: number[],
  color: string = C.primary,
): EChartsCoreOption {
  return {
    animationDuration: 700,
    grid: { top: 16, bottom: 24, left: 48, right: 12 },
    tooltip: {
      trigger: "axis",
      backgroundColor: C.card,
      borderColor: C.border,
      textStyle: { color: C.text, fontSize: 12 },
    },
    xAxis: {
      type: "category",
      data: labels,
      boundaryGap: false,
      axisLine: { lineStyle: { color: C.border } },
      axisLabel: AXIS_LABEL,
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      scale: true,
      splitLine: SPLIT_LINE,
      axisLabel: {
        ...AXIS_LABEL,
        formatter: (v: number) =>
          Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(0)}k` : `${v}`,
      },
    },
    series: [
      {
        type: "line",
        data: values,
        smooth: true,
        symbol: "circle",
        symbolSize: 5,
        showSymbol: false,
        lineStyle: { width: 2.5, color },
        itemStyle: { color },
        areaStyle: { color, opacity: 0.12 },
      },
    ],
  };
}

/** Radial gauge for a single 0–100 progress value. */
export function gauge(value: number, color: string = C.primary): EChartsCoreOption {
  return {
    animationDuration: 800,
    series: [
      {
        type: "gauge",
        startAngle: 220,
        endAngle: -40,
        min: 0,
        max: 100,
        radius: "92%",
        progress: {
          show: true,
          width: 10,
          roundCap: true,
          itemStyle: { color },
        },
        axisLine: {
          lineStyle: { width: 10, color: [[1, C.border]] },
        },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        anchor: { show: false },
        title: { show: false },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, 0],
          fontSize: 22,
          fontWeight: 600,
          fontFamily: "var(--font-jetbrains-mono), monospace",
          color: C.text,
          formatter: "{value}%",
        },
        data: [{ value: Math.round(value) }],
      },
    ],
  };
}

/** Category → token color for the knowledge-graph nodes. */
export const GRAPH_COLORS: Record<string, string> = {
  organization: C.primary,
  dna: C.info,
  goal: C.success,
  project: "#818cf8",
  risk: C.danger,
  kpi: C.warning,
  customer: C.muted,
  opportunity: "#34d399",
  recommendation: "#a78bfa",
};

interface GNode {
  id: string;
  label: string;
  category: string;
  value: number | null;
  detail: string | null;
}
interface GEdge {
  source: string;
  target: string;
  type: string;
}

/** Force-directed knowledge graph of the org's entities + relationships. */
export function graphChart(nodes: GNode[], edges: GEdge[]): EChartsCoreOption {
  const categories = Array.from(new Set(nodes.map((n) => n.category)));
  const detailById = new Map(nodes.map((n) => [n.id, n]));
  return {
    animationDuration: 600,
    tooltip: {
      backgroundColor: C.card,
      borderColor: C.border,
      textStyle: { color: C.text, fontSize: 12 },
      formatter: (p: { dataType: string; data: Record<string, unknown> }) => {
        if (p.dataType === "edge") {
          const d = p.data as unknown as { source: string; target: string; value: string };
          const s = detailById.get(d.source)?.label ?? "";
          const t = detailById.get(d.target)?.label ?? "";
          return `${s} <b>${d.value}</b> ${t}`;
        }
        const d = p.data as unknown as { name: string; detail?: string };
        return d.detail ? `<b>${d.name}</b><br/>${d.detail}` : `<b>${d.name}</b>`;
      },
    },
    legend: [
      {
        data: categories,
        textStyle: { color: C.muted, fontSize: 10 },
        icon: "circle",
        top: 0,
      },
    ],
    series: [
      {
        type: "graph",
        layout: "force",
        roam: true,
        draggable: true,
        zoom: 1.1,
        categories: categories.map((c) => ({
          name: c,
          itemStyle: { color: GRAPH_COLORS[c] ?? C.muted },
        })),
        data: nodes.map((n) => ({
          id: n.id,
          name: n.label,
          detail: n.detail,
          category: categories.indexOf(n.category),
          symbolSize: Math.max(8, Math.min(46, n.value ?? 12)),
          value: n.value ?? 12,
        })),
        links: edges.map((e) => ({
          source: e.source,
          target: e.target,
          value: e.type,
        })),
        force: { repulsion: 220, edgeLength: [70, 160], gravity: 0.08 },
        label: {
          show: true,
          position: "right",
          color: C.text,
          fontSize: 10,
          formatter: (p: { name: string }) =>
            p.name.length > 22 ? `${p.name.slice(0, 20)}…` : p.name,
        },
        lineStyle: { color: C.border, width: 1, opacity: 0.7, curveness: 0.06 },
        emphasis: { focus: "adjacency", lineStyle: { width: 2, color: C.muted } },
      },
    ],
  };
}

/** Horizontal bars for project health, colored by score band. */
export function healthBars(
  items: { name: string; score: number }[],
): EChartsCoreOption {
  const colorFor = (s: number) =>
    s >= 75 ? C.success : s >= 45 ? C.warning : C.danger;
  return {
    animationDuration: 700,
    grid: { top: 8, bottom: 8, left: 8, right: 40, containLabel: true },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: C.card,
      borderColor: C.border,
      textStyle: { color: C.text, fontSize: 12 },
    },
    xAxis: { type: "value", max: 100, show: false },
    yAxis: {
      type: "category",
      data: items.map((i) => i.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: C.text, fontSize: 11 },
      inverse: true,
    },
    series: [
      {
        type: "bar",
        data: items.map((i) => ({
          value: i.score,
          itemStyle: { color: colorFor(i.score), borderRadius: 4 },
        })),
        barWidth: 14,
        label: {
          show: true,
          position: "right",
          color: C.muted,
          fontSize: 11,
          formatter: "{c}",
        },
      },
    ],
  };
}
