from __future__ import annotations

from backend.heatshift.diagnostics import diagnose_job
from backend.heatshift.metrics import extract_plan_facts
from backend.heatshift.models import InterventionType, SolverStatus
from backend.heatshift.optimizer import build_optimizer_model, solve_staged
from backend.heatshift.patterns import generate_policy_constrained_patterns
from tests.unit.test_patterns import make_case


def _solve_original(scenario, policy):
    model = build_optimizer_model(
        scenario,
        policy,
        generate_policy_constrained_patterns(scenario, policy),
        enforce_policy=True,
    )
    result = solve_staged(model, 5)
    return extract_plan_facts(model, result), result


def test_catalogue_runs_all_candidates_in_declared_order_from_original_input() -> None:
    scenario, policy = make_case(
        ["normal"] * 8,
        active_minutes=45,
        window_start_slot=1,
        window_end_slot=2,
    )
    original_window_end = scenario.jobs[0].window_end
    original_overtime = scenario.crews[0].max_overtime_minutes
    original_facts, original_result = _solve_original(scenario, policy)

    diagnosis = diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        "job-a",
        time_limit_seconds=5,
    )

    interventions = diagnosis.tested_interventions
    assert [(item.type, item.value_minutes) for item in interventions] == [
        (InterventionType.DEADLINE_EXTENSION, 15),
        (InterventionType.DEADLINE_EXTENSION, 30),
        (InterventionType.OVERTIME_ALLOWANCE, 15),
        (InterventionType.OVERTIME_ALLOWANCE, 30),
    ]
    assert [item.status for item in interventions] == [
        SolverStatus.INFEASIBLE,
        SolverStatus.OPTIMAL,
        SolverStatus.INFEASIBLE,
        SolverStatus.INFEASIBLE,
    ]
    assert interventions[1].objective_delta.planned_service_value == 8
    assert scenario.jobs[0].window_end == original_window_end
    assert scenario.crews[0].max_overtime_minutes == original_overtime


def test_interventions_are_reported_even_when_main_forced_solve_is_not_proven() -> None:
    scenario, policy = make_case(
        ["normal"] * 8,
        active_minutes=45,
        window_start_slot=1,
        window_end_slot=2,
    )
    original_facts, original_result = _solve_original(scenario, policy)

    diagnosis = diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        "job-a",
        time_limit_seconds=0,
    )

    assert diagnosis.proof_status is SolverStatus.UNKNOWN
    assert len(diagnosis.tested_interventions) == 4
