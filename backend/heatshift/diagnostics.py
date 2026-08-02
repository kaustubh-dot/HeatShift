"""Forced-inclusion diagnosis for deferred jobs."""

from __future__ import annotations

import math

from .metrics import ModelReconciliationError, PlanFacts, extract_plan_facts
from .models import (
    ApiErrorDetail,
    DiagnosisClassification,
    DiagnosisResponse,
    ObjectiveDelta,
    Policy,
    Scenario,
    SolverStatus,
)
from .optimizer import StagedSolveResult, build_optimizer_model, solve_staged
from .patterns import ExecutionPattern, generate_policy_constrained_patterns
from .timegrid import adjust_heat_series
from .validation import validate_scenario


class DiagnosisValidationError(ValueError):
    """Structured validation failure for a diagnosis request."""

    def __init__(self, details: tuple[ApiErrorDetail, ...] | list[ApiErrorDetail]) -> None:
        self.details = tuple(details)
        self.issues = self.details
        summary = "; ".join(f"{detail.path}: {detail.message}" for detail in self.details)
        super().__init__(summary or "diagnosis validation failed")


def diagnose_job(
    scenario: Scenario,
    policy: Policy,
    original_facts: PlanFacts,
    original_result: StagedSolveResult,
    job_id: str,
    *,
    heat_adjustment_c: float | int = 0,
    time_limit_seconds: float | int = 5,
) -> DiagnosisResponse:
    """Force one deferred job into a fresh constrained optimization model.

    ``original_facts`` and ``original_result`` must describe the best proven or
    incumbent constrained plan for the same request conditions. A nonzero heat
    adjustment is applied to the fresh forced model using the policy's
    thresholds; the input scenario and original model are never mutated.
    """

    _validate_inputs(
        scenario,
        policy,
        original_facts,
        job_id,
        heat_adjustment_c,
        time_limit_seconds,
    )

    adjusted_scenario = _adjust_scenario(scenario, policy, heat_adjustment_c)
    patterns = generate_policy_constrained_patterns(adjusted_scenario, policy)
    forced_model = build_optimizer_model(
        adjusted_scenario,
        policy,
        patterns,
        enforce_policy=True,
    )
    forced_model.model.Add(forced_model.serve[job_id] == 1)
    forced_model.model.Add(
        forced_model.objective_expressions.critical_service
        >= original_facts.metrics.critical_jobs_scheduled
    )
    forced_result = solve_staged(forced_model, float(time_limit_seconds))

    forced_facts: PlanFacts | None = None
    if forced_result.selected_pattern_indices:
        try:
            forced_facts = extract_plan_facts(forced_model, forced_result)
        except ModelReconciliationError as error:
            raise DiagnosisValidationError(
                (
                    ApiErrorDetail(
                        path="forced_solver_result",
                        code="MODEL_RECONCILIATION",
                        message=str(error),
                    ),
                )
            ) from error

    classification = _classify(
        original_facts,
        original_result,
        forced_facts,
        forced_result,
    )
    if forced_facts is None:
        objective_delta = _zero_delta()
        displaced_job_ids: list[str] = []
    else:
        objective_delta = _objective_delta(original_facts, forced_facts)
        displaced_job_ids = _displaced_job_ids(original_facts, forced_facts)

    return DiagnosisResponse(
        job_id=job_id,
        classification=classification,
        proof_status=forced_result.status,
        retained_commitments=[
            "all-mandatory-rules",
            "original-critical-service-count",
            f"forced-job:{job_id}",
        ],
        displaced_job_ids=displaced_job_ids,
        objective_delta=objective_delta,
        binding_rule_ids=_binding_rule_ids(
            job_id,
            policy,
            original_facts,
            forced_facts,
            patterns,
        ),
        tested_interventions=[],
    )


def diagnose_forced_inclusion(
    scenario: Scenario,
    policy: Policy,
    original_facts: PlanFacts,
    original_result: StagedSolveResult,
    job_id: str,
    *,
    heat_adjustment_c: float | int = 0,
    time_limit_seconds: float | int = 5,
) -> DiagnosisResponse:
    """Descriptive alias for the public forced-inclusion operation."""

    return diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        job_id,
        heat_adjustment_c=heat_adjustment_c,
        time_limit_seconds=time_limit_seconds,
    )


def _validate_inputs(
    scenario: Scenario,
    policy: Policy,
    original_facts: PlanFacts,
    job_id: str,
    heat_adjustment_c: float | int,
    time_limit_seconds: float | int,
) -> None:
    scenario_issues = validate_scenario(scenario, policy)
    if scenario_issues:
        raise DiagnosisValidationError(scenario_issues)
    if isinstance(time_limit_seconds, bool) or not isinstance(time_limit_seconds, (int, float)):
        raise DiagnosisValidationError(
            (
                ApiErrorDetail(
                    path="time_limit_seconds",
                    code="INVALID_VALUE",
                    message="time_limit_seconds must be a finite non-negative number",
                ),
            )
        )
    if not math.isfinite(float(time_limit_seconds)) or time_limit_seconds < 0:
        raise DiagnosisValidationError(
            (
                ApiErrorDetail(
                    path="time_limit_seconds",
                    code="INVALID_VALUE",
                    message="time_limit_seconds must be a finite non-negative number",
                ),
            )
        )
    if isinstance(heat_adjustment_c, bool) or not isinstance(heat_adjustment_c, (int, float)):
        raise DiagnosisValidationError(
            (
                ApiErrorDetail(
                    path="heat_adjustment_c",
                    code="INVALID_VALUE",
                    message="heat_adjustment_c must be a finite number",
                ),
            )
        )
    if not math.isfinite(float(heat_adjustment_c)):
        raise DiagnosisValidationError(
            (
                ApiErrorDetail(
                    path="heat_adjustment_c",
                    code="INVALID_VALUE",
                    message="heat_adjustment_c must be a finite number",
                ),
            )
        )

    scenario_job_ids = {job.id for job in scenario.jobs}
    if job_id not in scenario_job_ids:
        raise DiagnosisValidationError(
            (
                ApiErrorDetail(
                    path="job_id",
                    code="UNKNOWN_REFERENCE",
                    message=f"unknown job ID {job_id!r}",
                ),
            )
        )

    original_jobs = {job.job_id: job for job in original_facts.jobs}
    original_job = original_jobs.get(job_id)
    if original_job is None:
        raise DiagnosisValidationError(
            (
                ApiErrorDetail(
                    path="original_plan.jobs",
                    code="MISSING_JOB_RESULT",
                    message=f"original plan has no result for job ID {job_id!r}",
                ),
            )
        )
    if original_job.served:
        raise DiagnosisValidationError(
            (
                ApiErrorDetail(
                    path="job_id",
                    code="ALREADY_SERVED",
                    message=f"job ID {job_id!r} is already served in the original plan",
                ),
            )
        )


def _adjust_scenario(scenario: Scenario, policy: Policy, heat_adjustment_c: float | int) -> Scenario:
    if heat_adjustment_c == 0:
        return scenario
    return scenario.model_copy(
        deep=True,
        update={
            "heat_series": adjust_heat_series(
                scenario.heat_series,
                heat_adjustment_c,
                policy.band_thresholds_c,
            )
        },
    )


def _classify(
    original_facts: PlanFacts,
    original_result: StagedSolveResult,
    forced_facts: PlanFacts | None,
    forced_result: StagedSolveResult,
) -> DiagnosisClassification:
    if forced_result.status is SolverStatus.INFEASIBLE:
        return DiagnosisClassification.PROVEN_INFEASIBLE
    if forced_facts is None or forced_result.status not in {
        SolverStatus.OPTIMAL,
        SolverStatus.FEASIBLE,
    }:
        return DiagnosisClassification.NOT_PROVEN

    objective_equal = _objective_vector(original_facts) == _objective_vector(forced_facts)
    if (
        objective_equal
        and original_result.maximum_claim_allowed
        and forced_result.maximum_claim_allowed
    ):
        return DiagnosisClassification.EQUIVALENT_ALTERNATIVE
    return DiagnosisClassification.FEASIBLE_WITH_COST


def _objective_vector(facts: PlanFacts) -> tuple[int, int, int, int]:
    metrics = facts.metrics
    return (
        metrics.critical_jobs_scheduled,
        metrics.planned_service_value,
        metrics.travel_minutes,
        metrics.overtime_minutes,
    )


def _objective_delta(original: PlanFacts, forced: PlanFacts) -> ObjectiveDelta:
    original_vector = _objective_vector(original)
    forced_vector = _objective_vector(forced)
    return ObjectiveDelta(
        critical_service=forced_vector[0] - original_vector[0],
        planned_service_value=forced_vector[1] - original_vector[1],
        travel_minutes=forced_vector[2] - original_vector[2],
        overtime_minutes=forced_vector[3] - original_vector[3],
    )


def _zero_delta() -> ObjectiveDelta:
    return ObjectiveDelta(
        critical_service=0,
        planned_service_value=0,
        travel_minutes=0,
        overtime_minutes=0,
    )


def _displaced_job_ids(original: PlanFacts, forced: PlanFacts) -> list[str]:
    original_served = {job.job_id for job in original.jobs if job.served}
    forced_served = {job.job_id for job in forced.jobs if job.served}
    return sorted(original_served - forced_served)


def _binding_rule_ids(
    job_id: str,
    policy: Policy,
    original: PlanFacts,
    forced: PlanFacts | None,
    patterns: list[ExecutionPattern],
) -> list[str]:
    policy_rule_ids = {rule.id for rule in policy.rules}
    rule_ids: set[str] = set()
    if forced is not None:
        rule_ids.update(
            rule_id
            for segment in forced.timeline_segments
            if segment.job_id == job_id and segment.state.value == "work"
            for rule_id in segment.policy_rule_ids
        )
        rule_ids.update(
            rule_id
            for conflict in forced.conflicts.conflicts
            if job_id in conflict.job_ids
            for rule_id in conflict.rule_ids
        )
    else:
        rule_ids.update(
            rule_id
            for pattern in patterns
            if pattern.job_id == job_id
            for _, pattern_rule_ids in pattern.rule_ids_by_work_slot
            for rule_id in pattern_rule_ids
        )
    rule_ids.update(
        rule_id
        for conflict in original.conflicts.conflicts
        if job_id in conflict.job_ids
        for rule_id in conflict.rule_ids
    )
    return sorted(rule_id for rule_id in rule_ids if rule_id in policy_rule_ids)
