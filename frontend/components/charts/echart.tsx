"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";

/**
 * Thin ECharts wrapper — initializes once, updates option reactively, and
 * resizes with its container. Canvas renderer, dark surface, no glow.
 */
export function EChart({
  option,
  className,
  height = 220,
}: {
  option: echarts.EChartsCoreOption;
  className?: string;
  height?: number;
}) {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!el.current) return;
    const instance = echarts.init(el.current, null, { renderer: "canvas" });
    chart.current = instance;
    const ro = new ResizeObserver(() => {
      if (!instance.isDisposed()) instance.resize();
    });
    ro.observe(el.current);
    return () => {
      ro.disconnect();
      instance.dispose();
      chart.current = null;
    };
  }, []);

  useEffect(() => {
    chart.current?.setOption(option, true);
  }, [option]);

  return <div ref={el} style={{ height }} className={className} />;
}
