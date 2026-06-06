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
