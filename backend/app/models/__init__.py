"""All ORM models. Importing this package registers every table on Base.metadata
(required for Alembic autogenerate and metadata.create_all)."""

from app.models.agents import Agent, AgentInteraction, AgentTask
from app.models.analytics import KPI, Anomaly, Forecast, Opportunity
from app.models.customers import (
    Customer,
    CustomerHealth,
    CustomerInsight,
    SupportTicket,
)
from app.models.discovery import BusinessBlueprint, BusinessDNA, BusinessProfile
from app.models.goals import GoalMetric, GoalProgress, StrategicGoal
from app.models.governance import ApiKey, AuditLog, GovernanceRecord
from app.models.identity import (
    Organization,
    OrganizationUser,
    Permission,
    Role,
    RolePermission,
    Session,
    User,
)
from app.models.knowledge_graph import Entity, GraphEvent, Relationship
from app.models.memory import (
    AgentMemory,
    DecisionMemory,
    OrganizationMemory,
    ProjectMemory,
    UserMemory,
)
from app.models.monitoring import Alert, FailureEvent, Incident, RootCauseAnalysis
from app.models.org_structure import Department, Team, TeamMember
from app.models.products import DemandForecast, Inventory, Product, ProductMetric
from app.models.projects import (
    Milestone,
    Project,
    ProjectRisk,
    Task,
    TaskDependency,
)
from app.models.recommendations import (
    LearningEvent,
    OutcomeTracking,
    Recommendation,
    RecommendationFeedback,
)
from app.models.reporting import ExecutiveBrief, Report, ReportAsset
from app.models.twin import Simulation, SimulationResult, TwinModel, TwinSnapshot

__all__ = [
    "Agent", "AgentInteraction", "AgentTask",
    "KPI", "Anomaly", "Forecast", "Opportunity",
    "Customer", "CustomerHealth", "CustomerInsight", "SupportTicket",
    "BusinessBlueprint", "BusinessDNA", "BusinessProfile",
    "GoalMetric", "GoalProgress", "StrategicGoal",
    "ApiKey", "AuditLog", "GovernanceRecord",
    "Organization", "OrganizationUser", "Permission", "Role",
    "RolePermission", "Session", "User",
    "Entity", "GraphEvent", "Relationship",
    "AgentMemory", "DecisionMemory", "OrganizationMemory",
    "ProjectMemory", "UserMemory",
    "Alert", "FailureEvent", "Incident", "RootCauseAnalysis",
    "Department", "Team", "TeamMember",
    "DemandForecast", "Inventory", "Product", "ProductMetric",
    "Milestone", "Project", "ProjectRisk", "Task", "TaskDependency",
    "LearningEvent", "OutcomeTracking", "Recommendation", "RecommendationFeedback",
    "ExecutiveBrief", "Report", "ReportAsset",
    "Simulation", "SimulationResult", "TwinModel", "TwinSnapshot",
]
