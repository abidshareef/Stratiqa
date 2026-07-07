"""Render a ~15-page project report for STRATIQA into a formatted Word document.

Enhancements: auto-updating Table of Contents, header + page-number footer,
professional academic styling, and embedded architecture/schema diagrams.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

import make_report_diagrams as diagrams

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "STRATIQA_Project_Report.docx"
PRIMARY = RGBColor(0x25, 0x63, 0xEB)
DARK = RGBColor(0x11, 0x11, 0x11)

BODY_FONT = "Times New Roman"
HEAD_FONT = "Calibri"

doc = Document()

# --- Base / body style -------------------------------------------------------
normal = doc.styles["Normal"]
normal.font.name = BODY_FONT
normal.font.size = Pt(12)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.4
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# --- Heading styles (so the TOC can pick them up) ----------------------------
hs1 = doc.styles["Heading 1"]
hs1.font.name = HEAD_FONT
hs1.font.size = Pt(17)
hs1.font.bold = True
hs1.font.color.rgb = PRIMARY
hs1.paragraph_format.space_before = Pt(6)
hs1.paragraph_format.space_after = Pt(10)
hs1.paragraph_format.page_break_before = True  # each top section starts a new page

hs2 = doc.styles["Heading 2"]
hs2.font.name = HEAD_FONT
hs2.font.size = Pt(13)
hs2.font.bold = True
hs2.font.color.rgb = DARK
hs2.paragraph_format.space_before = Pt(8)
hs2.paragraph_format.space_after = Pt(4)

_section_no = 0


# --- helpers -----------------------------------------------------------------
def h1(text: str, numbered_section: bool = True) -> None:
    global _section_no
    if numbered_section:
        _section_no += 1
        text = f"{_section_no}.  {text}"
    doc.add_heading(text, level=1)


def h2(text: str) -> None:
    doc.add_heading(text, level=2)


def para(text: str) -> None:
    doc.add_paragraph(text)


def bullet(text: str) -> None:
    doc.add_paragraph(text, style="List Bullet")


def numbered(text: str) -> None:
    doc.add_paragraph(text, style="List Number")


def bold_lead_bullet(lead: str, rest: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(lead)
    r.bold = True
    p.add_run(rest)


def caption(text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.italic = True
    r.font.size = Pt(10)


def add_image(path: Path, width_in: float, cap: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width_in))
    caption(cap)


def make_table(headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, htext in enumerate(headers):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(htext)
        run.bold = True
        run.font.size = Pt(10.5)
        run.font.name = HEAD_FONT
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(val)
            run.font.size = Pt(10)
            run.font.name = BODY_FONT
    doc.add_paragraph()


def _field(paragraph, instr: str, placeholder: str) -> None:
    """Insert a Word field (e.g. PAGE, TOC) into a paragraph."""
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    placeholder_el = OxmlElement("w:t")
    placeholder_el.text = placeholder
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r = run._r
    r.append(fld_begin)
    r.append(instr_el)
    r.append(fld_sep)
    r.append(placeholder_el)
    r.append(fld_end)


def set_update_fields_on_open() -> None:
    """Tell Word to refresh all fields (so the TOC populates) when opened."""
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)


def add_header_footer() -> None:
    section = doc.sections[0]
    # Header — project title
    header = section.header
    hp = header.paragraphs[0]
    hp.text = ""
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hp.add_run("STRATIQA — Strategic Intelligence & Analytics Platform")
    hr.font.size = Pt(8.5)
    hr.font.color.rgb = RGBColor(0x77, 0x77, 0x77)
    hr.font.name = HEAD_FONT
    # Footer — Page X of Y
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = ""
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.add_run("Page ").font.size = Pt(9)
    _field(fp, "PAGE", "1")
    fp.add_run(" of ").font.size = Pt(9)
    _field(fp, "NUMPAGES", "1")
    for run in fp.runs:
        run.font.size = Pt(9)
        run.font.name = HEAD_FONT
        run.font.color.rgb = RGBColor(0x77, 0x77, 0x77)


# ===========================================================================
# TITLE PAGE
# ===========================================================================
for _ in range(3):
    doc.add_paragraph()

t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("STRATIQA")
r.bold = True
r.font.size = Pt(44)
r.font.color.rgb = PRIMARY
r.font.name = HEAD_FONT

s = doc.add_paragraph()
s.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = s.add_run("Strategic Intelligence & Analytics Platform")
rs.bold = True
rs.font.size = Pt(18)
rs.font.name = HEAD_FONT

s2 = doc.add_paragraph()
s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs2 = s2.add_run("An AI-Powered Business Operating System")
rs2.italic = True
rs2.font.size = Pt(14)

for _ in range(4):
    doc.add_paragraph()

pr = doc.add_paragraph()
pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
pr.add_run("A Project Report").font.size = Pt(13)

pr2 = doc.add_paragraph()
pr2.alignment = WD_ALIGN_PARAGRAPH.CENTER
pr2.add_run(
    "Submitted in partial fulfillment of the requirements for the award of the degree"
).font.size = Pt(11)

for _ in range(6):
    doc.add_paragraph()

dt = doc.add_paragraph()
dt.alignment = WD_ALIGN_PARAGRAPH.CENTER
dt.add_run("Department of Computer Science & Engineering").bold = True
dt2 = doc.add_paragraph()
dt2.alignment = WD_ALIGN_PARAGRAPH.CENTER
dt2.add_run("[ Institution / University Name ]")
dt3 = doc.add_paragraph()
dt3.alignment = WD_ALIGN_PARAGRAPH.CENTER
dt3.add_run("June 2026").italic = True

# ===========================================================================
# TABLE OF CONTENTS
# ===========================================================================
doc.add_page_break()
toc_title = doc.add_paragraph()
toc_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
rt = toc_title.add_run("Table of Contents")
rt.bold = True
rt.font.size = Pt(17)
rt.font.color.rgb = PRIMARY
rt.font.name = HEAD_FONT
doc.add_paragraph()
toc_p = doc.add_paragraph()
_field(
    toc_p,
    'TOC \\o "1-2" \\h \\z \\u',
    "Right-click here and choose “Update Field” to build the table of contents.",
)

# ===========================================================================
# 1. TEAM MEMBERS
# ===========================================================================
h1("Team Members")
para(
    "This project was conceived, designed, and developed by the following team members under "
    "the guidance of the project guide. Each member contributed across the full stack — from "
    "requirement analysis and database design to backend services, frontend interfaces, and "
    "testing."
)
make_table(
    ["S. No.", "Name", "Roll Number", "Role / Contribution"],
    [
        ["1", "[Member 1 Name]", "[Roll No.]", "Team Lead — Architecture & Backend Services"],
        ["2", "[Member 2 Name]", "[Roll No.]", "Frontend & UI/UX (Next.js, ECharts)"],
        ["3", "[Member 3 Name]", "[Roll No.]", "Database Design & Data Ingestion"],
        ["4", "[Member 4 Name]", "[Roll No.]", "AI Agents & Recommendation Engine"],
    ],
)
h2("Project Guide")
make_table(
    ["Name", "Designation", "Department"],
    [["[Guide Name]", "[Designation]", "Computer Science & Engineering"]],
)

# ===========================================================================
# 2. ABSTRACT
# ===========================================================================
h1("Abstract")
para(
    "STRATIQA is a multi-tenant, AI-powered Business Operating System that closes the gap "
    "between data and decision. Unlike conventional business-intelligence (BI) tools that stop "
    "at charts and raw numbers, STRATIQA understands a specific business, continuously reasons "
    "over its real operational data, and surfaces explainable, grounded recommendations that "
    "executives can trust and act on. Every insight the platform produces is tied to the "
    "company’s own data and accompanied by its reasoning, expected impact, confidence score, "
    "and source — never a generic tip and never an opaque, black-box output."
)
para(
    "The platform is built on the principle of intelligence before analytics. At its center sits "
    "STRATIQA One, a master intelligence agent that orchestrates a set of specialized domain "
    "agents (Finance, Sales, Project, Risk, Customer Success, Product, and HR). A new "
    "organization is onboarded through a short Business Discovery interview that is transformed "
    "into a Business DNA profile, a strategic Blueprint, and a set of automatically tracked "
    "goals, so the platform is grounded in the company from day one. Businesses then feed in "
    "their real operational data through file uploads, which the engines convert into prioritized "
    "risks, opportunities, and recommendations surfaced through two signature interfaces: the "
    "STRATIQA One Home and the Executive War Room."
)
para(
    "STRATIQA is implemented as a secure, modular monolith with strict multi-tenancy, JWT "
    "authentication, and role-based access control. The backend is built with FastAPI and Python "
    "over a 55+ table relational schema; the frontend is a Next.js + TypeScript application with "
    "an executive-grade, dark-mode-first interface. The result is a working system that turns "
    "scattered business data into trustworthy, explainable, and actionable strategic "
    "intelligence."
)

# ===========================================================================
# 3. INTRODUCTION
# ===========================================================================
h1("Introduction")
para(
    "Modern organizations generate more data than ever before, yet the leaders who must act on "
    "that data — founders, CEOs, and operations heads — are increasingly overwhelmed. They are "
    "surrounded by dashboards, spreadsheets, and reports, but the critical task of interpreting "
    "what all of it means and deciding what to do next still rests entirely on human judgment. "
    "The promise of analytics has been to make better decisions; in practice, most tools merely "
    "present numbers and leave the decision-making untouched."
)
para(
    "This gap is the central problem STRATIQA addresses. The platform is not another dashboard, "
    "BI tool, or generic chatbot. It is an integrated operating system for strategic "
    "decision-making that understands a specific business, reasons over its real data, and "
    "recommends concrete actions — each one explainable and traceable to its source."
)
h2("Problem Statement")
para(
    "Existing business-intelligence tools, spreadsheets, and general-purpose AI chatbots present "
    "charts and raw numbers, then leave the hardest part — interpreting what the data means and "
    "deciding what to do next — entirely to the human. The few AI advisors on the market produce "
    "generic, black-box advice disconnected from a company’s actual situation, offering no "
    "reasoning, no confidence, and no traceability to source data. The result is slow, "
    "gut-driven decision-making and analytics that inform but never act."
)
h2("Motivation")
para(
    "The motivation behind STRATIQA is to make every business decision evidence-driven and "
    "explainable. By grounding all outputs in a company’s own data and exposing the reasoning "
    "behind them, the platform aims to give leaders not just a clearer view of their business, "
    "but a clear recommendation on what to do next — with the confidence and traceability needed "
    "to act."
)
h2("Scope of the Project")
para(
    "The scope of this project covers a complete, working Minimum Viable Product (MVP) spanning "
    "authentication and multi-tenant organization setup, business discovery and onboarding, the "
    "executive dashboard and war room, strategic goals and projects, an explainable "
    "recommendation engine, file-based data ingestion, reporting and executive briefs, and "
    "advanced intelligence layers including a Business Twin, a Knowledge Graph, and a layer of "
    "specialized AI agents."
)

# ===========================================================================
# 4. OBJECTIVES
# ===========================================================================
h1("Objectives")
para("The primary objectives of the STRATIQA project are as follows:")
for obj in [
    "To design and build a multi-tenant Business Operating System that delivers intelligence "
    "before analytics, prioritizing decisions over raw charts.",
    "To ground every insight in the organization’s own data, ensuring recommendations are "
    "specific to the business and never generic.",
    "To make all outputs explainable by attaching reasoning, expected impact, a confidence "
    "score, a risk level, and data sources to every recommendation.",
    "To onboard a new organization quickly through a Business Discovery interview that produces "
    "a Business DNA profile, a strategic Blueprint, and auto-tracked goals.",
    "To enable file-based data ingestion (CSV, Excel, PDF, Word) with smart column mapping so "
    "real business data continuously feeds the intelligence engines.",
    "To provide a layer of specialized AI agents orchestrated by a master agent (STRATIQA One) "
    "for domain-specific analysis.",
    "To add forward-looking capabilities through a Business Twin (scenario simulation) and a "
    "Knowledge Graph that reveals relationships across business entities.",
    "To proactively detect risks, anomalies, and KPI deterioration through an alerts and "
    "monitoring subsystem.",
    "To enforce security and isolation through JWT authentication, role-based access control, "
    "and strict per-organization data separation.",
    "To verify the system end-to-end through an automated test suite and deliver an "
    "executive-grade, production-quality user interface.",
]:
    numbered(obj)

# ===========================================================================
# 5. LITERATURE SURVEY
# ===========================================================================
h1("Literature Survey")
para(
    "A study of existing solutions and academic literature was carried out to position STRATIQA "
    "relative to current technology. The survey spanned four categories of systems: traditional "
    "BI platforms, spreadsheet-based analysis, general-purpose AI assistants, and emerging "
    "decision-intelligence research."
)
h2("Traditional Business Intelligence Platforms")
para(
    "Tools such as Power BI, Tableau, and Looker excel at data visualization and reporting. "
    "However, the literature consistently notes that these platforms are descriptive rather than "
    "prescriptive — they answer “what happened” but not “what should I do.” The interpretation "
    "and decision burden remains with the analyst, and there is no native grounding of "
    "recommendations in the organization’s strategic context."
)
h2("Spreadsheet-Based Analysis")
para(
    "Spreadsheets remain the most widely used analytical tool in business. Studies highlight "
    "their flexibility but also their well-documented weaknesses: error-proneness, lack of "
    "auditability, poor scalability, and the absence of any reasoning or recommendation layer. "
    "They are fundamentally manual and reactive."
)
h2("General-Purpose AI Assistants")
para(
    "Large Language Model (LLM) assistants such as ChatGPT and Gemini can generate fluent "
    "business advice, but research on LLM reliability emphasizes two limitations relevant here: "
    "(1) hallucination and lack of traceability, and (2) absence of grounding in an "
    "organization’s private, structured data. Without explicit grounding and explainability, "
    "their advice cannot be trusted for high-stakes decisions."
)
h2("Decision Intelligence & Explainable AI")
para(
    "Recent research in Decision Intelligence and Explainable AI (XAI) argues that for AI "
    "recommendations to be adopted in practice, they must be transparent, traceable to source "
    "data, and accompanied by a measure of confidence. STRATIQA operationalizes these findings "
    "by attaching reasoning, confidence, risk level, and data sources to every recommendation."
)
h2("Summary of Findings")
make_table(
    ["System Type", "Strength", "Key Limitation"],
    [
        ["BI Platforms", "Rich visualization & reporting", "Descriptive, not prescriptive"],
        ["Spreadsheets", "Flexible & ubiquitous", "Manual, error-prone, no reasoning"],
        ["LLM Assistants", "Natural-language fluency", "Ungrounded, black-box advice"],
        ["STRATIQA", "Grounded, explainable decisions", "Rule-based grounding in MVP"],
    ],
)

# ===========================================================================
# 6. EXISTING SYSTEM
# ===========================================================================
h1("Existing System")
para(
    "Today, founders, CEOs, and operations leaders rely on a fragmented mix of spreadsheets, "
    "traditional BI dashboards, and general-purpose AI chatbots to run their organizations. "
    "These tools share a common, fundamental limitation: they present information but do not "
    "produce decisions."
)
h2("Limitations of the Existing System")
for lead, rest in [
    ("Analytics without intelligence",
     " — Conventional BI tools display charts and raw metrics, then leave interpretation and "
     "decision-making entirely to the human."),
    ("Generic, black-box advice",
     " — Existing AI advisor products generate generic recommendations disconnected from a "
     "company’s actual situation, with no reasoning, confidence level, or traceability."),
    ("No grounding in the business",
     " — Generic chatbots have no model of the specific organization — its goals, projects, "
     "customers, products, and risks — so their answers are not anchored in the company’s real "
     "state."),
    ("Fragmented and manual",
     " — Data lives in disconnected silos; consolidating and interpreting it is slow, manual, "
     "and error-prone, leading to gut-driven decisions."),
    ("Reactive, not proactive",
     " — Existing systems rarely detect KPI deterioration, anomalies, or emerging risks early; "
     "problems are often noticed only after they become losses."),
    ("No continuous learning",
     " — There is no feedback loop to capture whether a recommendation was useful, so the "
     "systems never improve from outcomes."),
]:
    bold_lead_bullet(lead, rest)
para(
    "The net result is a paradox: organizations are drowning in dashboards yet starved of "
    "decisions, with analytics that inform but never act."
)

# ===========================================================================
# 7. PROPOSED SYSTEM
# ===========================================================================
h1("Proposed System")
para(
    "STRATIQA is an integrated operating system for strategic decision-making built on the "
    "principle of intelligence before analytics. At its center sits STRATIQA One, a master "
    "intelligence agent that orchestrates specialized domain agents across the business. A new "
    "organization is onboarded through a short Business Discovery interview that is transformed — "
    "using transparent, explainable logic — into a Business DNA profile, a strategic Blueprint, "
    "and a set of automatically tracked goals, so the platform is grounded in the company from "
    "day one."
)
h2("Key Features")
for lead, rest in [
    ("Business Discovery & DNA", " — A guided founder interview becomes an explainable Business "
     "Profile, DNA (growth stage, risk profile, complexity, market type), strategic blueprint, "
     "and auto-seeded goals, making a brand-new account immediately useful."),
    ("Explainable Recommendation Engine", " — Continuously analyzes goals, projects, risks, "
     "tasks, and KPIs to generate grounded recommendations, each carrying a title, reasoning, "
     "expected impact, confidence score, risk level, and data sources in a dedicated "
     "explainability panel."),
    ("File-Based Data Ingestion", " — Businesses upload existing files (CSV, Excel, PDF, Word); "
     "STRATIQA parses them deterministically, confirms a smart column mapping, and ingests rows "
     "into KPIs, customers, and products — instantly feeding the recommendation engine."),
    ("STRATIQA One & Specialized AI Agents", " — A master agent plus eight domain specialists "
     "(Finance, Sales, Project, Risk, Customer Success, Product, HR) translate raw signals into "
     "executive-level findings and answer per-agent questions."),
    ("Business Twin (Digital Twin)", " — Simulates strategic scenarios and what-if outcomes "
     "against the company’s modeled state to support forward-looking decisions."),
    ("Knowledge Graph", " — Connects entities (goals, projects, customers, products, risks) into "
     "a navigable, force-directed network that reveals relationships and clustered communities."),
    ("Customer & Product Intelligence", " — Surfaces account health, churn risk, support load, "
     "product performance, and inventory signals — each grounded in the underlying data."),
    ("Alerts & Monitoring", " — Detects KPI deterioration, anomalies, and high-severity risks "
     "early, escalating incidents before they become losses."),
    ("Reports & Executive Briefs", " — Generates board-ready reports and concise executive "
     "summaries automatically from live data."),
    ("Continuous Learning Loop", " — Captures user feedback (accept / dismiss / outcome) on "
     "every recommendation, building the foundation for confidence tuning and adaptive "
     "intelligence."),
]:
    bold_lead_bullet(lead, rest)
h2("Advantages over the Existing System")
for adv in [
    "Produces decisions and prioritized actions, not just charts.",
    "Every output is grounded in the organization’s own data.",
    "Full explainability: reasoning, confidence, risk level, and sources on every insight.",
    "Proactive risk and anomaly detection rather than reactive reporting.",
    "Strict multi-tenancy with per-organization data isolation and RBAC.",
    "A continuous feedback loop that lays the foundation for adaptive intelligence.",
]:
    bullet(adv)

# ===========================================================================
# 8. DESIGN
# ===========================================================================
h1("Design")
para(
    "STRATIQA is architected as a secure, modular monolith. The system is organized into three "
    "logical tiers — a presentation tier (frontend), an application/service tier (backend), and a "
    "data tier — with a clear separation of concerns and strict multi-tenancy enforced across "
    "every layer."
)
h2("System Architecture")
para(
    "The frontend communicates with the backend exclusively through a versioned REST API "
    "(/api/v1). Each request carries a JWT bearer token and an X-Organization-Id header, which "
    "the backend uses to authenticate the user and scope all queries to the correct tenant. The "
    "service layer contains the business logic and intelligence engines, which read from and "
    "write to the relational database. Background jobs and vector memory are handled by Celery "
    "and Qdrant respectively."
)
add_image(diagrams.ASSETS / "architecture.png", 6.2, "Figure 8.1 — Three-tier system architecture of STRATIQA")
h2("Database Design")
para(
    "The persistence layer follows a 55+ table relational schema organized into 16 functional "
    "sections. Every business entity carries an organization_id foreign key, enforcing "
    "multi-tenant isolation at the data level. The schema is dialect-portable: it targets "
    "PostgreSQL in production but runs on SQLite in development through portable column types."
)
add_image(diagrams.ASSETS / "schema.png", 6.0, "Figure 8.2 — Multi-tenant hub-and-spoke schema (Organization as tenant root)")
make_table(
    ["#", "Schema Section", "Representative Tables"],
    [
        ["1", "Identity & IAM", "users, roles, permissions, sessions"],
        ["2", "Organization Structure", "organizations, teams, members"],
        ["3", "Business Discovery", "discovery_responses, business_dna, blueprints"],
        ["4", "Strategic Goals", "goals, milestones, goal_progress"],
        ["5", "Project Intelligence", "projects, tasks, risks"],
        ["6", "AI Agents", "agents, agent_insights"],
        ["7", "Memory Layer", "memory_entries, embeddings"],
        ["8", "Knowledge Graph", "entities, relationships"],
        ["9", "Digital Twin", "twin_state, simulations"],
        ["10", "KPI & Analytics", "kpis, kpi_values, metrics"],
        ["11", "Recommendations & Learning", "recommendations, feedback"],
        ["12", "Customer Intelligence", "customers, health, tickets"],
        ["13", "Product Intelligence", "products, inventory, forecasts"],
        ["14", "Reporting", "reports, briefs"],
        ["15", "Alerts & Monitoring", "alerts, anomalies, incidents"],
        ["16", "Audit & Governance", "audit_logs"],
    ],
)
h2("Module Design")
para(
    "Each functional domain is implemented as a self-contained vertical slice comprising a "
    "database model, a deterministic service that produces an overview plus grounded, explainable "
    "signals, a REST API route, and a typed frontend page. This pattern keeps modules loosely "
    "coupled and independently testable."
)
h2("User Interface Design")
para(
    "The interface is dark-mode-first and optimized for executive decision-making. The visual "
    "language deliberately avoids gradients, neon, glow, and flashy animation in favor of a "
    "clean, professional aesthetic. The two signature surfaces are the STRATIQA One Home "
    "(welcome, today’s priorities, risks, opportunities, goals, projects, recommendations, "
    "executive brief) and the Executive War Room (critical risks, goals, projects, "
    "recommendations, business events, and twin insights)."
)

# ===========================================================================
# 9. METHODOLOGY
# ===========================================================================
h1("Methodology")
para(
    "The project followed an iterative, incremental development methodology. The system was built "
    "in a strict MVP build order, with each phase delivering a working, tested vertical slice "
    "before the next began. This ensured a continuously runnable system and early verification of "
    "every feature."
)
h2("Development Approach — Vertical Slices")
para(
    "Each feature was delivered end-to-end following a consistent pattern: seed data → a "
    "deterministic service producing an overview and grounded/explainable signals → an API route "
    "→ a typed frontend page with sidebar navigation → automated tests. This vertical-slice "
    "approach guaranteed that every module was demonstrable and verifiable on completion."
)
h2("MVP Build Order")
make_table(
    ["Phase", "Module", "Phase", "Module"],
    [
        ["1", "Authentication", "7", "STRATIQA One"],
        ["2", "Organization Setup", "8", "Reports"],
        ["3", "Business Discovery", "9", "Executive Briefs"],
        ["4", "Dashboard (One Home)", "10", "Business Twin"],
        ["5", "Projects", "11", "Knowledge Graph"],
        ["6", "Strategic Goals", "12", "Advanced AI Agents"],
    ],
)
para(
    "Subsequent post-MVP phases added Customer Intelligence, Product Intelligence, and Alerts & "
    "Monitoring, each following the same vertical-slice pattern."
)
h2("Grounding & Explainability Methodology")
para(
    "For the MVP, recommendations and simulations use transparent, rule-based logic rather than "
    "opaque models. This is a deliberate methodological choice: it guarantees that every output "
    "is deterministic, reproducible, and fully traceable to the data that produced it. Every "
    "recommendation is required to carry a title, reasoning, expected impact, confidence score, "
    "and risk level."
)
h2("Testing Methodology")
para(
    "Each module is accompanied by automated tests. Tests use a dedicated SQLite fixture database "
    "configured before application import, so the system is verifiable with no external "
    "infrastructure. Code quality is enforced with the Ruff linter, and the full suite is run on "
    "every change."
)

# ===========================================================================
# 10. TECHNOLOGIES
# ===========================================================================
h1("Technologies Used")
h2("Frontend")
for x in [
    "Next.js 15 (App Router) — React framework with server/client components",
    "TypeScript — type-safe application code",
    "Tailwind CSS + ShadCN UI — utility-first styling and component primitives",
    "Zustand — lightweight client-side state management",
    "React Hook Form + Zod — form handling and schema validation",
    "Apache ECharts — interactive data visualization and force-directed graphs",
    "Framer Motion — subtle, performant animation",
]:
    bullet(x)
h2("Backend")
for x in [
    "FastAPI — high-performance asynchronous Python web framework",
    "Python 3.12 — primary backend language",
    "Pydantic — data validation and settings management",
    "SQLAlchemy + Alembic — ORM and database migrations",
    "PostgreSQL — production relational database (SQLite for development)",
    "Redis — caching and task queue broker",
    "Celery — asynchronous background job processing",
    "Qdrant — vector database for AI memory and semantic search",
]:
    bullet(x)
h2("Artificial Intelligence")
bullet("Provider-agnostic LLM gateway (OpenAI / Gemini / Claude / local models)")
bullet("Transparent, rule-based grounding engine for deterministic MVP recommendations")
h2("Security")
bullet("JWT (JSON Web Tokens) — stateless authentication")
bullet("Role-Based Access Control (RBAC) — fine-grained authorization")
bullet("Per-organization data isolation — enforced multi-tenancy")
h2("Tooling & Quality")
for x in [
    "pytest — automated testing framework",
    "Ruff — fast Python linter and formatter",
    "Node.js + npm — frontend build and dependency management",
    "Git — version control",
]:
    bullet(x)

# ===========================================================================
# 11. RESULT ANALYSIS
# ===========================================================================
h1("Result Analysis")
para(
    "The STRATIQA MVP was implemented, integrated, and verified end-to-end. All planned build "
    "phases (1–12) plus three post-MVP intelligence modules were completed and are runnable "
    "locally with no external infrastructure. The following results summarize the delivered "
    "system."
)
h2("System Metrics")
make_table(
    ["Metric", "Value"],
    [
        ["Backend service modules", "16"],
        ["REST API route modules (/api/v1)", "16"],
        ["Database tables", "55+ (16 sections)"],
        ["Frontend application routes", "21"],
        ["Automated tests (passing)", "64"],
        ["Specialized AI agents", "8"],
        ["Linter status (Ruff)", "Clean"],
    ],
)
h2("Delivered Modules")
para("The following functional modules were delivered and verified:")
for x in [
    "Authentication, organization setup, and multi-tenant isolation",
    "Business Discovery onboarding producing Business DNA and a Blueprint",
    "STRATIQA One Home dashboard and Executive War Room",
    "Strategic Goals and Project Intelligence",
    "Explainable Recommendation Engine with feedback capture",
    "File-based data ingestion with smart column mapping",
    "Reports and Executive Briefs generation",
    "Business Twin, Knowledge Graph, and the 8-agent layer",
    "Customer Intelligence, Product Intelligence, and Alerts & Monitoring",
]:
    bullet(x)
h2("Functional Verification")
para(
    "End-to-end verification confirmed the intended new-user journey: a user registers via the "
    "signup page, completes the multi-step founder interview during onboarding, and lands on a "
    "populated dashboard. The discovery service persists the founder’s stated goals as tracked "
    "strategic goals and refreshes recommendations, so a brand-new organization is immediately "
    "non-empty and useful. A seeded demo organization (Northwind Robotics) provides grounded "
    "goals, projects, KPIs, risks, recommendations, customers, products, and alerts for "
    "demonstration."
)
h2("Discussion")
para(
    "The results validate the central thesis of the project: that analytics can be reframed "
    "around action. Because all recommendations are generated by transparent, rule-based logic "
    "over real organizational data, every output in the delivered system is explainable and "
    "traceable — directly addressing the black-box limitation of existing AI advisors. The "
    "vertical-slice methodology proved effective, keeping the system continuously runnable and "
    "fully tested throughout development."
)

# ===========================================================================
# 12. CONCLUSION
# ===========================================================================
h1("Conclusion")
para(
    "STRATIQA successfully demonstrates an AI-powered Business Operating System that closes the "
    "gap between data and decision. By grounding every output in a company’s own information and "
    "exposing the reasoning behind it, the platform turns scattered business data into "
    "trustworthy, explainable, and actionable strategic intelligence."
)
para(
    "The project delivered a complete, tested MVP spanning authentication, onboarding, an "
    "executive dashboard and war room, strategic goals and projects, an explainable "
    "recommendation engine, file-based data ingestion, reporting, and advanced intelligence "
    "layers including a Business Twin, a Knowledge Graph, and a set of specialized AI agents. The "
    "principle of intelligence before analytics is realized throughout: the system leads with "
    "decisions and surfaces supporting charts only afterward."
)
para(
    "In contrast to traditional BI tools that inform but never act, and generic AI assistants "
    "that advise without grounding or transparency, STRATIQA gives leaders not just a clearer "
    "view of their business, but a clear, defensible recommendation on what to do next."
)

# ===========================================================================
# 13. FUTURE ENHANCEMENTS
# ===========================================================================
h1("Future Enhancements")
para(
    "While the current system delivers a complete and verified MVP, several enhancements are "
    "planned to extend its intelligence and reach:"
)
for lead, rest in [
    ("LLM-powered reasoning",
     " — Move beyond rule-based grounding to integrate the provider-agnostic LLM gateway for "
     "richer natural-language reasoning, while preserving full traceability and explainability."),
    ("Adaptive confidence tuning",
     " — Use the continuous feedback loop (accept / dismiss / outcome) to automatically tune "
     "recommendation confidence and learn from real outcomes over time."),
    ("Live data integrations",
     " — Add direct connectors to accounting, CRM, and analytics platforms (e.g., QuickBooks, "
     "Salesforce, Google Analytics) to complement file-based ingestion."),
    ("Predictive analytics",
     " — Incorporate time-series forecasting and machine-learning models for demand, churn, and "
     "revenue prediction."),
    ("Advanced Business Twin",
     " — Extend the digital twin with probabilistic, multi-variable scenario modeling and "
     "Monte-Carlo simulation."),
    ("Mobile and collaboration",
     " — Deliver native mobile applications and multi-user collaborative decision workflows with "
     "notifications."),
    ("Expanded agent ecosystem",
     " — Add further domain agents (Legal, Marketing, Supply Chain) and inter-agent collaboration "
     "orchestrated by STRATIQA One."),
    ("Voice and conversational interface",
     " — Enable natural-language and voice queries over the Knowledge Graph and business state."),
]:
    bold_lead_bullet(lead, rest)

# ===========================================================================
# 14. REFERENCES
# ===========================================================================
h1("References")
refs = [
    "FastAPI Documentation. Sebastián Ramírez. https://fastapi.tiangolo.com/",
    "Next.js Documentation. Vercel Inc. https://nextjs.org/docs",
    "PostgreSQL Global Development Group. PostgreSQL Documentation. https://www.postgresql.org/docs/",
    "Apache ECharts. The Apache Software Foundation. https://echarts.apache.org/",
    "Qdrant Vector Database Documentation. https://qdrant.tech/documentation/",
    "Pydantic Documentation. https://docs.pydantic.dev/",
    "SQLAlchemy Documentation. https://docs.sqlalchemy.org/",
    "Tailwind CSS Documentation. https://tailwindcss.com/docs",
    "Celery: Distributed Task Queue Documentation. https://docs.celeryq.dev/",
    "Pramod J. Sadalage and Martin Fowler, “NoSQL Distilled,” Addison-Wesley, 2012.",
    "Christoph Molnar, “Interpretable Machine Learning,” 2nd ed., 2022.",
    "L. Cao, “Decision Intelligence: Human–AI Collaborative Decision Making,” IEEE Intelligent Systems, 2022.",
    "D. Gunning et al., “XAI—Explainable Artificial Intelligence,” Science Robotics, 2019.",
    "JSON Web Tokens (JWT) — RFC 7519. Internet Engineering Task Force.",
    "Martin Fowler, “Patterns of Enterprise Application Architecture,” Addison-Wesley, 2002.",
]
for i, ref in enumerate(refs, 1):
    doc.add_paragraph(f"[{i}]  {ref}")

# ===========================================================================
# FINALIZE — header/footer, field auto-update, save
# ===========================================================================
add_header_footer()
set_update_fields_on_open()
doc.save(OUT)
print(f"Saved: {OUT}")
