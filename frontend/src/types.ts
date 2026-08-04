export type HeatBand = "normal" | "elevated" | "severe" | "extreme";
export type HeatThresholdBand = Exclude<HeatBand, "normal">;
export type Exertion = "heavy" | "moderate";
export type Priority = "critical" | "high" | "planned";
export type SolverStatus =
  | "OPTIMAL"
  | "FEASIBLE"
  | "INFEASIBLE"
  | "UNKNOWN"
  | "MODEL_INVALID";
export type TimelineState = "work" | "recovery" | "travel" | "idle" | "unavailable";
export type StageName =
  | "critical_service"
  | "planned_service_value"
  | "travel_minutes"
  | "overtime_minutes"
  | "standalone_recovery";
export type PlanChange =
  | "unchanged"
  | "moved_time"
  | "moved_crew"
  | "recovery_added"
  | "served"
  | "deferred";
export type DiagnosisClassification =
  | "equivalent_alternative"
  | "feasible_with_cost"
  | "proven_infeasible"
  | "not_proven";
export type InterventionType = "deadline_extension" | "overtime_allowance";
export type ApiErrorCode =
  | "INVALID_SCENARIO"
  | "INVALID_POLICY"
  | "MODEL_INVALID"
  | "SOLVER_TIMEOUT"
  | "NO_FEASIBLE_PLAN"
  | "INTERNAL_ERROR";

export type Coordinate = [number, number];

export interface Crew {
  id: string;
  name: string;
  shift_start: string;
  shift_end: string;
  start_depot_id: string;
  end_depot_id: string;
  capabilities: string[];
  equipment: string[];
  max_overtime_minutes: number;
  recovery_profile: string;
}

export interface Job {
  id: string;
  name: string;
  location_id: string;
  active_minutes: number;
  exertion: Exertion;
  priority: Priority;
  service_value: number;
  window_start: string;
  window_end: string;
  required_capabilities: string[];
  required_equipment: string[];
  locked: boolean;
  locked_crew_id: string | null;
  locked_start: string | null;
}

export interface Location {
  id: string;
  coordinates: Coordinate;
  name: string | null;
}

export interface HeatSlot {
  slot: number;
  start: string;
  temperature_c: number;
  band: HeatBand;
}

export interface Scenario {
  id: string;
  date: string;
  slot_minutes: number;
  day_start: string;
  day_end: string;
  policy_id: string;
  crews: Crew[];
  jobs: Job[];
  locations: Location[];
  heat_series: HeatSlot[];
  travel_matrix_location_ids: string[];
  travel_matrix_minutes: number[][];
}

export interface PolicyRule {
  id: string;
  band: HeatBand;
  exertion: Exertion;
  max_active_slots: number;
  min_recovery_slots: number;
  stop_work: boolean;
}

export interface Policy {
  id: string;
  name: string;
  synthetic: boolean;
  disclaimer: string;
  band_thresholds_c: Record<HeatThresholdBand, number>;
  rolling_window_slots: number;
  eligible_recovery_profiles: string[];
  travel_counts_as_recovery: boolean;
  rules: PolicyRule[];
}

export interface SolveRequest {
  scenario: Scenario;
  policy: Policy;
  heat_adjustment_c: number;
  time_limit_seconds: number;
}

export interface DiagnoseRequest extends SolveRequest {
  job_id: string;
}

export interface Stage {
  name: StageName;
  status: SolverStatus;
  objective_value: number | null;
  best_bound: number | null;
  wall_time_seconds: number;
}

export interface Metrics {
  critical_jobs_scheduled: number;
  critical_jobs_total: number;
  planned_service_value: number;
  mandatory_policy_conflicts: number;
  travel_minutes: number;
  overtime_minutes: number;
  active_work_minutes: number;
  eligible_recovery_minutes: number;
}

export interface TimelineSegment {
  crew_id: string;
  state: TimelineState;
  job_id: string | null;
  start_slot: number;
  end_slot: number;
  start: string;
  end: string;
  exertion: Exertion | null;
  location_id: string | null;
  policy_rule_ids: string[];
}

export interface RouteSegment {
  crew_id: string;
  from_location_id: string;
  to_location_id: string;
  departure: string;
  arrival: string;
  travel_minutes: number;
  from_coordinates: Coordinate;
  to_coordinates: Coordinate;
}

export interface JobResult {
  job_id: string;
  served: boolean;
  crew_id: string | null;
  start: string | null;
  end: string | null;
  status_reason_code: string | null;
}

export interface Plan {
  label: string;
  status: SolverStatus;
  maximum_claim_allowed: boolean;
  wall_time_seconds: number;
  stages: Stage[];
  metrics: Metrics;
  timeline_segments: TimelineSegment[];
  route_segments: RouteSegment[];
  jobs: JobResult[];
}

export interface PlanJobState {
  crew_id: string | null;
  start: string | null;
  end: string | null;
}

export interface PlanDiff {
  job_id: string;
  change: PlanChange;
  before: PlanJobState | null;
  after: PlanJobState | null;
  binding_rule_ids: string[];
  explanation_code: string;
}

export interface SolveScenario {
  id: string;
  policy_id: string;
  policy_disclaimer: string;
  slot_minutes: number;
  heat_adjustment_c: number;
}

export interface PlanSet {
  service_first: Plan;
  policy_constrained: Plan;
  heat_shock: Plan | null;
}

export interface SolveResponse {
  scenario: SolveScenario;
  plans: PlanSet;
  plan_diff: PlanDiff[];
  diagnostics: Record<string, unknown>;
}

export interface ObjectiveDelta {
  critical_service: number;
  planned_service_value: number;
  travel_minutes: number;
  overtime_minutes: number;
}

export interface TestedIntervention {
  type: InterventionType;
  value_minutes: number;
  status: SolverStatus;
  objective_delta: ObjectiveDelta;
}

export interface DiagnosisResponse {
  job_id: string;
  classification: DiagnosisClassification;
  proof_status: SolverStatus;
  retained_commitments: string[];
  displaced_job_ids: string[];
  objective_delta: ObjectiveDelta;
  binding_rule_ids: string[];
  tested_interventions: TestedIntervention[];
}

export interface ApiErrorDetail {
  path: string;
  code: string;
  message: string;
}

export interface ApiError {
  code: ApiErrorCode;
  message: string;
  details: ApiErrorDetail[];
}

export interface SavedResultMetadata {
  fixture_version: string;
  generated_at: string;
  solver_version: string;
  sha256: string;
}

export interface DemoResponse {
  scenario: Scenario;
  policy: Policy;
  display_coordinates: Record<string, Coordinate>;
  saved_result_metadata: SavedResultMetadata | null;
}

export interface SavedManifest {
  fixture_version: string;
  generated_at: string;
  python_version: string;
  ortools_version: string;
  solver_seed: number;
  solver_workers: number;
  designated_diagnosis_job_id: string;
  canonical_hash_excluded_fields: string[];
  canonical_hash_format: string;
  input_hashes: Record<string, string>;
  output_hashes: Record<string, string>;
}

export interface DemoBundle {
  fixture_version: string;
  generated_at: string;
  scenario: Scenario;
  policy: Policy;
  base_solve: SolveResponse;
  heat_shock_solve: SolveResponse;
  diagnoses: Record<string, DiagnosisResponse>;
  manifest: SavedManifest;
}
