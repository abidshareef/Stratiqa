"""Draw the architecture and schema diagrams for the STRATIQA report using Pillow."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "_report_assets"
ASSETS.mkdir(exist_ok=True)

PRIMARY = (0x25, 0x63, 0xEB)
DARK = (0x11, 0x11, 0x11)
SLATE = (0x33, 0x41, 0x55)
LIGHT = (0xEF, 0xF3, 0xFB)
GREY = (0x88, 0x88, 0x88)
WHITE = (0xFF, 0xFF, 0xFF)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["arialbd.ttf", "Arialbd.ttf"] if bold else ["arial.ttf", "Arial.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_centered(draw, box, text, font, fill):
    x0, y0, x1, y1 = box
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2 - tb[1]), text, font=font, fill=fill)


def _round_box(draw, box, fill, outline, width=3, radius=14):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _arrow(draw, x, y0, y1, color):
    draw.line([(x, y0), (x, y1)], fill=color, width=4)
    draw.polygon([(x - 9, y1 - 12), (x + 9, y1 - 12), (x, y1)], fill=color)


# ---------------------------------------------------------------------------
# Architecture diagram (3-tier, top to bottom)
# ---------------------------------------------------------------------------
def architecture() -> Path:
    W, H = 1500, 1080
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    title_f = _font(34, bold=True)
    tier_f = _font(26, bold=True)
    body_f = _font(20)
    small_f = _font(17)

    _text_centered(d, (0, 20, W, 80), "STRATIQA — System Architecture", title_f, DARK)

    cx = W // 2
    bw = 1180
    x0 = cx - bw // 2
    x1 = cx + bw // 2

    tiers = [
        ("PRESENTATION TIER", "Next.js 15  •  TypeScript  •  Tailwind / ShadCN  •  ECharts  •  Zustand",
         "Executive dark-mode UI: One Home, War Room, Goals, Projects, Agents, Graph, Reports"),
        ("REST API  ( /api/v1 )", "FastAPI  •  JWT Bearer Auth  •  X-Organization-Id  •  RBAC",
         "16 route modules: auth, discovery, recommendations, agents, twin, knowledge-graph, ..."),
        ("SERVICE / INTELLIGENCE TIER", "Recommendation Engine • STRATIQA One • 8 AI Agents • Business Twin",
         "Knowledge Graph • Ingestion • Customer / Product Intelligence • Monitoring • Reports"),
        ("DATA TIER", "PostgreSQL (55+ tables, 16 sections)  •  Redis  •  Qdrant (vector memory)",
         "Strict multi-tenancy: every entity scoped by organization_id  •  Celery background jobs"),
    ]
    fills = [LIGHT, (0xDD, 0xE9, 0xFD), LIGHT, (0xDD, 0xE9, 0xFD)]

    top = 110
    th = 190
    gap = 60
    for i, (name, line2, line3) in enumerate(tiers):
        y0 = top + i * (th + gap)
        y1 = y0 + th
        _round_box(d, (x0, y0, x1, y1), fills[i], PRIMARY, width=3)
        _text_centered(d, (x0, y0 + 22, x1, y0 + 62), name, tier_f, PRIMARY)
        _text_centered(d, (x0, y0 + 78, x1, y0 + 112), line2, body_f, DARK)
        _text_centered(d, (x0, y0 + 124, x1, y0 + 160), line3, small_f, SLATE)
        if i < len(tiers) - 1:
            _arrow(d, cx, y1 + 6, y1 + gap - 6, SLATE)

    out = ASSETS / "architecture.png"
    img.save(out)
    return out


# ---------------------------------------------------------------------------
# Schema / ER diagram (hub-and-spoke multi-tenancy)
# ---------------------------------------------------------------------------
def schema() -> Path:
    import math

    W, H = 1500, 1180
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    title_f = _font(34, bold=True)
    hub_f = _font(28, bold=True)
    node_f = _font(19, bold=True)
    sub_f = _font(15)

    _text_centered(d, (0, 20, W, 80), "STRATIQA — Multi-Tenant Schema (Hub & Spoke)", title_f, DARK)

    cx, cy = W // 2, (H // 2) + 30
    # spokes
    nodes = [
        ("Users & IAM", "roles, sessions"),
        ("Strategic Goals", "milestones"),
        ("Projects", "tasks, risks"),
        ("Recommendations", "feedback"),
        ("AI Agents", "agent_insights"),
        ("Knowledge Graph", "entities, edges"),
        ("Business Twin", "simulations"),
        ("KPIs & Analytics", "kpi_values"),
        ("Customers", "health, tickets"),
        ("Products", "inventory, forecasts"),
        ("Alerts & Monitoring", "anomalies, incidents"),
        ("Reports & Briefs", "discovery, DNA"),
    ]
    n = len(nodes)
    R = 430
    nw, nh = 230, 92
    # draw spokes first (lines behind boxes)
    positions = []
    for i in range(n):
        ang = -math.pi / 2 + i * (2 * math.pi / n)
        nx = cx + int(R * math.cos(ang))
        ny = cy + int(R * 0.66 * math.sin(ang))
        positions.append((nx, ny))
        d.line([(cx, cy), (nx, ny)], fill=GREY, width=2)

    # hub
    hub_w, hub_h = 280, 120
    _round_box(d, (cx - hub_w // 2, cy - hub_h // 2, cx + hub_w // 2, cy + hub_h // 2),
               PRIMARY, PRIMARY, width=3, radius=18)
    _text_centered(d, (cx - hub_w // 2, cy - hub_h // 2 + 18, cx + hub_w // 2, cy - 6),
                   "ORGANIZATION", hub_f, WHITE)
    _text_centered(d, (cx - hub_w // 2, cy + 4, cx + hub_w // 2, cy + hub_h // 2 - 14),
                   "(tenant root)", sub_f, (0xDD, 0xE9, 0xFD))

    # nodes
    for (name, sub), (nx, ny) in zip(nodes, positions):
        box = (nx - nw // 2, ny - nh // 2, nx + nw // 2, ny + nh // 2)
        _round_box(d, box, LIGHT, PRIMARY, width=2, radius=12)
        _text_centered(d, (box[0], box[1] + 14, box[2], box[1] + 48), name, node_f, DARK)
        _text_centered(d, (box[0], box[1] + 50, box[2], box[3] - 8), sub, sub_f, SLATE)

    _text_centered(d, (0, H - 50, W, H - 18),
                   "Every entity carries organization_id  →  enforced per-tenant isolation",
                   sub_f, GREY)

    out = ASSETS / "schema.png"
    img.save(out)
    return out


if __name__ == "__main__":
    print("Saved:", architecture())
    print("Saved:", schema())
