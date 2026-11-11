"""Seed the database with a demo organization and realistic data.

Run with:  python -m app.scripts.seed

Creates tables if missing (dev convenience), then a demo founder account so the
executive surfaces (STRATIQA One Home, War Room, reports, briefs) have grounded
data to reason over. Idempotent: re-running won't duplicate the demo org.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.analytics import KPI, Anomaly, Opportunity
from app.models.customers import Customer, CustomerHealth, CustomerInsight, SupportTicket
from app.models.goals import GoalProgress, StrategicGoal
from app.models.identity import Organization, OrganizationUser, Role, User
from app.models.monitoring import Alert, Incident
from app.models.products import DemandForecast, Inventory, Product, ProductMetric
from app.models.projects import Milestone, Project, ProjectRisk, Task
from app.schemas.discovery import FounderInterview
from app.services import (
    agents,
    brief_generator,
    discovery_service,
    knowledge_graph,
    recommendation_engine,
    report_generator,
)

DEMO_EMAIL = "founder@stratiqa.dev"
DEMO_PASSWORD = "stratiqa123"  # demo only — never a real credential


def _ensure_roles(db) -> dict[str, Role]:
    roles = {}
    for name in ["Owner", "CEO", "Manager", "Analyst", "Employee"]:
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, description=f"{name} role")
            db.add(role)
            db.flush()
        roles[name] = role
    return roles


def seed() -> None:
    print("Creating tables (if not present)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == DEMO_EMAIL)):
            print(f"Demo user {DEMO_EMAIL} already exists — skipping.")
            return

        roles = _ensure_roles(db)

        user = User(
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Avery Founder",
        )
        db.add(user)
        db.flush()

        org = Organization(
            name="Northwind Robotics",
            industry="Manufacturing",
            business_stage="growth",
            country="US",
            timezone="America/New_York",
            created_by=user.id,
        )
        db.add(org)
        db.flush()

        db.add(
            OrganizationUser(
                organization_id=org.id, user_id=user.id, role_id=roles["Owner"].id
            )
        )

        # --- Strategic goals ---
        g1 = StrategicGoal(
            organization_id=org.id,
            title="Reach $5M ARR",
            description="Grow annual recurring revenue to $5M.",
            goal_type="revenue",
            target_value=5_000_000,
            target_date=date.today() + timedelta(days=45),
            status="active",
        )
        g2 = StrategicGoal(
            organization_id=org.id,
            title="Launch EU market",
            description="Establish operations in the EU.",
            goal_type="expansion",
            target_value=1,
            target_date=date.today() + timedelta(days=120),
            status="active",
        )
        db.add_all([g1, g2])
        db.flush()

        # Progress trend over the last 6 months (oldest -> newest).
        def _progress(goal_id, points: list[float]) -> None:
            n = len(points)
            for i, pct in enumerate(points):
                db.add(
                    GoalProgress(
                        goal_id=goal_id,
                        progress_percentage=pct,
                        recorded_at=datetime.utcnow() - timedelta(days=30 * (n - 1 - i)),
                    )
                )

        _progress(g1.id, [8, 14, 19, 24, 28, 32])  # behind -> triggers rec
        _progress(g2.id, [20, 30, 42, 50, 56, 60])

        # --- Project with overdue tasks + high risk ---
        proj = Project(
            organization_id=org.id,
            name="Assembly Line Automation",
            description="Automate the primary assembly line.",
            owner_id=user.id,
            budget=750_000,
            status="active",
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=30),
        )
        db.add(proj)
        db.flush()

        db.add(
            Milestone(
                project_id=proj.id,
                title="Phase 1: Sensors",
                due_date=date.today() - timedelta(days=5),
                status="pending",
            )
        )
        for i in range(4):  # 4 overdue tasks -> triggers re-sequence rec
            db.add(
                Task(
                    project_id=proj.id,
                    title=f"Integrate robotic arm #{i + 1}",
                    assigned_to=user.id,
                    priority="high",
                    status="in_progress",
                    due_date=date.today() - timedelta(days=3 + i),
                )
            )
        db.add(
            Task(
                project_id=proj.id,
                title="Safety review",
                priority="high",
                status="todo",
                due_date=date.today(),
            )
        )
        db.add(
            ProjectRisk(
                project_id=proj.id,
                risk_title="Supplier delay on servo motors",
                risk_level="critical",
                impact="Could delay launch by 6 weeks.",
                mitigation=None,
            )
        )

        # --- KPIs: 12 months of history (oldest -> newest) so the dashboard
        # charts have real shape. Monthly Revenue dips at the end (470 -> 420
        # -> 355), which trips the KPI-decline recommendation. ---
        kpi_series: dict[str, list[float]] = {
            "Monthly Revenue": [300_000, 322_000, 348_000, 360_000, 375_000, 392_000,
                                405_000, 428_000, 452_000, 470_000, 420_000, 355_000],
            "MRR": [120_000, 128_000, 135_000, 142_000, 150_000, 158_000,
                    165_000, 172_000, 180_000, 188_000, 196_000, 205_000],
            "Gross Margin": [52, 53, 54, 55, 56, 57, 58, 59, 59, 60, 59, 58],
            "Active Customers": [98, 104, 110, 116, 121, 127, 131, 135, 138, 141, 142, 144],
            "Net Burn": [210_000, 205_000, 198_000, 190_000, 185_000, 180_000,
                         176_000, 170_000, 168_000, 165_000, 162_000, 158_000],
            "Cash Runway": [9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14],
            "NPS": [31, 33, 34, 36, 38, 39, 41, 42, 44, 45, 46, 48],
            "CAC": [1_400, 1_380, 1_350, 1_320, 1_300, 1_280,
                    1_260, 1_240, 1_220, 1_200, 1_180, 1_160],
        }
        for name, values in kpi_series.items():
            n = len(values)
            for i, val in enumerate(values):
                db.add(
                    KPI(
                        organization_id=org.id,
                        kpi_name=name,
                        value=val,
                        recorded_at=datetime.utcnow() - timedelta(days=30 * (n - 1 - i)),
                    )
                )

        # --- Two more projects for a varied project-health picture ---
        proj_eu = Project(
            organization_id=org.id,
            name="EU Compliance Readiness",
            description="CE marking and GDPR readiness for the EU launch.",
            owner_id=user.id,
            budget=180_000,
            status="active",
            start_date=date.today() - timedelta(days=40),
            end_date=date.today() + timedelta(days=80),
        )
        proj_portal = Project(
            organization_id=org.id,
            name="Customer Portal v2",
            description="Self-service portal for fleet telemetry and support.",
            owner_id=user.id,
            budget=240_000,
            status="active",
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() + timedelta(days=100),
        )
        db.add_all([proj_eu, proj_portal])
        db.flush()

        # EU project: one high risk + one overdue task -> "at_risk".
        db.add(
            ProjectRisk(
                project_id=proj_eu.id,
                risk_title="Notified-body audit slot not yet confirmed",
                risk_level="high",
                impact="Could push CE certification past the launch window.",
                mitigation="Escalate scheduling with two backup bodies.",
            )
        )
        db.add(
            Task(
                project_id=proj_eu.id,
                title="Submit technical documentation package",
                assigned_to=user.id,
                priority="high",
                status="in_progress",
                due_date=date.today() - timedelta(days=2),
            )
        )
        # Portal project: on track -> "healthy".
        for i in range(3):
            db.add(
                Task(
                    project_id=proj_portal.id,
                    title=f"Build portal module #{i + 1}",
                    assigned_to=user.id,
                    priority="medium",
                    status="in_progress",
                    due_date=date.today() + timedelta(days=10 + i * 7),
                )
            )

        # --- Opportunities ---
        db.add_all(
            [
                Opportunity(
                    organization_id=org.id,
                    title="Upsell maintenance contracts to top 20 accounts",
                    estimated_impact="+$180K ARR",
                    recommendation="Bundle predictive maintenance with existing hardware deals.",
                ),
                Opportunity(
                    organization_id=org.id,
                    title="Expand into EU mid-market manufacturers",
                    estimated_impact="+$1.2M TAM",
                    recommendation=(
                        "Prioritize Germany and Benelux where automation demand is highest."
                    ),
                ),
            ]
        )

        # --- Customer base: health, churn risk, support, and insights ---
        # A varied book of business so retention intelligence has real signal:
        # two clearly at-risk accounts (churn >= 60) plus healthy anchors.
        customer_specs = [
            ("Atlas Manufacturing", "Enterprise", 42, 72, 3),
            ("Meridian Logistics", "Enterprise", 55, 64, 2),
            ("Cobalt Devices", "Mid-Market", 68, 38, 1),
            ("Northstar Foods", "Mid-Market", 81, 18, 0),
            ("Pioneer Aerospace", "Enterprise", 88, 12, 0),
            ("Vertex Tooling", "SMB", 76, 22, 0),
        ]
        for name, segment, health, churn, open_tickets in customer_specs:
            cust = Customer(
                organization_id=org.id, customer_name=name, segment=segment
            )
            db.add(cust)
            db.flush()
            db.add(
                CustomerHealth(
                    customer_id=cust.id, health_score=health, churn_risk=churn
                )
            )
            for t in range(open_tickets):
                db.add(
                    SupportTicket(
                        customer_id=cust.id,
                        title=f"Escalation #{t + 1} from {name}",
                        status="open",
                        priority="high" if churn >= 60 else "medium",
                    )
                )
            if churn >= 60:
                db.add(
                    CustomerInsight(
                        customer_id=cust.id,
                        insight=(
                            f"{name} shows churn risk {churn}% with "
                            f"{open_tickets} open ticket(s) — schedule an executive review."
                        ),
                    )
                )

        # --- Product line: catalog, inventory, sales, demand forecasts ---
        # A robotics manufacturer's line: two SKUs run low (trips stockout
        # signal), the robotic arm dominates revenue (concentration signal).
        # (name, category, sales, revenue, qty, reorder, demand trend)
        product_specs = [
            ("Robotic Arm RA-7", "Assemblies", 85, 1_275_000, 12, 5, "up"),
            ("Servo Motor X1", "Components", 1_200, 480_000, 40, 50, "up"),
            ("Vision Sensor V2", "Components", 640, 320_000, 8, 20, "flat"),
            ("Controller Unit C9", "Electronics", 310, 217_000, 90, 30, "down"),
            ("Maintenance Kit MK-1", "Service", 540, 162_000, 200, 50, "up"),
        ]
        for name, category, sales, revenue, qty, reorder, trend in product_specs:
            prod = Product(
                organization_id=org.id, product_name=name, category=category
            )
            db.add(prod)
            db.flush()
            db.add(Inventory(product_id=prod.id, quantity=qty, reorder_level=reorder))
            db.add(
                ProductMetric(
                    product_id=prod.id, sales_count=sales, revenue=revenue
                )
            )
            db.add(
                DemandForecast(
                    product_id=prod.id,
                    forecast_data={
                        "trend": trend,
                        "next_30d_units": int(sales / 12),
                        "basis": "trailing 12-month sales",
                    },
                )
            )

        # --- Monitoring: persisted system alerts, anomalies, incidents ---
        # These sit alongside the alerts the monitoring service derives live
        # from business data (risks, churn, stock, KPIs, goals).
        db.add_all(
            [
                Alert(
                    organization_id=org.id,
                    title="Database CPU sustained above 85%",
                    severity="warning",
                    status="open",
                ),
                Alert(
                    organization_id=org.id,
                    title="Nightly analytics ETL completed",
                    severity="info",
                    status="resolved",
                ),
            ]
        )
        db.add(
            Anomaly(
                organization_id=org.id,
                anomaly_type="revenue_dip",
                severity="high",
                description="Monthly revenue fell ~15% MoM — outside normal variance.",
            )
        )
        db.add_all(
            [
                Incident(
                    organization_id=org.id,
                    incident_type="service_degradation",
                    description="Customer portal latency spike during peak hours.",
                    resolved=False,
                ),
                Incident(
                    organization_id=org.id,
                    incident_type="failed_deployment",
                    description="Rolled back v2.3 release after a migration error.",
                    resolved=True,
                ),
            ]
        )

        db.flush()

        # Run Business Discovery so the demo org has a Business DNA + Blueprint
        # (the goal titles match the seeded goals above, so no duplicates).
        discovery_service.run_discovery(
            db,
            org.id,
            FounderInterview(
                industry="Manufacturing",
                business_model="Hardware + maintenance contracts",
                company_size="51-200",
                annual_revenue=4_200_000,
                employee_count=120,
                primary_goals=["Reach $5M ARR", "Launch EU market"],
                main_challenges=[
                    "Supplier delays on critical components",
                    "EU regulatory readiness",
                    "Hiring automation engineers",
                ],
                target_market="B2B enterprise manufacturers",
            ),
        )

        # Generate grounded recommendations from the seeded data.
        recs = recommendation_engine.refresh_recommendations(db, org.id)

        # Pre-generate executive collateral so the Reports and Briefs surfaces
        # are populated out of the box (otherwise a fresh demo lands on empty
        # lists). All grounded in the seeded data above.
        for report_type in ("executive", "weekly"):
            report_generator.generate(db, org.id, report_type, generated_by=user.id)
        for brief_type in ("morning", "evening"):
            brief_generator.generate(db, org.id, brief_type)

        # Register the specialist agent roster and materialize the knowledge graph
        # (knowledge graph is built last so it captures the recommendations too).
        agents.ensure_agents(db, org.id)
        knowledge_graph.rebuild_graph(db, org.id)

        db.commit()
        print("Seed complete.")
        print(f"  Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  Organization: {org.name} ({org.id})")
        print(f"  Recommendations generated: {len(recs)}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
