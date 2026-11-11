/**
 * TypeScript mirrors of the backend Pydantic schemas (app/schemas).
 * Keep these in sync with the API contracts.
 */

export type Severity = "info" | "warning" | "danger";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface UserOut {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  mfa_enabled: boolean;
  last_login: string | null;
}

export interface OrganizationOut {
  id: string;
  name: string;
  industry: string | null;
  business_stage: string | null;
  country: string | null;
  timezone: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResult {
  user: UserOut;
  organization: OrganizationOut;
  tokens: TokenPair;
}

export interface GoalOut {
  id: string;
  title: string;
  description: string | null;
  goal_type: string | null;
  target_value: number | null;
  target_date: string | null;
  status: string;
}

export interface ProjectOut {
  id: string;
  name: string;
  description: string | null;
  budget: number | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
}

export interface RecommendationOut {
  id: string;
  title: string;
  description: string | null;
  reasoning: string | null;
  confidence_score: number;
  expected_impact: string | null;
  risk_level: string;
  data_sources: string | null;
  status: string;
  created_at: string;
}

export interface PriorityItem {
  title: string;
  detail: string;
  severity: Severity;
  source: string;
}

export interface RiskItem {
  title: string;
  level: string;
  context: string;
}

export interface OpportunityItem {
  title: string;
  estimated_impact: string | null;
  recommendation: string | null;
}

export interface ExecutiveHome {
  welcome: string;
  summary: string;
  todays_priorities: PriorityItem[];
  risks: RiskItem[];
  opportunities: OpportunityItem[];
  goals: GoalOut[];
  projects: ProjectOut[];
  recommendations: RecommendationOut[];
}

// --- Analytics ---------------------------------------------------------------

export interface KpiCard {
  key: string;
  label: string;
  value: number;
  unit: string;
  fmt: "currency" | "percent" | "number";
  delta_pct: number | null;
  direction: "up" | "down" | "flat";
  positive: boolean;
  series: number[];
}

export interface TimeSeries {
  labels: string[];
  values: number[];
}

export interface GoalProgressPoint {
  title: string;
  progress: number;
  target_date: string | null;
  status: string;
  series: number[];
}

export interface ProjectHealth {
  name: string;
  score: number;
  label: string;
  open_risks: number;
  overdue_tasks: number;
}

export interface AnalyticsOverview {
  kpis: KpiCard[];
  revenue_trend: TimeSeries;
  goal_progress: GoalProgressPoint[];
  project_health: ProjectHealth[];
  generated_at: string;
}

// --- War Room ---------------------------------------------------------------

export interface BusinessEvent {
  type: string;
  title: string;
  at: string | null;
}

export interface WarRoom {
  critical_risks: RiskItem[];
  goals: GoalOut[];
  projects: ProjectOut[];
  recommendations: RecommendationOut[];
  opportunities: OpportunityItem[];
  business_events: BusinessEvent[];
  twin_insights: string[];
}

// --- Ask --------------------------------------------------------------------

export interface AskResponse {
  answer: string;
  confidence_score: number;
  data_sources: string[];
  related_recommendations: RecommendationOut[];
}

// --- Projects (detail) ------------------------------------------------------

export interface TaskOut {
  id: string;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  due_date: string | null;
}

export interface MilestoneOut {
  id: string;
  title: string;
  due_date: string | null;
  status: string;
}

export interface ProjectRiskOut {
  id: string;
  risk_title: string;
  risk_level: string;
  impact: string | null;
  mitigation: string | null;
}

export interface ProjectHealthDetail {
  score: number;
  label: string;
  open_tasks: number;
  overdue_tasks: number;
  open_risks: number;
  drivers: string[];
}

export interface ProjectDetail extends ProjectOut {
  health: ProjectHealthDetail;
  tasks: TaskOut[];
  milestones: MilestoneOut[];
  risks: ProjectRiskOut[];
}

// --- Goals (detail) ---------------------------------------------------------

export interface GoalDetail extends GoalOut {
  latest_progress: number;
  completion_forecast: string | null;
  risk_indicator: string;
}

// --- Reports & Briefs -------------------------------------------------------

export interface ReportSummary {
  id: string;
  report_type: string;
  title: string | null;
  created_at: string;
}

export interface ReportOut extends ReportSummary {
  content: Record<string, unknown>;
}

export interface BriefOut {
  id: string;
  brief_type: string;
  content: Record<string, unknown>;
  generated_at: string;
}

// --- Business Twin ----------------------------------------------------------

export interface SimulationInput {
  scenario_name: string;
  scenario_description?: string | null;
  marketing_spend_change: number;
  hiring_change: number;
  price_change: number;
  market_expansion: number;
  new_product_launch: boolean;
}

export interface SimulationOutcome {
  revenue_impact: number;
  profit_impact: number;
  risk_impact: number;
  growth_impact: number;
  narrative: string;
  confidence_score: number;
}

export interface SimulationOut {
  id: string;
  scenario_name: string;
  scenario_description: string | null;
  inputs: Record<string, unknown>;
  created_at: string;
}

export interface SimulationResultOut {
  simulation: SimulationOut;
  outcome: SimulationOutcome;
}

// --- Business Discovery / Onboarding ----------------------------------------

export interface FounderInterview {
  industry: string;
  business_model: string;
  company_size: string;
  annual_revenue: number | null;
  employee_count: number | null;
  primary_goals: string[];
  main_challenges: string[];
  target_market: string | null;
}

export interface BusinessProfileOut {
  id: string;
  industry: string | null;
  business_model: string | null;
  company_size: string | null;
  annual_revenue: number | null;
  employee_count: number | null;
}

export interface BusinessDNAOut {
  id: string;
  growth_stage: string | null;
  risk_profile: string | null;
  operational_complexity: string | null;
  market_type: string | null;
  generated_at: string;
}

export interface BlueprintJson {
  industry: string | null;
  revenue_model: string | null;
  growth_profile: string;
  risk_profile: string;
  operational_complexity: string;
  market_type: string;
  stated_goals: string[];
  key_challenges: string[];
  recommended_focus_areas: string[];
  suggested_kpis: string[];
}

export interface BusinessBlueprintOut {
  id: string;
  blueprint_json: BlueprintJson;
  generated_at: string;
}

export interface DiscoveryResult {
  profile: BusinessProfileOut;
  dna: BusinessDNAOut;
  blueprint: BusinessBlueprintOut;
}

// --- Knowledge Graph --------------------------------------------------------

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  category: string;
  value: number | null;
  detail: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphOut {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: Record<string, number>;
  generated_at: string;
}

// --- Customer Intelligence --------------------------------------------------

export interface CustomerHealthOut {
  id: string;
  customer_name: string;
  segment: string | null;
  health_score: number | null;
  churn_risk: number | null;
  open_tickets: number;
  status: "healthy" | "watch" | "at_risk";
}

export interface CustomerStats {
  total_customers: number;
  avg_health_score: number | null;
  avg_churn_risk: number | null;
  at_risk_count: number;
  open_tickets: number;
}

export interface CustomerSignal {
  title: string;
  finding: string;
  severity: "info" | "warning" | "danger" | "success";
  confidence_score: number;
  data_sources: string[];
  recommended_action: string | null;
}

export interface CustomerOverview {
  stats: CustomerStats;
  customers: CustomerHealthOut[];
  signals: CustomerSignal[];
  generated_at: string;
}

// --- Product Intelligence ---------------------------------------------------

export interface ProductOut {
  id: string;
  product_name: string;
  category: string | null;
  sales_count: number;
  revenue: number | null;
  quantity: number;
  reorder_level: number;
  stock_status: "ok" | "low" | "out";
  demand_trend: "up" | "down" | "flat" | null;
}

export interface ProductStats {
  total_products: number;
  total_revenue: number;
  low_stock_count: number;
  top_product: string | null;
}

export interface ProductSignal {
  title: string;
  finding: string;
  severity: "info" | "warning" | "danger" | "success";
  confidence_score: number;
  data_sources: string[];
  recommended_action: string | null;
}

export interface ProductOverview {
  stats: ProductStats;
  products: ProductOut[];
  signals: ProductSignal[];
  generated_at: string;
}

// --- Alerts & Monitoring ----------------------------------------------------

export interface AlertItem {
  title: string;
  detail: string;
  severity: "info" | "warning" | "danger";
  category:
    | "risk"
    | "customer"
    | "inventory"
    | "kpi"
    | "goal"
    | "delivery"
    | "system";
  source: string;
  status: "open" | "resolved";
  at: string | null;
  derived: boolean;
}

export interface IncidentOut {
  id: string;
  incident_type: string;
  description: string | null;
  resolved: boolean;
}

export interface MonitoringStats {
  total_open: number;
  critical: number;
  warning: number;
  incidents_open: number;
  anomalies: number;
}

export interface MonitoringOverview {
  stats: MonitoringStats;
  alerts: AlertItem[];
  incidents: IncidentOut[];
  generated_at: string;
}

// --- AI Agents --------------------------------------------------------------

export interface AgentInsight {
  agent_type: string;
  title: string;
  finding: string;
  severity: "info" | "warning" | "danger" | "success";
  confidence_score: number;
  data_sources: string[];
  metric: string | null;
  recommended_action: string | null;
}

export interface AgentSummary {
  agent_type: string;
  name: string;
  domain: string;
  status: string;
  headline: string;
  insight_count: number;
  top_severity: string;
}

export interface AgentDetail {
  agent_type: string;
  name: string;
  domain: string;
  status: string;
  insights: AgentInsight[];
}

export interface AgentRoster {
  agents: AgentSummary[];
  generated_at: string;
}

export interface AgentAskResponse {
  agent_type: string;
  name: string;
  answer: string;
  confidence_score: number;
  data_sources: string[];
  insights: AgentInsight[];
}

// --- Data ingestion (file uploads) ------------------------------------------

export type IngestTarget = "kpi" | "customers" | "products";

export interface UploadOut {
  id: string;
  filename: string;
  file_kind: string;
  status: string;
  row_count: number;
  columns: string[];
  created_at: string;
}

export interface SuggestedMapping {
  target?: IngestTarget;
  fields?: Record<string, string>;
  kpi_label?: string | null;
}

export interface UploadDetail extends UploadOut {
  preview_rows: Record<string, unknown>[];
  extracted_text: string | null;
  suggested_mapping: SuggestedMapping;
  commit_summary: Record<string, number | string>;
  error: string | null;
}

export interface CommitMapping {
  target: IngestTarget;
  fields: Record<string, string>;
  kpi_label?: string | null;
}

export interface AnalysisChanges {
  new_insights: string[];
  resolved_insights: string[];
  unchanged: number;
}

export interface CommitResult {
  upload_id: string;
  target: string;
  created: Record<string, number>;
  skipped: number;
  total: number;
  recommendations_refreshed: number;
  analysis_changes: AnalysisChanges;
}

// --- Audit & Governance (Section 16) ---

export interface AuditEntry {
  id: string;
  action: string;
  category: "security" | "data" | "other";
  actor: string;
  resource: string | null;
  detail: string | null;
  ip_address: string | null;
  at: string | null;
}

export interface GovernanceStats {
  total_events: number;
  security_events: number;
  failed_logins: number;
  data_events: number;
}

export interface DecisionGovernance {
  total_decisions: number;
  with_reasoning: number;
  with_confidence: number;
  with_data_sources: number;
  explainability_coverage: number;
  avg_confidence: number;
}

export interface GovernanceOverview {
  stats: GovernanceStats;
  decisions: DecisionGovernance;
  trail: AuditEntry[];
  generated_at: string;
}
