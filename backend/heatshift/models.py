"""Canonical request, fixture, and result models for HeatShift.

These models describe the JSON contract only. Cross-reference and scheduling
rules belong to the validation and solver layers that consume them.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    StrictBool,
    StrictInt,
    StrictStr,
)


def _require_non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty")
    return value


def _require_finite_number(value: object) -> object:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("must be a finite number")
    if not math.isfinite(float(value)):
        raise ValueError("must be finite")
    return value


NonEmptyStr = Annotated[StrictStr, AfterValidator(_require_non_blank)]
Identifier = Annotated[
    StrictStr,
    StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
]
TimeString = Annotated[
    StrictStr,
    StringConstraints(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$"),
]
DateString = Annotated[StrictStr, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")]
NonNegativeInt = Annotated[StrictInt, Field(ge=0)]
FiniteNumber = Annotated[int | float, BeforeValidator(_require_finite_number)]
NonNegativeNumber = Annotated[FiniteNumber, Field(ge=0)]
Coordinate = Annotated[list[FiniteNumber], Field(min_length=2, max_length=2)]


class HeatBand(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    SEVERE = "severe"
    EXTREME = "extreme"


class HeatThresholdBand(str, Enum):
    ELEVATED = "elevated"
    SEVERE = "severe"
    EXTREME = "extreme"


class Exertion(str, Enum):
    HEAVY = "heavy"
    MODERATE = "moderate"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    PLANNED = "planned"


class SolverStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNKNOWN = "UNKNOWN"
    MODEL_INVALID = "MODEL_INVALID"


class TimelineState(str, Enum):
    WORK = "work"
    RECOVERY = "recovery"
    TRAVEL = "travel"
    IDLE = "idle"
    UNAVAILABLE = "unavailable"


class StageName(str, Enum):
    CRITICAL_SERVICE = "critical_service"
    PLANNED_SERVICE_VALUE = "planned_service_value"
    TRAVEL_MINUTES = "travel_minutes"
    OVERTIME_MINUTES = "overtime_minutes"
    STANDALONE_RECOVERY = "standalone_recovery"


class PlanChange(str, Enum):
    UNCHANGED = "unchanged"
    MOVED_TIME = "moved_time"
    MOVED_CREW = "moved_crew"
    RECOVERY_ADDED = "recovery_added"
    SERVED = "served"
    DEFERRED = "deferred"


class DiagnosisClassification(str, Enum):
    EQUIVALENT_ALTERNATIVE = "equivalent_alternative"
    FEASIBLE_WITH_COST = "feasible_with_cost"
    PROVEN_INFEASIBLE = "proven_infeasible"
    NOT_PROVEN = "not_proven"


class InterventionType(str, Enum):
    DEADLINE_EXTENSION = "deadline_extension"
    OVERTIME_ALLOWANCE = "overtime_allowance"


class ApiErrorCode(str, Enum):
    INVALID_SCENARIO = "INVALID_SCENARIO"
    INVALID_POLICY = "INVALID_POLICY"
    MODEL_INVALID = "MODEL_INVALID"
    SOLVER_TIMEOUT = "SOLVER_TIMEOUT"
    NO_FEASIBLE_PLAN = "NO_FEASIBLE_PLAN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class StrictModel(BaseModel):
    """Base configuration shared by every public contract model."""

    model_config = ConfigDict(extra="forbid")


class Crew(StrictModel):
    id: Identifier
    name: NonEmptyStr
    shift_start: TimeString
    shift_end: TimeString
    start_depot_id: Identifier
    end_depot_id: Identifier
    capabilities: list[NonEmptyStr]
    equipment: list[NonEmptyStr]
    max_overtime_minutes: NonNegativeInt
    recovery_profile: Identifier


class Job(StrictModel):
    id: Identifier
    name: NonEmptyStr
    location_id: Identifier
    active_minutes: NonNegativeInt
    exertion: Exertion
    priority: Priority
    service_value: NonNegativeInt
    window_start: TimeString
    window_end: TimeString
    required_capabilities: list[NonEmptyStr]
    required_equipment: list[NonEmptyStr]
    locked: StrictBool
    locked_crew_id: Identifier | None = None
    locked_start: TimeString | None = None


class Location(StrictModel):
    id: Identifier
    coordinates: Coordinate
    name: NonEmptyStr | None = None


class HeatSlot(StrictModel):
    slot: NonNegativeInt
    start: TimeString
    temperature_c: FiniteNumber
    band: HeatBand


class Scenario(StrictModel):
    id: Identifier
    date: DateString
    slot_minutes: NonNegativeInt
    day_start: TimeString
    day_end: TimeString
    policy_id: Identifier
    crews: list[Crew]
    jobs: list[Job]
    locations: list[Location]
    heat_series: list[HeatSlot]
    travel_matrix_location_ids: list[Identifier]
    travel_matrix_minutes: list[list[NonNegativeInt]]


class PolicyRule(StrictModel):
    id: Identifier
    band: HeatBand
    exertion: Exertion
    max_active_slots: NonNegativeInt
    min_recovery_slots: NonNegativeInt
    stop_work: StrictBool


class Policy(StrictModel):
    id: Identifier
    name: NonEmptyStr
    synthetic: StrictBool
    disclaimer: NonEmptyStr
    band_thresholds_c: dict[HeatThresholdBand, FiniteNumber]
    rolling_window_slots: NonNegativeInt
    eligible_recovery_profiles: list[Identifier]
    travel_counts_as_recovery: StrictBool
    rules: list[PolicyRule]


class SolveRequest(StrictModel):
    scenario: Scenario
    policy: Policy
    heat_adjustment_c: FiniteNumber
    time_limit_seconds: NonNegativeNumber


class DiagnoseRequest(StrictModel):
    scenario: Scenario
    policy: Policy
    job_id: Identifier
    heat_adjustment_c: FiniteNumber
    time_limit_seconds: NonNegativeNumber


class Stage(StrictModel):
    name: StageName
    status: SolverStatus
    objective_value: FiniteNumber | None
    best_bound: FiniteNumber | None
    wall_time_seconds: NonNegativeNumber


class Metrics(StrictModel):
    critical_jobs_scheduled: NonNegativeInt
    critical_jobs_total: NonNegativeInt
    planned_service_value: NonNegativeInt
    mandatory_policy_conflicts: NonNegativeInt
    travel_minutes: NonNegativeInt
    overtime_minutes: NonNegativeInt
    active_work_minutes: NonNegativeInt
    eligible_recovery_minutes: NonNegativeInt


class TimelineSegment(StrictModel):
    crew_id: Identifier
    state: TimelineState
    job_id: Identifier | None = None
    start_slot: NonNegativeInt
    end_slot: NonNegativeInt
    start: TimeString
    end: TimeString
    exertion: Exertion | None = None
    location_id: Identifier | None = None
    policy_rule_ids: list[Identifier] = Field(default_factory=list)


class RouteSegment(StrictModel):
    crew_id: Identifier
    from_location_id: Identifier
    to_location_id: Identifier
    departure: TimeString
    arrival: TimeString
    travel_minutes: NonNegativeInt
    from_coordinates: Coordinate
    to_coordinates: Coordinate


class JobResult(StrictModel):
    job_id: Identifier
    served: StrictBool
    crew_id: Identifier | None = None
    start: TimeString | None = None
    end: TimeString | None = None
    status_reason_code: NonEmptyStr | None = None


class Plan(StrictModel):
    label: NonEmptyStr
    status: SolverStatus
    maximum_claim_allowed: StrictBool
    wall_time_seconds: NonNegativeNumber
    stages: list[Stage]
    metrics: Metrics
    timeline_segments: list[TimelineSegment]
    route_segments: list[RouteSegment]
    jobs: list[JobResult]


class PlanJobState(StrictModel):
    crew_id: Identifier | None = None
    start: TimeString | None = None
    end: TimeString | None = None


class PlanDiff(StrictModel):
    job_id: Identifier
    change: PlanChange
    before: PlanJobState | None = None
    after: PlanJobState | None = None
    binding_rule_ids: list[Identifier] = Field(default_factory=list)
    explanation_code: NonEmptyStr


class SolveScenario(StrictModel):
    id: Identifier
    policy_id: Identifier
    policy_disclaimer: NonEmptyStr
    slot_minutes: NonNegativeInt
    heat_adjustment_c: FiniteNumber


class PlanSet(StrictModel):
    service_first: Plan
    policy_constrained: Plan
    heat_shock: Plan | None = None


class SolveResponse(StrictModel):
    scenario: SolveScenario
    plans: PlanSet
    plan_diff: list[PlanDiff]
    diagnostics: dict[str, Any]


class ObjectiveDelta(StrictModel):
    critical_service: StrictInt
    planned_service_value: StrictInt
    travel_minutes: StrictInt
    overtime_minutes: StrictInt


class TestedIntervention(StrictModel):
    type: InterventionType
    value_minutes: NonNegativeInt
    status: SolverStatus
    objective_delta: ObjectiveDelta


class DiagnosisResponse(StrictModel):
    job_id: Identifier
    classification: DiagnosisClassification
    proof_status: SolverStatus
    retained_commitments: list[NonEmptyStr]
    displaced_job_ids: list[Identifier]
    objective_delta: ObjectiveDelta
    binding_rule_ids: list[Identifier]
    tested_interventions: list[TestedIntervention]


class ApiErrorDetail(StrictModel):
    path: NonEmptyStr
    code: NonEmptyStr
    message: NonEmptyStr


class ApiError(StrictModel):
    code: ApiErrorCode
    message: NonEmptyStr
    details: list[ApiErrorDetail]


class SavedResultMetadata(StrictModel):
    fixture_version: NonEmptyStr
    generated_at: NonEmptyStr
    solver_version: NonEmptyStr
    sha256: NonEmptyStr


class DemoResponse(StrictModel):
    scenario: Scenario
    policy: Policy
    display_coordinates: dict[Identifier, Coordinate]
    saved_result_metadata: SavedResultMetadata | None = None
