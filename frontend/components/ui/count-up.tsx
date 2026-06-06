"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Animates a number from 0 to `value` on mount (eased). Renders via the
 * provided formatter so it works for currency, percent, or plain counts.
 */
export function CountUp({
  value,
  format = (n) => Math.round(n).toString(),
  durationMs = 700,
  className,
}: {
  value: number;
  format?: (n: number) => string;
  durationMs?: number;
  className?: string;
}) {
  const [display, setDisplay] = useState(0);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setDisplay(value * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [value, durationMs]);

  return <span className={className}>{format(display)}</span>;
}
