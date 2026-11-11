"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Plus, Sparkles, X } from "lucide-react";

import { ApiError, getBlueprint, runDiscovery } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import type { DiscoveryResult, FounderInterview } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-1000", "1000+"];
const MARKETS = [
  { value: "B2B", label: "B2B — businesses" },
  { value: "B2C", label: "B2C — consumers" },
  { value: "mixed", label: "Mixed / marketplace" },
];

const STEPS = ["Your business", "Scale", "Goals & challenges"];

const selectClass =
  "flex h-9 w-full rounded-md border border-border bg-surface px-3 py-1 text-sm text-foreground shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary";

const EMPTY: FounderInterview = {
  industry: "",
  business_model: "",
  company_size: "11-50",
  annual_revenue: null,
  employee_count: null,
  primary_goals: [],
  main_challenges: [],
  target_market: "B2B",
};

export default function OnboardingPage() {
  const router = useRouter();
  const hydrated = useAuthStore((s) => s.hydrated);
  const accessToken = useAuthStore((s) => s.accessToken);
  const orgName = useAuthStore((s) => s.organization?.name);

  const [checking, setChecking] = useState(true);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FounderInterview>(EMPTY);
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Guard: require auth; skip onboarding if it's already been completed.
  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    let active = true;
    getBlueprint()
      .then((bp) => {
        if (!active) return;
        if (bp) router.replace("/dashboard");
        else setChecking(false);
      })
      .catch(() => active && setChecking(false));
    return () => {
      active = false;
    };
  }, [hydrated, accessToken, router]);

  const update = useCallback(
    <K extends keyof FounderInterview>(key: K, value: FounderInterview[K]) =>
      setForm((f) => ({ ...f, [key]: value })),
    [],
  );

  const step0Valid =
    form.industry.trim() !== "" && form.business_model.trim() !== "";

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await runDiscovery(form);
      setResult(res);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Discovery failed. Try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (!hydrated || checking) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  if (result) {
    return <BlueprintReveal result={result} onEnter={() => router.replace("/dashboard")} />;
  }

  return (
    <main className="mx-auto flex min-h-full w-full max-w-2xl flex-1 flex-col justify-center px-5 py-10">
      <div className="animate-rise space-y-2">
        <div className="flex items-center gap-2 text-primary">
          <Sparkles className="size-4" />
          <span className="text-xs font-medium uppercase tracking-wider">
            Business discovery
          </span>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Let&apos;s map {orgName ?? "your business"}.
        </h1>
        <p className="text-sm text-muted-foreground">
          A few questions in your own words. STRATIQA turns them into your
          Business DNA, a strategic blueprint, and tracked goals — grounded in
          what you tell us, never generic.
        </p>
      </div>

      {/* Stepper */}
      <div className="mt-8 flex items-center gap-2">
        {STEPS.map((label, i) => (
          <div key={label} className="flex flex-1 items-center gap-2">
            <div
              className={`flex size-6 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
                i <= step
                  ? "bg-primary text-white"
                  : "bg-surface text-muted-foreground"
              }`}
            >
              {i + 1}
            </div>
            <span
              className={`hidden text-xs sm:inline ${
                i === step ? "text-foreground" : "text-muted-foreground"
              }`}
            >
              {label}
            </span>
            {i < STEPS.length - 1 && (
              <div className="h-px flex-1 bg-border" />
            )}
          </div>
        ))}
      </div>

      <Card className="mt-6">
        <CardContent className="space-y-5 p-6">
          {step === 0 && (
            <>
              <Field label="Industry" hint="e.g. Manufacturing, SaaS, Healthcare">
                <Input
                  value={form.industry}
                  onChange={(e) => update("industry", e.target.value)}
                  placeholder="What industry are you in?"
                />
              </Field>
              <Field
                label="Business model"
                hint="How you make money — e.g. Subscription, Hardware, Marketplace"
              >
                <Input
                  value={form.business_model}
                  onChange={(e) => update("business_model", e.target.value)}
                  placeholder="Subscription / SaaS"
                />
              </Field>
              <div className="grid gap-5 sm:grid-cols-2">
                <Field label="Company size">
                  <select
                    className={selectClass}
                    value={form.company_size}
                    onChange={(e) => update("company_size", e.target.value)}
                  >
                    {COMPANY_SIZES.map((s) => (
                      <option key={s} value={s}>
                        {s} people
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Primary market">
                  <select
                    className={selectClass}
                    value={form.target_market ?? ""}
                    onChange={(e) => update("target_market", e.target.value)}
                  >
                    {MARKETS.map((m) => (
                      <option key={m.value} value={m.value}>
                        {m.label}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
            </>
          )}

          {step === 1 && (
            <>
              <Field
                label="Annual revenue (USD)"
                hint="Approximate is fine — leave blank if pre-revenue"
              >
                <Input
                  type="number"
                  min={0}
                  value={form.annual_revenue ?? ""}
                  onChange={(e) =>
                    update(
                      "annual_revenue",
                      e.target.value === "" ? null : Number(e.target.value),
                    )
                  }
                  placeholder="1500000"
                />
              </Field>
              <Field label="Team size (headcount)" hint="Full-time equivalents">
                <Input
                  type="number"
                  min={0}
                  value={form.employee_count ?? ""}
                  onChange={(e) =>
                    update(
                      "employee_count",
                      e.target.value === "" ? null : Number(e.target.value),
                    )
                  }
                  placeholder="22"
                />
              </Field>
              <p className="text-xs text-muted-foreground">
                These calibrate your growth stage and operational complexity.
              </p>
            </>
          )}

          {step === 2 && (
            <>
              <ChipField
                label="Primary goals"
                hint="What are you trying to achieve? Each becomes a tracked strategic goal."
                placeholder="Reach $5M ARR"
                values={form.primary_goals}
                onChange={(v) => update("primary_goals", v)}
              />
              <ChipField
                label="Main challenges"
                hint="What's standing in the way right now?"
                placeholder="Supplier delays"
                values={form.main_challenges}
                onChange={(v) => update("main_challenges", v)}
              />
            </>
          )}

          {error && (
            <div className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
              {error}
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0 || submitting}
            >
              <ArrowLeft className="size-4" />
              Back
            </Button>

            {step < STEPS.length - 1 ? (
              <Button
                size="sm"
                onClick={() => setStep((s) => s + 1)}
                disabled={step === 0 && !step0Valid}
              >
                Continue
                <ArrowRight className="size-4" />
              </Button>
            ) : (
              <Button size="sm" onClick={submit} disabled={submitting}>
                <Sparkles className={submitting ? "size-4 animate-pulse" : "size-4"} />
                {submitting ? "Analyzing…" : "Generate blueprint"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

// --- Field helpers -----------------------------------------------------------

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function ChipField({
  label,
  hint,
  placeholder,
  values,
  onChange,
}: {
  label: string;
  hint?: string;
  placeholder: string;
  values: string[];
  onChange: (v: string[]) => void;
}) {
  const [draft, setDraft] = useState("");

  function add() {
    const v = draft.trim();
    if (!v) return;
    if (!values.includes(v)) onChange([...values, v]);
    setDraft("");
  }

  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              add();
            }
          }}
          placeholder={placeholder}
        />
        <Button type="button" variant="outline" size="sm" onClick={add}>
          <Plus className="size-4" />
          Add
        </Button>
      </div>
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      {values.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {values.map((v) => (
            <span
              key={v}
              className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-1 text-xs"
            >
              {v}
              <button
                type="button"
                onClick={() => onChange(values.filter((x) => x !== v))}
                className="text-muted-foreground hover:text-danger"
                aria-label={`Remove ${v}`}
              >
                <X className="size-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Blueprint reveal --------------------------------------------------------

function BlueprintReveal({
  result,
  onEnter,
}: {
  result: DiscoveryResult;
  onEnter: () => void;
}) {
  const { dna, blueprint } = result;
  const bp = blueprint.blueprint_json;
  const dnaItems = [
    { label: "Growth stage", value: dna.growth_stage },
    { label: "Risk profile", value: dna.risk_profile },
    { label: "Complexity", value: dna.operational_complexity },
    { label: "Market", value: dna.market_type },
  ];

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-5 py-10">
      <div className="animate-rise space-y-2 text-center">
        <div className="flex items-center justify-center gap-2 text-primary">
          <Sparkles className="size-4" />
          <span className="text-xs font-medium uppercase tracking-wider">
            Your blueprint is ready
          </span>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">Business DNA</h1>
        <p className="text-sm text-muted-foreground">
          Derived from your answers. This now grounds every recommendation
          STRATIQA makes.
        </p>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {dnaItems.map((d) => (
          <Card key={d.label} className="animate-rise">
            <CardContent className="p-4">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
                {d.label}
              </p>
              <p className="mt-1 text-sm font-medium capitalize">
                {d.value?.replace(/_/g, " ") ?? "—"}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="space-y-2 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">
              Recommended focus areas
            </p>
            <ul className="space-y-1.5">
              {bp.recommended_focus_areas.map((a) => (
                <li key={a} className="flex items-start gap-2 text-sm">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                  {a}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-2 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">
              Suggested KPIs to track
            </p>
            <div className="flex flex-wrap gap-2">
              {bp.suggested_kpis.map((k) => (
                <Badge key={k} tone="info">
                  {k}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {bp.stated_goals.length > 0 && (
        <Card className="mt-4">
          <CardContent className="space-y-2 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">
              Goals now being tracked
            </p>
            <div className="flex flex-wrap gap-2">
              {bp.stated_goals.map((g) => (
                <Badge key={g} tone="success">
                  {g}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Button className="mt-8 w-full" onClick={onEnter}>
        Enter STRATIQA One
        <ArrowRight className="size-4" />
      </Button>
    </main>
  );
}
