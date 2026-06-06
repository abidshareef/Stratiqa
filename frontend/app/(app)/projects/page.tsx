"use client";

import Link from "next/link";
import { ChevronRight, FolderKanban } from "lucide-react";

import type { ProjectOut } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, SkeletonBlock } from "@/components/dashboard/primitives";

export default function ProjectsPage() {
  const { data, error } = useApi<ProjectOut[]>("/projects");

  return (
    <div>
      <PageHeader
        title="Projects"
        subtitle="Delivery health across every active initiative."
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

      {data && data.length === 0 && <Empty>No projects yet.</Empty>}

      <div className="space-y-2">
        {data?.map((p) => (
          <Link key={p.id} href={`/projects/${p.id}`}>
            <Card className="animate-rise cursor-pointer">
              <CardContent className="flex items-center justify-between gap-3 p-4">
                <div className="flex items-center gap-3">
                  <FolderKanban className="size-4 text-primary" />
                  <div>
                    <p className="text-sm font-medium">{p.name}</p>
                    {p.description && (
                      <p className="line-clamp-1 text-xs text-muted-foreground">
                        {p.description}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {p.budget != null && (
                    <span className="metric hidden text-xs text-muted sm:inline">
                      ${p.budget.toLocaleString()}
                    </span>
                  )}
                  <Badge tone={toneForLevel(p.status)}>{p.status}</Badge>
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
