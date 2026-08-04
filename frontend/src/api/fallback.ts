import type {
  Coordinate,
  DemoResponse,
  DiagnoseRequest,
  DiagnosisResponse,
  DemoBundle,
  HeatBand,
  Exertion,
  Priority,
  Plan,
  PlanChange,
  Policy,
  SavedManifest,
  SavedResultMetadata,
  Scenario,
  SolveResponse,
  SolveRequest,
  SolverStatus,
  StageName,
  TimelineState,
} from "../types";

const SOLVER_STATUSES = new Set<SolverStatus>([
  "OPTIMAL",
  "FEASIBLE",
  "INFEASIBLE",
  "UNKNOWN",
  "MODEL_INVALID",
]);
const HEAT_BANDS = new Set<HeatBand>(["normal", "elevated", "severe", "extreme"]);
const PLAN_CHANGES = new Set<PlanChange>([
  "unchanged",
  "moved_time",
  "moved_crew",
  "recovery_added",
  "served",
  "deferred",
]);
const EXERTIONS = new Set<Exertion>(["heavy", "moderate"]);
const PRIORITIES = new Set<Priority>(["critical", "high", "planned"]);
const STAGE_NAMES = new Set<StageName>([
  "critical_service",
  "planned_service_value",
  "travel_minutes",
  "overtime_minutes",
  "standalone_recovery",
]);
const TIMELINE_STATES = new Set<TimelineState>(["work", "recovery", "travel", "idle", "unavailable"]);
const DIAGNOSIS_CLASSIFICATIONS = new Set(["equivalent_alternative", "feasible_with_cost", "proven_infeasible", "not_proven"]);
const INTERVENTION_TYPES = new Set(["deadline_extension", "overtime_allowance"]);

export class FallbackDataError extends Error {
  constructor(
    message: string,
    readonly path: string,
  ) {
    super(`${path}: ${message}`);
    this.name = "FallbackDataError";
  }
}

type JsonRecord = Record<string, unknown>;

function record(value: unknown, path: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new FallbackDataError("expected an object", path);
  }
  return value as JsonRecord;
}

function required(value: JsonRecord, key: string, path: string): unknown {
  if (!(key in value)) {
    throw new FallbackDataError("is required", `${path}.${key}`);
  }
  return value[key];
}

function string(value: unknown, path: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new FallbackDataError("expected a non-empty string", path);
  }
  return value;
}

function number(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new FallbackDataError("expected a finite number", path);
  }
  return value;
}

function boolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    throw new FallbackDataError("expected a boolean", path);
  }
  return value;
}

function array(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new FallbackDataError("expected an array", path);
  }
  return value;
}

function stringArray(value: unknown, path: string): void {
  array(value, path).forEach((item, index) => string(item, `${path}[${index}]`));
}

function coordinate(value: unknown, path: string): Coordinate {
  const values = array(value, path);
  if (values.length !== 2) throw new FallbackDataError("expected two coordinates", path);
  return [number(values[0], `${path}[0]`), number(values[1], `${path}[1]`)];
}

function nullableString(value: unknown, path: string): string | null {
  return value === null ? null : string(value, path);
}

function enumValue<T extends string>(value: unknown, allowed: Set<T>, path: string): T {
  const candidate = string(value, path) as T;
  if (!allowed.has(candidate)) {
    throw new FallbackDataError(`unexpected value ${candidate}`, path);
  }
  return candidate;
}

function validateScenario(value: unknown, path: string): Scenario {
  const item = record(value, path);
  string(required(item, "id", path), `${path}.id`);
  string(required(item, "date", path), `${path}.date`);
  number(required(item, "slot_minutes", path), `${path}.slot_minutes`);
  string(required(item, "day_start", path), `${path}.day_start`);
  string(required(item, "day_end", path), `${path}.day_end`);
  string(required(item, "policy_id", path), `${path}.policy_id`);

  array(required(item, "crews", path), `${path}.crews`).forEach((crew, index) => {
    const crewPath = `${path}.crews[${index}]`;
    const value = record(crew, crewPath);
    for (const key of ["id", "name", "shift_start", "shift_end", "start_depot_id", "end_depot_id", "recovery_profile"]) {
      string(required(value, key, crewPath), `${crewPath}.${key}`);
    }
    number(required(value, "max_overtime_minutes", crewPath), `${crewPath}.max_overtime_minutes`);
    stringArray(required(value, "capabilities", crewPath), `${crewPath}.capabilities`);
    stringArray(required(value, "equipment", crewPath), `${crewPath}.equipment`);
  });

  array(required(item, "jobs", path), `${path}.jobs`).forEach((job, index) => {
    const jobPath = `${path}.jobs[${index}]`;
    const value = record(job, jobPath);
    for (const key of ["id", "name", "location_id", "window_start", "window_end"]) {
      string(required(value, key, jobPath), `${jobPath}.${key}`);
    }
    enumValue(required(value, "exertion", jobPath), EXERTIONS, `${jobPath}.exertion`);
    enumValue(required(value, "priority", jobPath), PRIORITIES, `${jobPath}.priority`);
    number(required(value, "active_minutes", jobPath), `${jobPath}.active_minutes`);
    number(required(value, "service_value", jobPath), `${jobPath}.service_value`);
    boolean(required(value, "locked", jobPath), `${jobPath}.locked`);
    nullableString(required(value, "locked_crew_id", jobPath), `${jobPath}.locked_crew_id`);
    nullableString(required(value, "locked_start", jobPath), `${jobPath}.locked_start`);
    stringArray(required(value, "required_capabilities", jobPath), `${jobPath}.required_capabilities`);
    stringArray(required(value, "required_equipment", jobPath), `${jobPath}.required_equipment`);
  });

  array(required(item, "locations", path), `${path}.locations`).forEach((location, index) => {
    const locationPath = `${path}.locations[${index}]`;
    const value = record(location, locationPath);
    string(required(value, "id", locationPath), `${locationPath}.id`);
    coordinate(required(value, "coordinates", locationPath), `${locationPath}.coordinates`);
    const name = required(value, "name", locationPath);
    if (name !== null) string(name, `${locationPath}.name`);
  });

  array(required(item, "heat_series", path), `${path}.heat_series`).forEach((slot, index) => {
    const slotPath = `${path}.heat_series[${index}]`;
    const value = record(slot, slotPath);
    number(required(value, "slot", slotPath), `${slotPath}.slot`);
    string(required(value, "start", slotPath), `${slotPath}.start`);
    number(required(value, "temperature_c", slotPath), `${slotPath}.temperature_c`);
    enumValue(required(value, "band", slotPath), HEAT_BANDS, `${slotPath}.band`);
  });
  stringArray(required(item, "travel_matrix_location_ids", path), `${path}.travel_matrix_location_ids`);
  array(required(item, "travel_matrix_minutes", path), `${path}.travel_matrix_minutes`).forEach((row, rowIndex) => {
    array(row, `${path}.travel_matrix_minutes[${rowIndex}]`).forEach((minutes, columnIndex) =>
      number(minutes, `${path}.travel_matrix_minutes[${rowIndex}][${columnIndex}]`),
    );
  });

  return value as Scenario;
}

function validatePolicy(value: unknown, path: string): Policy {
  const item = record(value, path);
  for (const key of ["id", "name", "disclaimer"]) {
    string(required(item, key, path), `${path}.${key}`);
  }
  boolean(required(item, "synthetic", path), `${path}.synthetic`);
  const thresholds = record(required(item, "band_thresholds_c", path), `${path}.band_thresholds_c`);
  for (const key of ["elevated", "severe", "extreme"]) {
    number(required(thresholds, key, `${path}.band_thresholds_c`), `${path}.band_thresholds_c.${key}`);
  }
  number(required(item, "rolling_window_slots", path), `${path}.rolling_window_slots`);
  stringArray(required(item, "eligible_recovery_profiles", path), `${path}.eligible_recovery_profiles`);
  boolean(required(item, "travel_counts_as_recovery", path), `${path}.travel_counts_as_recovery`);
  array(required(item, "rules", path), `${path}.rules`).forEach((rule, index) => {
    const rulePath = `${path}.rules[${index}]`;
    const value = record(rule, rulePath);
    string(required(value, "id", rulePath), `${rulePath}.id`);
    enumValue(required(value, "band", rulePath), HEAT_BANDS, `${rulePath}.band`);
    enumValue(required(value, "exertion", rulePath), EXERTIONS, `${rulePath}.exertion`);
    number(required(value, "max_active_slots", rulePath), `${rulePath}.max_active_slots`);
    number(required(value, "min_recovery_slots", rulePath), `${rulePath}.min_recovery_slots`);
    boolean(required(value, "stop_work", rulePath), `${rulePath}.stop_work`);
  });
  return value as Policy;
}

function validateMetrics(value: unknown, path: string): void {
  const item = record(value, path);
  for (const key of [
    "critical_jobs_scheduled",
    "critical_jobs_total",
    "planned_service_value",
    "mandatory_policy_conflicts",
    "travel_minutes",
    "overtime_minutes",
    "active_work_minutes",
    "eligible_recovery_minutes",
  ]) {
    number(required(item, key, path), `${path}.${key}`);
  }
}

function validatePlanJobState(value: unknown, path: string): void {
  const item = record(value, path);
  nullableString(required(item, "crew_id", path), `${path}.crew_id`);
  nullableString(required(item, "start", path), `${path}.start`);
  nullableString(required(item, "end", path), `${path}.end`);
}

function validateTimelineSegment(value: unknown, path: string): void {
  const item = record(value, path);
  string(required(item, "crew_id", path), `${path}.crew_id`);
  enumValue(required(item, "state", path), TIMELINE_STATES, `${path}.state`);
  nullableString(required(item, "job_id", path), `${path}.job_id`);
  number(required(item, "start_slot", path), `${path}.start_slot`);
  number(required(item, "end_slot", path), `${path}.end_slot`);
  string(required(item, "start", path), `${path}.start`);
  string(required(item, "end", path), `${path}.end`);
  const exertion = required(item, "exertion", path);
  if (exertion !== null) enumValue(exertion, EXERTIONS, `${path}.exertion`);
  nullableString(required(item, "location_id", path), `${path}.location_id`);
  stringArray(required(item, "policy_rule_ids", path), `${path}.policy_rule_ids`);
}

function validateRouteSegment(value: unknown, path: string): void {
  const item = record(value, path);
  for (const key of ["crew_id", "from_location_id", "to_location_id", "departure", "arrival"]) {
    string(required(item, key, path), `${path}.${key}`);
  }
  number(required(item, "travel_minutes", path), `${path}.travel_minutes`);
  coordinate(required(item, "from_coordinates", path), `${path}.from_coordinates`);
  coordinate(required(item, "to_coordinates", path), `${path}.to_coordinates`);
}

function validateJobResult(value: unknown, path: string): void {
  const item = record(value, path);
  string(required(item, "job_id", path), `${path}.job_id`);
  boolean(required(item, "served", path), `${path}.served`);
  nullableString(required(item, "crew_id", path), `${path}.crew_id`);
  nullableString(required(item, "start", path), `${path}.start`);
  nullableString(required(item, "end", path), `${path}.end`);
  nullableString(required(item, "status_reason_code", path), `${path}.status_reason_code`);
}

function validatePlan(value: unknown, path: string): Plan {
  const item = record(value, path);
  string(required(item, "label", path), `${path}.label`);
  enumValue(required(item, "status", path), SOLVER_STATUSES, `${path}.status`);
  boolean(required(item, "maximum_claim_allowed", path), `${path}.maximum_claim_allowed`);
  number(required(item, "wall_time_seconds", path), `${path}.wall_time_seconds`);
  array(required(item, "stages", path), `${path}.stages`).forEach((stage, index) => {
    const stagePath = `${path}.stages[${index}]`;
    const value = record(stage, stagePath);
    enumValue(required(value, "name", stagePath), STAGE_NAMES, `${stagePath}.name`);
    enumValue(required(value, "status", stagePath), SOLVER_STATUSES, `${stagePath}.status`);
    const objectiveValue = required(value, "objective_value", stagePath);
    if (objectiveValue !== null) number(objectiveValue, `${stagePath}.objective_value`);
    const bestBound = required(value, "best_bound", stagePath);
    if (bestBound !== null) number(bestBound, `${stagePath}.best_bound`);
    number(required(value, "wall_time_seconds", stagePath), `${stagePath}.wall_time_seconds`);
  });
  validateMetrics(required(item, "metrics", path), `${path}.metrics`);
  array(required(item, "timeline_segments", path), `${path}.timeline_segments`).forEach((segment, index) =>
    validateTimelineSegment(segment, `${path}.timeline_segments[${index}]`),
  );
  array(required(item, "route_segments", path), `${path}.route_segments`).forEach((segment, index) =>
    validateRouteSegment(segment, `${path}.route_segments[${index}]`),
  );
  array(required(item, "jobs", path), `${path}.jobs`).forEach((job, index) =>
    validateJobResult(job, `${path}.jobs[${index}]`),
  );
  return value as Plan;
}

function validateSolveResponse(value: unknown, path: string): SolveResponse {
  const item = record(value, path);
  const scenario = record(required(item, "scenario", path), `${path}.scenario`);
  string(required(scenario, "id", `${path}.scenario`), `${path}.scenario.id`);
  string(required(scenario, "policy_id", `${path}.scenario`), `${path}.scenario.policy_id`);
  string(required(scenario, "policy_disclaimer", `${path}.scenario`), `${path}.scenario.policy_disclaimer`);
  number(required(scenario, "slot_minutes", `${path}.scenario`), `${path}.scenario.slot_minutes`);
  number(required(scenario, "heat_adjustment_c", `${path}.scenario`), `${path}.scenario.heat_adjustment_c`);

  const plans = record(required(item, "plans", path), `${path}.plans`);
  validatePlan(required(plans, "service_first", `${path}.plans`), `${path}.plans.service_first`);
  validatePlan(required(plans, "policy_constrained", `${path}.plans`), `${path}.plans.policy_constrained`);
  const shock = required(plans, "heat_shock", `${path}.plans`);
  if (shock !== null) validatePlan(shock, `${path}.plans.heat_shock`);

  array(required(item, "plan_diff", path), `${path}.plan_diff`).forEach((diff, index) => {
    const diffPath = `${path}.plan_diff[${index}]`;
    const value = record(diff, diffPath);
    string(required(value, "job_id", diffPath), `${diffPath}.job_id`);
    enumValue(required(value, "change", diffPath), PLAN_CHANGES, `${diffPath}.change`);
    const before = required(value, "before", diffPath);
    const after = required(value, "after", diffPath);
    if (before !== null) validatePlanJobState(before, `${diffPath}.before`);
    if (after !== null) validatePlanJobState(after, `${diffPath}.after`);
    stringArray(required(value, "binding_rule_ids", diffPath), `${diffPath}.binding_rule_ids`);
    string(required(value, "explanation_code", diffPath), `${diffPath}.explanation_code`);
  });
  record(required(item, "diagnostics", path), `${path}.diagnostics`);
  return value as SolveResponse;
}

function validateDiagnosis(value: unknown, path: string): DiagnosisResponse {
  const item = record(value, path);
  string(required(item, "job_id", path), `${path}.job_id`);
  enumValue(required(item, "classification", path), DIAGNOSIS_CLASSIFICATIONS, `${path}.classification`);
  enumValue(required(item, "proof_status", path), SOLVER_STATUSES, `${path}.proof_status`);
  stringArray(required(item, "retained_commitments", path), `${path}.retained_commitments`);
  stringArray(required(item, "displaced_job_ids", path), `${path}.displaced_job_ids`);
  validateMetricsDelta(required(item, "objective_delta", path), `${path}.objective_delta`);
  stringArray(required(item, "binding_rule_ids", path), `${path}.binding_rule_ids`);
  array(required(item, "tested_interventions", path), `${path}.tested_interventions`).forEach((intervention, index) => {
    const interventionPath = `${path}.tested_interventions[${index}]`;
    const value = record(intervention, interventionPath);
    enumValue(required(value, "type", interventionPath), INTERVENTION_TYPES, `${interventionPath}.type`);
    number(required(value, "value_minutes", interventionPath), `${interventionPath}.value_minutes`);
    enumValue(required(value, "status", interventionPath), SOLVER_STATUSES, `${interventionPath}.status`);
    validateMetricsDelta(required(value, "objective_delta", interventionPath), `${interventionPath}.objective_delta`);
  });
  return value as DiagnosisResponse;
}

function validateSavedResultMetadata(value: unknown, path: string): SavedResultMetadata {
  const item = record(value, path);
  for (const key of ["fixture_version", "generated_at", "solver_version", "sha256"]) {
    string(required(item, key, path), `${path}.${key}`);
  }
  return value as SavedResultMetadata;
}

function validateMetricsDelta(value: unknown, path: string): void {
  const item = record(value, path);
  for (const key of ["critical_service", "planned_service_value", "travel_minutes", "overtime_minutes"]) {
    number(required(item, key, path), `${path}.${key}`);
  }
}

function validateManifest(value: unknown, path: string): SavedManifest {
  const item = record(value, path);
  for (const key of [
    "fixture_version",
    "generated_at",
    "python_version",
    "ortools_version",
    "designated_diagnosis_job_id",
    "canonical_hash_format",
  ]) {
    string(required(item, key, path), `${path}.${key}`);
  }
  number(required(item, "solver_seed", path), `${path}.solver_seed`);
  number(required(item, "solver_workers", path), `${path}.solver_workers`);
  number(required(item, "time_limit_seconds", path), `${path}.time_limit_seconds`);
  stringArray(required(item, "canonical_hash_excluded_fields", path), `${path}.canonical_hash_excluded_fields`);
  for (const key of ["input_hashes", "output_hashes"] as const) {
    const hashes = record(required(item, key, path), `${path}.${key}`);
    for (const [name, hash] of Object.entries(hashes)) string(hash, `${path}.${key}.${name}`);
  }
  return value as SavedManifest;
}

export function parseDemoBundle(value: unknown): DemoBundle {
  const item = record(value, "bundle");
  string(required(item, "fixture_version", "bundle"), "bundle.fixture_version");
  string(required(item, "generated_at", "bundle"), "bundle.generated_at");
  const scenario = validateScenario(required(item, "scenario", "bundle"), "bundle.scenario");
  const policy = validatePolicy(required(item, "policy", "bundle"), "bundle.policy");
  const baseSolve = validateSolveResponse(required(item, "base_solve", "bundle"), "bundle.base_solve");
  const heatShockSolve = validateSolveResponse(
    required(item, "heat_shock_solve", "bundle"),
    "bundle.heat_shock_solve",
  );
  const diagnosesValue = record(required(item, "diagnoses", "bundle"), "bundle.diagnoses");
  const diagnoses: Record<string, DiagnosisResponse> = {};
  for (const [jobId, diagnosis] of Object.entries(diagnosesValue)) {
    diagnoses[jobId] = validateDiagnosis(diagnosis, `bundle.diagnoses.${jobId}`);
  }
  const manifest = validateManifest(required(item, "manifest", "bundle"), "bundle.manifest");

  return {
    fixture_version: string(item.fixture_version, "bundle.fixture_version"),
    generated_at: string(item.generated_at, "bundle.generated_at"),
    scenario,
    policy,
    base_solve: baseSolve,
    heat_shock_solve: heatShockSolve,
    diagnoses,
    manifest,
  };
}

export function parseDemoResponse(value: unknown): DemoResponse {
  const item = record(value, "response");
  const scenario = validateScenario(required(item, "scenario", "response"), "response.scenario");
  const policy = validatePolicy(required(item, "policy", "response"), "response.policy");
  const coordinates = record(required(item, "display_coordinates", "response"), "response.display_coordinates");
  const displayCoordinates: Record<string, Coordinate> = {};
  for (const [locationId, coordinateValue] of Object.entries(coordinates)) {
    const coordinatePath = `response.display_coordinates.${locationId}`;
    displayCoordinates[locationId] = coordinate(coordinateValue, coordinatePath);
  }
  const metadataValue = item.saved_result_metadata ?? null;
  const savedResultMetadata = metadataValue === null ? null : validateSavedResultMetadata(metadataValue, "response.saved_result_metadata");
  return {
    scenario,
    policy,
    display_coordinates: displayCoordinates,
    saved_result_metadata: savedResultMetadata,
  };
}

export function parseSolveResponse(value: unknown): SolveResponse {
  return validateSolveResponse(value, "response");
}

export function parseDiagnosisResponse(value: unknown): DiagnosisResponse {
  return validateDiagnosis(value, "response");
}

function savedSolveCandidate(bundle: DemoBundle, heatAdjustment: number): SolveResponse | null {
  if (heatAdjustment === 0) return bundle.base_solve;
  if (heatAdjustment === 2) return bundle.heat_shock_solve;
  return null;
}

function deepEqual(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) return true;
  if (typeof left !== "object" || left === null || typeof right !== "object" || right === null) return false;
  if (Array.isArray(left) || Array.isArray(right)) {
    return Array.isArray(left) && Array.isArray(right) && left.length === right.length && left.every((value, index) => deepEqual(value, right[index]));
  }
  const leftRecord = left as JsonRecord;
  const rightRecord = right as JsonRecord;
  const leftKeys = Object.keys(leftRecord);
  const rightKeys = Object.keys(rightRecord);
  return leftKeys.length === rightKeys.length && leftKeys.every((key) => key in rightRecord && deepEqual(leftRecord[key], rightRecord[key]));
}

function matchesSavedSolve(
  bundle: DemoBundle,
  result: SolveResponse,
  request: Pick<SolveRequest, "scenario" | "policy" | "heat_adjustment_c">,
): boolean {
  return (
    deepEqual(bundle.scenario, request.scenario) &&
    deepEqual(bundle.policy, request.policy) &&
    result.scenario.id === request.scenario.id &&
    result.scenario.policy_id === request.policy.id &&
    result.scenario.heat_adjustment_c === request.heat_adjustment_c
  );
}

export function findSavedSolve(
  bundle: DemoBundle,
  request: Pick<SolveRequest, "scenario" | "policy" | "heat_adjustment_c">,
): SolveResponse | null {
  const candidate = savedSolveCandidate(bundle, request.heat_adjustment_c);
  return candidate !== null && matchesSavedSolve(bundle, candidate, request) ? candidate : null;
}

export function findSavedDiagnosis(
  bundle: DemoBundle,
  request: Pick<DiagnoseRequest, "scenario" | "policy" | "heat_adjustment_c" | "job_id">,
): DiagnosisResponse | null {
  const savedSolve = findSavedSolve(bundle, request);
  if (savedSolve === null || request.heat_adjustment_c !== 0) return null;
  const candidate = bundle.diagnoses[request.job_id];
  return candidate?.job_id === request.job_id ? candidate : null;
}

export interface FallbackLoadOptions {
  url?: string;
  fetcher?: typeof fetch;
}

export async function loadFallbackDemo({
  url = "/fallback/demo.json",
  fetcher = fetch,
}: FallbackLoadOptions = {}): Promise<DemoBundle> {
  let response: Response;
  try {
    response = await fetcher(url);
  } catch (error) {
    const message = error instanceof Error ? error.message : "request failed";
    throw new FallbackDataError(message, "fallback.request");
  }
  if (!response.ok) {
    throw new FallbackDataError(`request returned HTTP ${response.status}`, "fallback.request");
  }
  let payload: unknown;
  try {
    payload = (await response.json()) as unknown;
  } catch {
    throw new FallbackDataError("response was not valid JSON", "fallback.json");
  }
  return parseDemoBundle(payload);
}
