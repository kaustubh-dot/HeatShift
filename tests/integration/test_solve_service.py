from __future__ import annotations

import pytest

from backend.heatshift.models import SolveRequest
from backend.heatshift.service import SolveServiceError, solve_scenario
from tests.unit.test_patterns import make_case


def test_solve_service_returns_canonical_zero_adjustment_response() -> None:
    scenario, policy = make_case(["normal"] * 8, active_minutes=45)
    response = solve_scenario(scenario, policy, heat_adjustment_c=0, time_limit_seconds=5)

    assert response.scenario.id == scenario.id
    assert response.scenario.policy_id == policy.id
    assert response.scenario.policy_disclaimer == policy.disclaimer
    assert response.plans.heat_shock is None
    assert response.plans.service_first.metrics.active_work_minutes == 45
    assert response.plans.policy_constrained.metrics.mandatory_policy_conflicts == 0
    assert response.plans.service_first.metrics.planned_service_value == 8
    assert len(response.plan_diff) == len(scenario.jobs)
    assert response.plan_diff[0].job_id == scenario.jobs[0].id
    assert response.plan_diff[0].change.value == "moved_time"
    assert response.plan_diff[0].before is not None
    assert response.plan_diff[0].after is not None
    assert response.model_validate(response.model_dump(mode="json")) == response


def test_solve_service_evaluates_baseline_conflicts_independently() -> None:
    scenario, policy = make_case(["elevated"] * 8, active_minutes=45)
    response = solve_scenario(scenario, policy, heat_adjustment_c=0, time_limit_seconds=5)

    assert response.plans.service_first.metrics.mandatory_policy_conflicts > 0
    assert response.plans.policy_constrained.metrics.mandatory_policy_conflicts == 0
    assert response.diagnostics["baseline_policy_conflict_count"] == response.plans.service_first.metrics.mandatory_policy_conflicts


def test_solve_service_accepts_request_model_and_keeps_shock_separate() -> None:
    scenario, policy = make_case(["normal", "elevated", "elevated", "normal", "normal", "normal", "normal", "normal"], active_minutes=45)
    original_heat = scenario.model_dump(mode="json")["heat_series"]
    request = SolveRequest(
        scenario=scenario,
        policy=policy,
        heat_adjustment_c=2,
        time_limit_seconds=5,
    )
    response = solve_scenario(request)

    assert response.scenario.heat_adjustment_c == 2
    assert response.plans.heat_shock is not None
    assert response.plans.service_first is not response.plans.heat_shock
    assert scenario.model_dump(mode="json")["heat_series"] == original_heat
    assert response.plans.policy_constrained.metrics.mandatory_policy_conflicts == 0
    assert response.plans.heat_shock.metrics.mandatory_policy_conflicts == 0


def test_invalid_cross_reference_stops_before_solving() -> None:
    scenario, policy = make_case(["normal"] * 8, active_minutes=45)
    scenario.jobs[0].location_id = "missing-location"

    with pytest.raises(SolveServiceError) as caught:
        solve_scenario(scenario, policy, heat_adjustment_c=0, time_limit_seconds=5)

    assert caught.value.code.value == "INVALID_SCENARIO"
    assert caught.value.details[0].path == "jobs[0].location_id"


def test_timeout_from_parallel_branch_preserves_service_error() -> None:
    scenario, policy = make_case(["normal"] * 8, active_minutes=45)

    with pytest.raises(SolveServiceError) as caught:
        solve_scenario(scenario, policy, heat_adjustment_c=0, time_limit_seconds=0)

    assert caught.value.code.value == "SOLVER_TIMEOUT"
