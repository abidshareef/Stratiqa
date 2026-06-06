"use client";

import Link from "next/link";
import { ChevronRight, Target } from "lucide-react";

import type { GoalOut } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, SkeletonBlock } from "@/components/dashboard/primitives";

export default function GoalsPage() {
  const { data, error } = useApi<GoalOut[]>("/goals");

  return (
    <div>
      <PageHeader
        title="Strategic Goals"
        subtitle="Track every objective against its target."
      />

      {error && (
        <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {!data && !error && (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonBlock key={i} className="h-16" />
          ))}
        </div>
      )}

      {data && data.length === 0 && <Empty>No goals yet.</Empty>}

      <div className="space-y-2">
        {data?.map((g) => (
          <Link key={g.id} href={`/goals/${g.id}`}>
            <Card className="animate-rise cursor-pointer">
              <CardContent className="flex items-center justify-between gap-3 p-4">
                <div className="flex items-center gap-3">
                  <Target className="size-4 text-info" />
                  <div>
                    <p className="text-sm font-medium">{g.title}</p>
                    {g.target_date && (
                      <p className="text-xs text-muted-foreground">
                        Target {g.target_date}
                        {g.goal_type ? ` · ${g.goal_type}` : ""}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={toneForLevel(g.status)}>{g.status}</Badge>
                  <ChevronRight className="size-4 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
