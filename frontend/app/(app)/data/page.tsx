"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  TriangleAlert,
  Upload,
} from "lucide-react";

import {
  ApiError,
  commitUpload,
  listUploads,
  uploadFile,
} from "@/lib/api";
import type {
  CommitResult,
  IngestTarget,
  UploadDetail,
  UploadOut,
} from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/page-header";
import { Empty, Section, SkeletonBlock } from "@/components/dashboard/primitives";
import { cn } from "@/lib/utils";

const ACCEPT = ".csv,.tsv,.xlsx,.xls,.pdf,.docx,.png,.jpg,.jpeg,.webp";

const selectClass =
  "flex h-9 w-full rounded-md border border-border bg-surface px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary";

const NONE = "__none__";

const TARGETS: { value: IngestTarget; label: string; hint: string }[] = [
  { value: "kpi", label: "KPI time-series", hint: "Each row → a metric reading (drives trend & decline detection)" },
  { value: "products", label: "Products", hint: "Each row → a product + sales/inventory metrics" },
  { value: "customers", label: "Customers", hint: "Each row → an account + health/churn" },
];

const TARGET_FIELDS: Record<
  IngestTarget,
  { key: string; label: string; required?: boolean }[]
> = {
  kpi: [
    { key: "value", label: "Metric value", required: true },
    { key: "date", label: "Date / period" },
    { key: "kpi_name", label: "Metric name (column)" },
  ],
  customers: [
    { key: "customer_name", label: "Customer name", required: true },
    { key: "segment", label: "Segment" },
    { key: "churn_risk", label: "Churn risk (%)" },
    { key: "health_score", label: "Health score" },
  ],
  products: [
    { key: "product_name", label: "Product name", required: true },
    { key: "category", label: "Category" },
    { key: "revenue", label: "Revenue" },
    { key: "sales_count", label: "Units sold" },
    { key: "quantity", label: "Stock quantity" },
  ],
};

function kindIcon(kind: string) {
  if (kind === "image") return ImageIcon;
  if (kind === "csv" || kind === "excel") return FileSpreadsheet;
  return FileText;
}

export default function DataPage() {
  const [history, setHistory] = useState<UploadOut[] | null>(null);
  const [upload, setUpload] = useState<UploadDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CommitResult | null>(null);

  const refreshHistory = useCallback(() => {
    listUploads()
      .then(setHistory)
      .catch(() => setHistory([]));
  }, []);

  useEffect(() => refreshHistory(), [refreshHistory]);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setResult(null);
    setUpload(null);
    try {
      const detail = await uploadFile(file);
      setUpload(detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Try again.");
    } finally {
      setBusy(false);
      refreshHistory();
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Data Ingestion"
        subtitle="Upload your business files — sales reports, customer lists, product exports. STRATIQA parses them, you confirm the mapping, and the data immediately feeds your KPIs and recommendations."
      />

      <Dropzone busy={busy} onFile={handleFile} />

      {error && (
        <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {result ? (
        <CommitSuccess result={result} onDone={() => { setResult(null); setUpload(null); }} />
      ) : upload ? (
        <MappingPanel
          upload={upload}
          onCommitted={(r) => setResult(r)}
        />
      ) : null}

      <Section title="Previous uploads" subtitle="Every file you've ingested for this organization.">
        {!history ? (
          <SkeletonBlock className="h-32" />
        ) : history.length === 0 ? (
          <Empty>No uploads yet. Drop a sales report above to begin.</Empty>
        ) : (
          <Card>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted">
                    <th className="px-4 py-3 font-medium">File</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium text-right">Rows</th>
                    <th className="px-4 py-3 font-medium text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((u) => {
                    const Icon = kindIcon(u.file_kind);
                    return (
                      <tr key={u.id} className="border-b border-border/50 last:border-0">
                        <td className="px-4 py-3">
                          <span className="flex items-center gap-2">
                            <Icon className="size-4 text-muted-foreground" />
                            {u.filename}
                          </span>
                        </td>
                        <td className="px-4 py-3 capitalize text-muted-foreground">
                          {u.file_kind}
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {u.row_count || "—"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <StatusBadge status={u.status} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </Section>
    </div>
  );
}

function Dropzone({ busy, onFile }: { busy: boolean; onFile: (f: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) onFile(file);
      }}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed px-6 py-12 text-center transition-colors ${
        over ? "border-primary bg-primary/5" : "border-border bg-surface hover:border-primary/50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = "";
        }}
      />
      <Upload className={`size-7 ${busy ? "animate-pulse text-primary" : "text-muted-foreground"}`} />
      <p className="mt-3 text-sm font-medium">
        {busy ? "Parsing your file…" : "Drop a file here, or click to browse"}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        CSV, Excel, PDF, Word, or image — up to 15 MB
      </p>
    </div>
  );
}

function MappingPanel({
  upload,
  onCommitted,
}: {
  upload: UploadDetail;
  onCommitted: (r: CommitResult) => void;
}) {
  const suggested = upload.suggested_mapping ?? {};
  const [target, setTarget] = useState<IngestTarget>(suggested.target ?? "kpi");
  const [fields, setFields] = useState<Record<string, string>>(suggested.fields ?? {});
  const [kpiLabel, setKpiLabel] = useState(suggested.kpi_label ?? "");
  const [committing, setCommitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Non-tabular files can't be column-mapped.
  if (!upload.columns.length) {
    return (
      <Card>
        <CardContent className="space-y-2 p-5">
          <div className="flex items-center gap-2 text-warning">
            <TriangleAlert className="size-4" />
            <p className="text-sm font-medium">
              {upload.status === "text_only"
                ? "Text extracted — no table to map"
                : "Can't auto-read this file"}
            </p>
          </div>
          <p className="text-sm text-muted-foreground">
            {upload.error ??
              "This file has no tabular columns. Its text is stored for reference, but to feed KPIs, upload a CSV/Excel export or enter the figures manually."}
          </p>
          {upload.extracted_text && (
            <pre className="mt-2 max-h-48 overflow-auto rounded-md border border-border bg-background p-3 text-xs text-muted-foreground">
              {upload.extracted_text.slice(0, 2000)}
            </pre>
          )}
        </CardContent>
      </Card>
    );
  }

  const required = TARGET_FIELDS[target].filter((f) => f.required);
  const missing = required.filter((f) => !fields[f.key]);
  const canCommit = missing.length === 0 && !committing;

  function setField(key: string, col: string) {
    setFields((prev) => {
      const next = { ...prev };
      if (col === NONE) delete next[key];
      else next[key] = col;
      return next;
    });
  }

  function switchTarget(next: IngestTarget) {
    setTarget(next);
    // Keep any field assignments still valid for the new target's keys.
    const validKeys = new Set(TARGET_FIELDS[next].map((f) => f.key));
    setFields((prev) =>
      Object.fromEntries(Object.entries(prev).filter(([k]) => validKeys.has(k))),
    );
  }

  async function commit() {
    setCommitting(true);
    setError(null);
    try {
      const res = await commitUpload(upload.id, {
        target,
        fields,
        kpi_label: target === "kpi" ? kpiLabel || null : null,
      });
      onCommitted(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Commit failed. Try again.");
    } finally {
      setCommitting(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* Preview */}
      <Section
        title={`Preview — ${upload.filename}`}
        subtitle={`${upload.row_count} rows detected. Showing the first ${upload.preview_rows.length}.`}
      >
        <Card>
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted">
                  {upload.columns.map((c) => (
                    <th key={c} className="whitespace-nowrap px-4 py-3 font-medium">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {upload.preview_rows.slice(0, 8).map((row, i) => (
                  <tr key={i} className="border-b border-border/50 last:border-0">
                    {upload.columns.map((c) => (
                      <td key={c} className="whitespace-nowrap px-4 py-2.5 text-muted-foreground">
                        {row[c] === null || row[c] === undefined ? "—" : String(row[c])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </Section>

      {/* Mapping */}
      <Section
        title="Map the columns"
        subtitle="We pre-filled a best guess. Confirm what each column means, then commit."
      >
        <Card>
          <CardContent className="space-y-5 p-5">
            <div className="space-y-1.5">
              <Label>This file represents</Label>
              <select
                className={selectClass}
                value={target}
                onChange={(e) => switchTarget(e.target.value as IngestTarget)}
              >
                {TARGETS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                {TARGETS.find((t) => t.value === target)?.hint}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {TARGET_FIELDS[target].map((f) => (
                <div key={f.key} className="space-y-1.5">
                  <Label>
                    {f.label}
                    {f.required && <span className="ml-1 text-danger">*</span>}
                  </Label>
                  <select
                    className={selectClass}
                    value={fields[f.key] ?? NONE}
                    onChange={(e) => setField(f.key, e.target.value)}
                  >
                    <option value={NONE}>{f.required ? "— select a column —" : "— none —"}</option>
                    {upload.columns.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {target === "kpi" && (
              <div className="space-y-1.5">
                <Label>Metric label</Label>
                <Input
                  value={kpiLabel}
                  onChange={(e) => setKpiLabel(e.target.value)}
                  placeholder="e.g. Monthly Revenue"
                />
                <p className="text-xs text-muted-foreground">
                  Used as the KPI name when there isn&apos;t a metric-name column.
                </p>
              </div>
            )}

            {error && (
              <div className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
                {error}
              </div>
            )}

            <div className="flex items-center justify-between pt-1">
              <p className="text-xs text-muted-foreground">
                {missing.length > 0
                  ? `Map ${missing.map((m) => m.label).join(", ")} to continue.`
                  : "Ready to import."}
              </p>
              <Button size="sm" onClick={commit} disabled={!canCommit}>
                {committing ? "Importing…" : "Commit & refresh insights"}
                <ArrowRight className="size-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </Section>
    </div>
  );
}

function CommitSuccess({
  result,
  onDone,
}: {
  result: CommitResult;
  onDone: () => void;
}) {
  const created = Object.entries(result.created).filter(([, n]) => n > 0);
  const changes = result.analysis_changes;
  const newInsights = changes?.new_insights ?? [];
  const resolvedInsights = changes?.resolved_insights ?? [];
  const shifted = newInsights.length > 0 || resolvedInsights.length > 0;
  return (
    <Card className="animate-rise">
      <CardContent className="space-y-4 p-6">
        <div className="flex items-center gap-2 text-success">
          <CheckCircle2 className="size-5" />
          <p className="text-sm font-semibold">Imported successfully</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {created.map(([k, n]) => (
            <Badge key={k} tone="success">
              {n} {k.replace(/_/g, " ")}
            </Badge>
          ))}
          {result.skipped > 0 && (
            <Badge tone="warning">{result.skipped} rows skipped</Badge>
          )}
          <Badge tone="info">
            {result.recommendations_refreshed} recommendations refreshed
          </Badge>
        </div>

        {shifted ? (
          <div className="space-y-3 rounded-md border border-border bg-background/60 p-4">
            <p className="text-sm font-medium">How this data changed your analysis</p>
            {newInsights.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium uppercase tracking-wider text-success">
                  New signals ({newInsights.length})
                </p>
                <ul className="space-y-1">
                  {newInsights.map((t) => (
                    <li key={t} className="flex items-start gap-2 text-sm text-foreground">
                      <ArrowRight className="mt-0.5 size-3.5 shrink-0 text-success" />
                      {t}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {resolvedInsights.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Resolved — no longer flagged ({resolvedInsights.length})
                </p>
                <ul className="space-y-1">
                  {resolvedInsights.map((t) => (
                    <li
                      key={t}
                      className="flex items-start gap-2 text-sm text-muted-foreground line-through"
                    >
                      <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                      {t}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p className="rounded-md border border-border bg-background/60 px-4 py-3 text-sm text-muted-foreground">
            Re-analyzed with the new data — no change to the active signals.
          </p>
        )}

        <p className="text-sm text-muted-foreground">
          Your new data is live. The recommendation engine has already re-analyzed
          it — check your dashboard for any new signals.
        </p>
        <div className="flex gap-2">
          <Link
            href="/dashboard"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
          >
            View dashboard <ArrowRight className="size-4" />
          </Link>
          <Button size="sm" variant="ghost" onClick={onDone}>
            Upload another
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "committed"
      ? "success"
      : status === "parsed"
        ? "info"
        : status === "failed"
          ? "danger"
          : "warning";
  return <Badge tone={tone as never}>{status.replace(/_/g, " ")}</Badge>;
}
