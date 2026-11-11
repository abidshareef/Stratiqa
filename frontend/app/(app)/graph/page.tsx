"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { getGraph, rebuildGraph } from "@/lib/api";
import { graphChart, GRAPH_COLORS } from "@/lib/charts";
import type { GraphOut } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EChart } from "@/components/charts/echart";
import { PageHeader } from "@/components/layout/page-header";
import { SkeletonBlock } from "@/components/dashboard/primitives";

export default function GraphPage() {
  const [graph, setGraph] = useState<GraphOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rebuilding, setRebuilding] = useState(false);

  useEffect(() => {
    let active = true;
    getGraph()
      .then((g) => active && setGraph(g))
      .catch(() => active && setError("Failed to load the knowledge graph."));
    return () => {
      active = false;
    };
  }, []);

  async function rebuild() {
    setRebuilding(true);
    try {
      setGraph(await rebuildGraph());
    } catch {
      /* keep current view */
    } finally {
      setRebuilding(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Knowledge Graph"
        subtitle="Every entity in your business and how they connect — goals, projects, risks, KPIs, and the recommendations that address them."
        action={
          <Button variant="outline" size="sm" onClick={rebuild} disabled={rebuilding}>
            <RefreshCw className={rebuilding ? "animate-spin" : ""} />
            Rebuild
          </Button>
        }
      />

      {error && (
        <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {!graph && !error && <SkeletonBlock className="h-[520px]" />}

      {graph && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {Object.entries(graph.stats).map(([cat, count]) => (
              <span
                key={cat}
                className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2 py-1 text-xs"
              >
                <span
                  className="size-2 rounded-full"
                  style={{ backgroundColor: GRAPH_COLORS[cat] ?? "#71717a" }}
                />
                <span className="capitalize text-muted">{cat}</span>
                <span className="metric font-semibold">{count}</span>
              </span>
            ))}
          </div>

          <Card>
            <CardContent className="p-2">
              <EChart
                option={graphChart(graph.nodes, graph.edges)}
                height={560}
              />
            </CardContent>
          </Card>

          <p className="text-xs text-muted-foreground">
            {graph.nodes.length} entities · {graph.edges.length} relationships.
            Drag nodes to explore; hover an edge to see how two entities relate.
          </p>
        </div>
      )}
    </div>
  );
}
