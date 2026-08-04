"""Application-level orchestration for baseline and constrained solves."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .differences import derive_plan_diff
from .metrics import ModelReconciliationError, PlanFacts, extract_plan_facts
from .models import (
    ApiErrorCode,
    ApiErrorDetail,
    Plan,
    PlanSet,
    SolveRequest,
    SolveResponse,
    SolveScenario,
    Stage,
    Scenario,
    Policy,
    SolverStatus,
)
from .optimizer import StagedSolveResult, build_optimizer_model, solve_staged
from .patterns import generate_baseline_patterns, generate_policy_constrained_patterns
from .timegrid import adjust_heat_series
from .validation import validate_scenario


@dataclass(slots=True)
class SolveServiceError(ValueError):
    """Precise service-layer failure that the API boundary can map later."""

    code: ApiErrorCode
    message: str
    details: tuple[ApiErrorDetail, ...] = ()

    def __post_init__(self) -> None:
        ValueError.__init__(self, self.message)


def solve_scenario(
    scenario: Scenario | SolveRequest,
    policy: Policy | None = None,
    heat_adjustment_c: float | int | None = None,
    time_limit_seconds: float | int | None = None,
) -> SolveResponse:
    """Run the canonical baseline/constrained solve sequence.

    The request-object form is accepted for the future HTTP boundary; the
    explicit argument form keeps unit and integration callers simple.
    """

    if isinstance(scenario, SolveRequest):
        request = scenario
        scenario = request.scenario
        policy = request.policy
        heat_adjustment_c = request.heat_adjustment_c
        time_limit_seconds = request.time_limit_seconds
    if policy is None or heat_adjustment_c is None or time_limit_seconds is None:
        raise ValueError("policy, heat_adjustment_c, and time_limit_seconds are required")
    if time_limit_seconds < 0:
        raise ValueError("time_limit_seconds must be non-negative")

    issues = validate_scenario(scenario, policy)
    if issues:
        raise SolveServiceError(
            code=ApiErrorCode.INVALID_SCENARIO,
            message="Scenario and policy validation failed.",
            details=tuple(issues),
        )

    plan_count = 2 if heat_adjustment_c == 0 else 3
    per_plan_budget = float(time_limit_seconds) / plan_count if plan_count else 0.0

    # The two base branches read the same immutable inputs but build independent
    # CP-SAT models. Running them concurrently preserves the per-branch budget
    # and deterministic one-worker solver configuration while keeping the
    # request wall time close to the slower branch rather than their sum.
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="heatshift-solve") as executor:
        baseline_future = executor.submit(
            _solve_facts,
            scenario,
            policy,
            per_plan_budget,
            constrained=False,
        )
        constrained_future = executor.submit(
            _solve_facts,
            scenario,
            policy,
            per_plan_budget,
            constrained=True,
        )
        baseline_facts, baseline_result = baseline_future.result()
        constrained_facts, constrained_result = constrained_future.result()
    if constrained_facts.conflicts.count != 0:
        raise SolveServiceError(
            code=ApiErrorCode.MODEL_INVALID,
            message="The policy-constrained plan failed independent conflict reconciliation.",
            details=(
                ApiErrorDetail(
                    path="plans.policy_constrained.metrics.mandatory_policy_conflicts",
                    code="POLICY_CONFLICT",
                    message=f"{constrained_facts.conflicts.count} policy conflicts remain",
                ),
            ),
        )

    heat_shock_plan: Plan | None = None
    shock_facts: PlanFacts | None = None
    shock_result: StagedSolveResult | None = None
    if heat_adjustment_c != 0:
        adjusted_scenario = scenario.model_copy(
            deep=True,
            update={
                "heat_series": adjust_heat_series(
                    scenario.heat_series,
                    heat_adjustment_c,
                    policy.band_thresholds_c,
                )
            },
        )
        shock_facts, shock_result = _solve_facts(
            adjusted_scenario,
            policy,
            per_plan_budget,
            constrained=True,
        )
        if shock_facts.conflicts.count != 0:
            raise SolveServiceError(
                code=ApiErrorCode.MODEL_INVALID,
                message="The heat-shock plan failed independent conflict reconciliation.",
                details=(
                    ApiErrorDetail(
                        path="plans.heat_shock.metrics.mandatory_policy_conflicts",
                        code="POLICY_CONFLICT",
                        message=f"{shock_facts.conflicts.count} policy conflicts remain",
                    ),
                ),
            )
        heat_shock_plan = _to_plan("heat_shock_policy_constrained_plan", shock_facts, shock_result)

    comparison_before = constrained_facts if heat_adjustment_c != 0 else baseline_facts
    comparison_after = shock_facts if heat_adjustment_c != 0 else constrained_facts
    assert comparison_after is not None

    response = SolveResponse(
        scenario=SolveScenario(
            id=scenario.id,
            policy_id=policy.id,
            policy_disclaimer=policy.disclaimer,
            slot_minutes=scenario.slot_minutes,
            heat_adjustment_c=heat_adjustment_c,
        ),
        plans=PlanSet(
            service_first=_to_plan("service_first_counterfactual", baseline_facts, baseline_result),
            policy_constrained=_to_plan(
                "maximum_service_compliant_plan",
                constrained_facts,
                constrained_result,
            ),
            heat_shock=heat_shock_plan,
        ),
        plan_diff=derive_plan_diff(comparison_before, comparison_after),
        diagnostics={
            "baseline_policy_conflict_count": baseline_facts.conflicts.count,
            "baseline_policy_conflict_rule_ids": list(baseline_facts.conflicts.rule_ids),
            "baseline_policy_conflict_job_ids": list(baseline_facts.conflicts.job_ids),
            "policy_constrained_policy_conflict_count": constrained_facts.conflicts.count,
            "heat_shock_policy_conflict_count": shock_facts.conflicts.count if shock_facts else None,
        },
    )
    return response


def _solve_facts(
    scenario: Scenario,
    policy: Policy,
    time_limit_seconds: float,
    *,
    constrained: bool,
) -> tuple[PlanFacts, StagedSolveResult]:
    patterns = (
        generate_policy_constrained_patterns(scenario, policy)
        if constrained
        else generate_baseline_patterns(scenario)
    )
    optimizer_model = build_optimizer_model(
        scenario,
        policy,
        patterns,
        enforce_policy=constrained,
    )
    result = solve_staged(optimizer_model, time_limit_seconds)
    if result.status in (SolverStatus.UNKNOWN, SolverStatus.MODEL_INVALID, SolverStatus.INFEASIBLE):
        if not result.selected_pattern_indices:
            code = {
                SolverStatus.UNKNOWN: ApiErrorCode.SOLVER_TIMEOUT,
                SolverStatus.MODEL_INVALID: ApiErrorCode.MODEL_INVALID,
                SolverStatus.INFEASIBLE: ApiErrorCode.NO_FEASIBLE_PLAN,
            }[result.status]
            raise SolveServiceError(
                code=code,
                message=f"{result.status.value} solve produced no reportable plan.",
            )
    try:
        facts = extract_plan_facts(optimizer_model, result)
    except ModelReconciliationError as error:
        raise SolveServiceError(
            code=ApiErrorCode.MODEL_INVALID,
            message="Solver output failed model reconciliation.",
            details=(ApiErrorDetail(path="solver_result", code="MODEL_RECONCILIATION", message=str(error)),),
        ) from error
    return facts, result


def _to_plan(label: str, facts: PlanFacts, result: StagedSolveResult) -> Plan:
    stages = [
        Stage(
            name=stage.name,
            status=stage.status,
            objective_value=stage.objective_value,
            best_bound=stage.best_bound,
            wall_time_seconds=stage.wall_time_seconds,
        )
        for stage in result.stages
    ]
    return Plan(
        label=label,
        status=result.status,
        maximum_claim_allowed=result.maximum_claim_allowed,
        wall_time_seconds=sum(stage.wall_time_seconds for stage in result.stages),
        stages=stages,
        metrics=facts.metrics,
        timeline_segments=list(facts.timeline_segments),
        route_segments=list(facts.route_segments),
        jobs=list(facts.jobs),
    )
