"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, apiFetch } from "./api";

/**
 * Minimal GET hook: fetches `path` on mount and exposes a `reload`. State is
 * set from inside `.then(...)` callbacks (never synchronously in the effect),
 * which keeps the React `set-state-in-effect` rule satisfied.
 */
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    if (!path) return;
    apiFetch<T>(path)
      .then(setData)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Failed to load."),
      );
  }, [path]);

  useEffect(() => {
    if (!path) return;
    let active = true;
    apiFetch<T>(path)
      .then((d) => active && setData(d))
      .catch(
        (e) =>
          active && setError(e instanceof ApiError ? e.message : "Failed to load."),
      );
    return () => {
      active = false;
    };
  }, [path]);

  return { data, error, reload, setData };
}
