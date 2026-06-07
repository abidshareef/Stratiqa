"""Knowledge Graph Engine.

Materializes the organization's real operating data (goals, projects, risks,
KPIs, customers, opportunities, recommendations, business DNA) into a graph of
``Entity`` + ``Relationship`` rows, then serves it as nodes/edges for the
executive graph view. Cross-links are grounded — e.g. a recommendation is linked
to the exact project its ``data_sources`` reference, so the graph explains *why*
nodes connect, never decoration.
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI, Opportunity
from app.models.customers import Customer
from app.models.discovery import BusinessDNA
from app.models.goals import StrategicGoal
from app.models.identity import Organization
from app.models.knowledge_graph import Entity, GraphEvent, Relationship
from app.models.projects import Project, ProjectRisk
from app.models.recommendations import Recommendation
from app.schemas.knowledge_graph import GraphEdge, GraphNode, GraphOut

_RISK_VALUE = {"critical": 22.0, "high": 16.0, "medium": 12.0, "low": 9.0}


def _clear(db: DBSession, org_id: uuid.UUID) -> None:
    ids = list(db.scalars(select(Entity.id).where(Entity.organization_id == org_id)).all())
    if not ids:
        return
    db.execute(delete(GraphEvent).where(GraphEvent.entity_id.in_(ids)))
    db.execute(
        delete(Relationship).where(
            or_(Relationship.source_entity.in_(ids), Relationship.target_entity.in_(ids))
        )
    )
    db.execute(delete(Entity).where(Entity.id.in_(ids)))


def rebuild_graph(db: DBSession, org_id: uuid.UUID) -> GraphOut:
    """Drop and re-materialize the org's knowledge graph from current data."""
    _clear(db, org_id)
    org = db.get(Organization, org_id)

    nodes: dict[str, Entity] = {}

    def add(key: str, etype: str, name: str, category: str, value: float, detail: str) -> None:
        entity = Entity(
            organization_id=org_id,
            entity_type=etype,
            entity_name=name,
            entity_metadata={"category": category, "value": value, "detail": detail},
        )
        db.add(entity)
        nodes[key] = entity

    add("org", "organization", org.name if org else "Organization", "organization", 46,
        (org.industry or "Organization") if org else "Organization")

    dna = db.scalar(select(BusinessDNA).where(BusinessDNA.organization_id == org_id))
    if dna:
        add("dna", "business_dna", f"DNA · {dna.growth_stage or 'profile'}", "dna", 18,
            f"{dna.growth_stage} · {dna.risk_profile} risk · {dna.market_type}")

    for g in db.scalars(
        select(StrategicGoal).where(StrategicGoal.organization_id == org_id)
    ).all():
        add(f"goal:{g.id}", "goal", g.title, "goal", 22,
            f"{g.goal_type or 'strategic'} · {g.status}")

    projects = list(
        db.scalars(select(Project).where(Project.organization_id == org_id)).all()
    )
    for p in projects:
        add(f"project:{p.id}", "project", p.name, "project", 26, f"status: {p.status}")
        for r in db.scalars(
            select(ProjectRisk).where(ProjectRisk.project_id == p.id)
        ).all():
            add(f"risk:{r.id}", "risk", r.risk_title, "risk",
                _RISK_VALUE.get(r.risk_level, 12.0), f"{r.risk_level} risk · {p.name}")

    for name in db.scalars(
        select(KPI.kpi_name).where(KPI.organization_id == org_id).distinct()
    ).all():
        latest = db.scalar(
            select(KPI)
            .where(KPI.organization_id == org_id, KPI.kpi_name == name)
            .order_by(KPI.recorded_at.desc())
        )
        val = f"{float(latest.value):,.0f}" if latest and latest.value is not None else "—"
        add(f"kpi:{name}", "kpi", name, "kpi", 14, f"latest: {val}")

    for c in db.scalars(select(Customer).where(Customer.organization_id == org_id)).all():
        add(f"customer:{c.id}", "customer", c.customer_name, "customer", 12,
            c.segment or "customer")

    for o in db.scalars(
        select(Opportunity).where(Opportunity.organization_id == org_id)
    ).all():
        add(f"opp:{o.id}", "opportunity", o.title, "opportunity", 16,
            o.estimated_impact or "opportunity")

    recs = list(
        db.scalars(
            select(Recommendation).where(
                Recommendation.organization_id == org_id,
                Recommendation.status == "pending",
            )
        ).all()
    )
    for rec in recs:
        add(f"rec:{rec.id}", "recommendation", rec.title, "recommendation", 18,
            f"{rec.risk_level} · {float(rec.confidence_score):.0f}% confidence")

    db.flush()  # assign entity ids

    rels: list[Relationship] = []

    def link(src: str, tgt: str, rtype: str) -> None:
        s, t = nodes.get(src), nodes.get(tgt)
        if s is not None and t is not None:
            rels.append(
                Relationship(source_entity=s.id, target_entity=t.id, relationship_type=rtype)
            )

    if "dna" in nodes:
        link("org", "dna", "characterized_by")
    for g in db.scalars(
        select(StrategicGoal).where(StrategicGoal.organization_id == org_id)
    ).all():
        link("org", f"goal:{g.id}", "pursues")
    for p in projects:
        link("org", f"project:{p.id}", "runs")
        for r in db.scalars(
            select(ProjectRisk).where(ProjectRisk.project_id == p.id)
        ).all():
            link(f"project:{p.id}", f"risk:{r.id}", "faces")
    for name in nodes:
        if name.startswith("kpi:"):
            link("org", name, "measures")
        elif name.startswith("customer:"):
            link("org", name, "serves")
        elif name.startswith("opp:"):
            link("org", name, "sees")
    for rec in recs:
        link("org", f"rec:{rec.id}", "advises")
        # Grounded cross-link: connect the recommendation to the project it cites.
        sources = rec.data_sources or ""
        for p in projects:
            if str(p.id) in sources:
                link(f"rec:{rec.id}", f"project:{p.id}", "addresses")

    db.add_all(rels)
    db.flush()
    return get_graph(db, org_id)


def get_graph(db: DBSession, org_id: uuid.UUID, *, build_if_empty: bool = False) -> GraphOut:
    entities = list(
        db.scalars(select(Entity).where(Entity.organization_id == org_id)).all()
    )
    if not entities and build_if_empty:
        return rebuild_graph(db, org_id)

    ids = {e.id for e in entities}
    nodes = [
        GraphNode(
            id=str(e.id),
            label=e.entity_name,
            type=e.entity_type,
            category=(e.entity_metadata or {}).get("category", e.entity_type),
            value=(e.entity_metadata or {}).get("value"),
            detail=(e.entity_metadata or {}).get("detail"),
        )
        for e in entities
    ]
    edges: list[GraphEdge] = []
    if ids:
        for r in db.scalars(
            select(Relationship).where(Relationship.source_entity.in_(ids))
        ).all():
            if r.target_entity in ids:
                edges.append(
                    GraphEdge(
                        source=str(r.source_entity),
                        target=str(r.target_entity),
                        type=r.relationship_type,
                    )
                )
    stats = Counter(n.category for n in nodes)
    return GraphOut(
        nodes=nodes,
        edges=edges,
        stats=dict(stats),
        generated_at=datetime.utcnow(),
    )
