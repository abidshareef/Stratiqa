"""One-off: render ABSTRACT.md into a formatted 2-page Word document."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

OUT = Path(__file__).resolve().parents[1] / "ABSTRACT.docx"
PRIMARY = RGBColor(0x25, 0x63, 0xEB)

doc = Document()

# Base font
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)


def heading(text: str) -> None:
    p = doc.add_paragraph()
    p.space_before = Pt(10)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = PRIMARY


def subheading(text: str) -> None:
    p = doc.add_paragraph()
    p.space_before = Pt(6)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)


def para(text: str) -> None:
    doc.add_paragraph(text)


def bold_lead_bullet(lead: str, rest: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(lead)
    r.bold = True
    p.add_run(rest)


def bullet(text: str) -> None:
    doc.add_paragraph(text, style="List Bullet")


# --- Title block -------------------------------------------------------------
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("STRATIQA — Strategic Intelligence & Analytics Platform")
r.bold = True
r.font.size = Pt(18)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = sub.add_run("An AI-Powered Business Operating System")
rs.bold = True
rs.font.size = Pt(13)
rs.font.color.rgb = PRIMARY

it = doc.add_paragraph()
it.alignment = WD_ALIGN_PARAGRAPH.CENTER
ri = it.add_run("Project Abstract")
ri.italic = True

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run("Submitted by: [Your Name / Team]   |   Guide: [Guide Name]   |   Date: June 9, 2026").italic = True

# --- Abstract ----------------------------------------------------------------
heading("Abstract")
para(
    "STRATIQA is a multi-tenant, AI-powered Business Operating System that closes the gap "
    "between data and decision. Unlike conventional business-intelligence tools that stop at "
    "charts and raw numbers, STRATIQA understands a specific business, continuously reasons over "
    "its real operational data, and surfaces explainable, grounded recommendations that "
    "executives can trust and act on. Every insight the platform produces is tied to the "
    "company’s own data and accompanied by its reasoning, expected impact, confidence score, and "
    "source — never a generic tip and never an opaque, black-box output."
)

# --- Existing System ---------------------------------------------------------
heading("Existing System")
para(
    "Today, founders, CEOs, and operations leaders rely on a fragmented mix of spreadsheets, "
    "traditional Business Intelligence (BI) dashboards, and general-purpose AI chatbots to run "
    "their organizations. These tools share a common, fundamental limitation: they present "
    "information but do not produce decisions. The existing approach suffers from the following "
    "drawbacks:"
)
existing = [
    ("Analytics without intelligence", " — Conventional BI tools display charts and raw metrics, "
     "then leave the hardest part — interpreting what the data means and deciding what to do next "
     "— entirely to the human."),
    ("Generic, black-box advice", " — Existing “AI advisor” products generate generic "
     "recommendations disconnected from a company’s actual situation, with no reasoning, no "
     "confidence level, and no traceability to source data, so leaders cannot trust or verify "
     "them."),
    ("No grounding in the business", " — Generic chatbots have no model of the specific "
     "organization — its goals, projects, customers, products, and risks — so their answers are "
     "not anchored in the company’s real state."),
    ("Fragmented and manual", " — Data lives in disconnected silos; consolidating and "
     "interpreting it is slow, manual, and error-prone, leading to gut-driven rather than "
     "evidence-driven decisions."),
    ("Reactive, not proactive", " — Existing systems rarely detect KPI deterioration, anomalies, "
     "or emerging risks early; problems are often noticed only after they become losses."),
]
for lead, rest in existing:
    bold_lead_bullet(lead, rest)
para(
    "The net result is a paradox: organizations are drowning in dashboards yet starved of "
    "decisions, with analytics that inform but never act."
)

# --- Proposed System ---------------------------------------------------------
heading("Proposed System")
para(
    "STRATIQA is an integrated operating system for strategic decision-making built on the "
    "principle of intelligence before analytics. At its center sits STRATIQA One, a master "
    "intelligence agent that orchestrates specialized domain agents across the business. A new "
    "organization is onboarded through a short Business Discovery interview that is transformed — "
    "using transparent, explainable logic — into a Business DNA profile, a strategic Blueprint, "
    "and a set of automatically tracked goals, so the platform is grounded in the company from "
    "day one. Businesses then feed in their real operational data, which STRATIQA’s engines "
    "convert into prioritized risks, opportunities, and recommendations surfaced through two "
    "signature interfaces: the STRATIQA One Home and the Executive War Room. Its key features "
    "are:"
)
features = [
    ("Business Discovery & DNA", " — A guided founder interview becomes an explainable Business "
     "Profile, DNA (growth stage, risk profile, complexity, market type), strategic blueprint, "
     "and auto-seeded goals, making a brand-new account immediately useful."),
    ("Explainable Recommendation Engine", " — Continuously analyzes the organization’s goals, "
     "projects, risks, tasks, and KPIs to generate grounded recommendations, each carrying a "
     "title, reasoning, expected impact, confidence score, risk level, and data sources in a "
     "dedicated explainability panel — no black box."),
    ("File-Based Data Ingestion", " — Businesses upload existing files (CSV, Excel, PDF, Word); "
     "STRATIQA parses them deterministically, confirms a smart column mapping, and ingests rows "
     "into KPIs, customers, and products — instantly feeding the recommendation engine."),
    ("STRATIQA One & Specialized AI Agents", " — A master agent plus eight domain specialists "
     "(Finance, Sales, Project, Risk, Customer Success, Product, HR) translate raw signals into "
     "executive-level findings and answer per-agent questions."),
    ("Business Twin (Digital Twin)", " — Simulates strategic scenarios and “what-if” outcomes "
     "against the company’s modeled state to support forward-looking decisions."),
    ("Knowledge Graph", " — Connects entities into a navigable, force-directed network that "
     "reveals relationships and clustered communities across the business."),
    ("Customer & Product Intelligence", " — Surfaces account health, churn risk, support load, "
     "product performance, and inventory signals — each grounded in the underlying data."),
    ("Alerts & Monitoring", " — Detects KPI deterioration, anomalies, and high-severity risks "
     "early, escalating incidents before they become losses."),
    ("Reports & Executive Briefs", " — Generates board-ready reports and concise executive "
     "summaries automatically from live data."),
    ("Continuous Learning Loop", " — Captures user feedback (accept / dismiss / outcome) on every "
     "recommendation, building the foundation for confidence tuning and adaptive intelligence."),
]
for lead, rest in features:
    bold_lead_bullet(lead, rest)
para(
    "The platform is architected as a secure, modular monolith with strict multi-tenancy, JWT "
    "authentication, and role-based access control, so every entity is isolated per organization."
)

# --- Software Specifications --------------------------------------------------
heading("Software Specifications")

subheading("Frontend")
bullet("Next.js 15 (App Router) with TypeScript and Tailwind CSS")
bullet("ShadCN UI components, Zustand (state), React Hook Form + Zod (forms/validation)")
bullet("Apache ECharts (data visualization), Framer Motion (subtle animation)")
bullet("Executive-grade, dark-mode-first interface")

subheading("Backend")
bullet("FastAPI on Python 3.12, with Pydantic for schemas and validation")
bullet("PostgreSQL (production), 55+ table, 16-section multi-tenant schema; SQLite for development")
bullet("Redis (caching/queues), Celery (background jobs), Qdrant (vector memory)")
bullet("JWT authentication with role-based access control (RBAC)")

subheading("Artificial Intelligence")
bullet("Provider-agnostic LLM gateway (OpenAI / Gemini / Claude / local models)")
bullet("Transparent, rule-based grounding for the MVP so every output is data-anchored")

subheading("Development & Deployment Environment")
bullet("OS: Windows / Linux / macOS (cross-platform)")
bullet("Tooling: Node.js + npm (frontend); Python virtual environment + pip (backend)")
bullet("Quality: pytest test suite and Ruff linting; runnable locally with no external infrastructure")

subheading("Recommended Hardware (development)")
bullet("Processor: Intel Core i5 / equivalent or higher")
bullet("Memory: 8 GB RAM minimum (16 GB recommended)")
bullet("Storage: 5 GB free disk space")
bullet("Network: Internet connection (required only when using cloud LLM providers)")

# --- Conclusion --------------------------------------------------------------
heading("Conclusion")
para(
    "By grounding every output in a company’s own information and exposing the reasoning behind "
    "it, STRATIQA turns scattered business data into trustworthy, explainable, and actionable "
    "strategic intelligence — giving leaders not just a clearer view of their business, but a "
    "clear recommendation on what to do next."
)

doc.save(OUT)
print(f"Saved: {OUT}")
