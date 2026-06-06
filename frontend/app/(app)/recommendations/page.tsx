"use client";

import { useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { apiFetch } from "@/lib/api";
import type { RecommendationOut } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { Button } from "@/components/ui/button";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, SkeletonBlock } from "@/components/dashboard/primitives";
import { cn } from "@/lib/utils";

const FILTERS = ["all", "pending", "accepted", "dismissed"] as const;
type Filter = (typeof FILTERS)[number];

export default function RecommendationsPage() {
  const { data, error, reload } = useApi<RecommendationOut[]>("/recommendations");
  const [filter, setFilter] = useState<Filter>("all");
  const [refreshing, setRefreshing] = useState(false);

  const filtered = useMemo(
    () =>
      (data ?? []).filter((r) => filter === "all" || r.status === filter),
    [data, filter],
  );

  async function refresh() {
    setRefreshing(true);
    try {
      await apiFetch("/recommendations/refresh", { method: "POST" });
      reload();
    } catch {
      /* ignore */
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Recommendations"
        subtitle="Every recommendation is grounded in your data and fully explainable."
        action={
          <Button variant="outline" size="sm" onClick={refresh} disabled={refreshing}>
            <RefreshCw className={refreshing ? "animate-spin" : ""} />
            Regenerate
          </Button>
        }
      />

      <div className="mb-4 flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-medium capitalize transition-colors",
              filter === f
                ? "bg-card text-foreground"
                : "text-muted hover:text-foreground",
            )}
          >
            {f}
            {data && (
              <span className="ml-1.5 text-muted-foreground">
                {f === "all" ? data.length : data.filter((r) => r.status === f).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {!data && !error && (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonBlock key={i} className="h-48" />
          ))}
        </div>
      )}

      {data && filtered.length === 0 && <Empty>No recommendations in this view.</Empty>}

      <div className="grid gap-4 md:grid-cols-2">
        {filtered.map((rec) => (
          <RecommendationCard key={rec.id} rec={rec} />
        ))}
      </div>
    </div>
  );
}
