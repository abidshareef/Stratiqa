# STRATIQA

**Strategic Intelligence & Analytics Platform** — an AI-Powered Business Operating System.

STRATIQA is not a dashboard, BI tool, or chatbot. It is an executive intelligence platform that understands a business, monitors operations, predicts risk, and recommends strategic action. The centerpiece is **STRATIQA One**, the master orchestration agent.

## Architecture

Modular monolith, multi-tenant. Every entity belongs to an organization.

```
stratiqa/
├── backend/     FastAPI · Python 3.12 · PostgreSQL · Redis · Qdrant · Celery
├── frontend/    Next.js 15 · TypeScript · Tailwind · ShadCN UI · Zustand · ECharts
└── infra/       docker-compose for Postgres / Redis / Qdrant
```

## Tech stack

| Layer        | Technology |
|--------------|------------|
| Frontend     | Next.js 15, TypeScript, Tailwind CSS, ShadCN UI, Zustand, React Hook Form, Zod, Apache ECharts, Framer Motion |
| Backend      | FastAPI, Python 3.12, Pydantic, SQLAlchemy 2.0, Alembic, Celery |
| Data         | PostgreSQL (primary), Redis (cache/queue), Qdrant (vector memory) |
| Auth         | JWT + refresh tokens, RBAC, MFA-ready, audit logging |
| AI           | Provider-agnostic LLM gateway (OpenAI / Gemini / Claude / local) |

## Design system

Dark mode first. No gradients, neon, glow, or flashy animation.

| Token   | Value     |  | Token    | Value     |
|---------|-----------|--|----------|-----------|
| bg      | `#0A0A0A` |  | primary  | `#2563EB` |
| surface | `#111111` |  | success  | `#10B981` |
| card    | `#171717` |  | warning  | `#F59E0B` |
| border  | `#262626` |  | danger   | `#EF4444` |
|         |           |  | info     | `#38BDF8` |

Fonts: Geist (primary), Inter (secondary), JetBrains Mono (metrics).

## Getting started

### Infrastructure
```bash
cd infra && docker compose up -d        # Postgres, Redis, Qdrant
```

### Backend
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env                   # then edit secrets
alembic upgrade head
python -m app.scripts.seed               # demo org + data
uvicorn app.main:app --reload
```
API docs at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```
App at http://localhost:3000

## MVP scope (build order)

1. Authentication → 2. Organization setup → 3. Business Discovery → 4. Dashboard (STRATIQA One Home) → 5. Projects → 6. Goals → 7. STRATIQA One → 8. Reports → 9. Executive Briefs → *(then)* Business Twin, Knowledge Graph, advanced agents.
