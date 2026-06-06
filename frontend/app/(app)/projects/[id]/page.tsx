"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Circle,
  Flag,
  Plus,
} from "lucide-react";

import { apiFetch } from "@/lib/api";
import { C, gauge } from "@/lib/charts";
import type { ProjectDetail, TaskOut } from "@/lib/types";
import { useApi } from "@/lib/use-api";
import { Badge, toneForLevel } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EChart } from "@/components/charts/echart";
import { Section, SkeletonBlock } from "@/components/dashboard/primitives";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useApi<ProjectDetail>(`/projects/${id}`);
  const [newTask, setNewTask] = useState("");
  const [adding, setAdding] = useState(false);

  async function addTask() {
    const title = newTask.trim();
    if (!title) return;
    setAdding(true);
    try {
      await apiFetch<TaskOut>(`/projects/${id}/tasks`, {
        method: "POST",
        body: { title, priority: "medium", status: "todo" },
      });
      setNewTask("");
      reload();
    } catch {
      /* ignore */
    } finally {
      setAdding(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }
  if (!data) return <SkeletonBlock className="h-64" />;

  const h = data.health;
  const healthColor =
    h.score >= 75 ? C.success : h.score >= 45 ? C.warning : C.danger;

  return (
    <div className="space-y-6">
      <Link
        href="/projects"
        className="inline-flex items-center gap-1 text-xs text-muted hover:text-foreground"
      >
        <ArrowLeft className="size-3" /> Projects
      </Link>

      <div className="animate-rise flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{data.name}</h1>
          {data.description && (
            <p className="mt-1 max-w-2xl text-sm text-muted">{data.description}</p>
          )}
        </div>
        <Badge tone={toneForLevel(data.status)}>{data.status}</Badge>
      </div>

      {/* Health */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Health score</CardTitle>
          </CardHeader>
          <CardContent>
            <EChart option={gauge(h.score, healthColor)} height={150} />
            <div className="text-center">
              <Badge tone={toneForLevel(h.label)}>{h.label.replace(/_/g, " ")}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Health drivers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <Stat label="Open tasks" value={h.open_tasks} />
              <Stat label="Overdue" value={h.overdue_tasks} danger={h.overdue_tasks > 0} />
              <Stat label="Open risks" value={h.open_risks} danger={h.open_risks > 0} />
            </div>
            <ul className="space-y-1.5 border-t border-border pt-3 text-sm text-muted">
              {h.drivers.map((d, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-muted-foreground" />
                  {d}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Tasks */}
      <Section title="Tasks">
        <Card>
          <CardContent className="divide-y divide-border p-0">
            {data.tasks.length === 0 ? (
              <p className="p-4 text-xs text-muted-foreground">No tasks.</p>
            ) : (
              data.tasks.map((t) => (
                <div key={t.id} className="flex items-center gap-3 px-4 py-3">
                  {t.status === "done" ? (
                    <CheckCircle2 className="size-4 text-success" />
                  ) : (
                    <Circle className="size-4 text-muted-foreground" />
                  )}
                  <span className="flex-1 text-sm">{t.title}</span>
                  {t.due_date && (
                    <span className="metric text-xs text-muted-foreground">
                      {t.due_date}
                    </span>
                  )}
                  <Badge tone={toneForLevel(t.priority)}>{t.priority}</Badge>
                  <Badge tone={toneForLevel(t.status)}>{t.status}</Badge>
                </div>
              ))
            )}
            <div className="flex items-center gap-2 p-3">
              <Input
                value={newTask}
                onChange={(e) => setNewTask(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addTask()}
                placeholder="Add a task…"
              />
              <Button onClick={addTask} disabled={adding || !newTask.trim()} size="icon">
                <Plus />
              </Button>
            </div>
          </CardContent>
        </Card>
      </Section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Milestones">
          <Card>
            <CardContent className="divide-y divide-border p-0">
              {data.milestones.length === 0 ? (
                <p className="p-4 text-xs text-muted-foreground">No milestones.</p>
              ) : (
                data.milestones.map((m) => (
                  <div key={m.id} className="flex items-center gap-3 px-4 py-3">
                    <Flag className="size-4 text-info" />
                    <span className="flex-1 text-sm">{m.title}</span>
                    {m.due_date && (
                      <span className="metric text-xs text-muted-foreground">
                        {m.due_date}
                      </span>
                    )}
                    <Badge tone={toneForLevel(m.status)}>{m.status}</Badge>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </Section>

        <Section title="Risks">
          <Card>
            <CardContent className="divide-y divide-border p-0">
              {data.risks.length === 0 ? (
                <p className="p-4 text-xs text-muted-foreground">No risks recorded.</p>
              ) : (
                data.risks.map((r) => (
                  <div key={r.id} className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="size-4 text-danger" />
                      <span className="flex-1 text-sm font-medium">
                        {r.risk_title}
                      </span>
                      <Badge tone={toneForLevel(r.risk_level)}>{r.risk_level}</Badge>
                    </div>
                    {r.impact && (
                      <p className="mt-1 pl-6 text-xs text-muted">{r.impact}</p>
                    )}
                    {r.mitigation && (
                      <p className="mt-0.5 pl-6 text-xs text-success">
                        Mitigation: {r.mitigation}
                      </p>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </Section>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  danger,
}: {
  label: string;
  value: number;
  danger?: boolean;
}) {
  return (
    <div className="rounded-md border border-border bg-surface/50 p-3 text-center">
      <p className={`metric text-xl font-semibold ${danger ? "text-danger" : ""}`}>
        {value}
      </p>
      <p className="mt-0.5 text-[11px] text-muted-foreground">{label}</p>
    </div>
  );
}
