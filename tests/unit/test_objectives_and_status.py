from __future__ import annotations

from ortools.sat.python import cp_model

import backend.heatshift.optimizer as optimizer
from backend.heatshift.models import SolverStatus, StageName
from backend.heatshift.optimizer import (
    SOLVER_NUM_SEARCH_WORKERS,
    SOLVER_RANDOM_SEED,
    build_optimizer_model,
    map_solver_status,
    solve_staged,
)
from backend.heatshift.patterns import generate_baseline_patterns
from tests.unit.test_patterns import make_case


def test_status_mapping_is_conservative_for_every_solver_value() -> None:
    assert map_solver_status(cp_model.OPTIMAL) is SolverStatus.OPTIMAL
    assert map_solver_status(cp_model.FEASIBLE) is SolverStatus.FEASIBLE
    assert map_solver_status(cp_model.INFEASIBLE) is SolverStatus.INFEASIBLE
    assert map_solver_status(cp_model.UNKNOWN) is SolverStatus.UNKNOWN
    assert map_solver_status(cp_model.MODEL_INVALID) is SolverStatus.MODEL_INVALID
    assert map_solver_status(999999) is SolverStatus.MODEL_INVALID


def make_solved_model():
    scenario, policy = make_case(["normal"] * 8, active_minutes=45)
    model_data = build_optimizer_model(
        scenario,
        policy,
        generate_baseline_patterns(scenario),
        enforce_policy=False,
    )
    return scenario, policy, model_data


def test_all_required_stages_are_fixed_before_lower_objectives_run() -> None:
    scenario, policy, model_data = make_solved_model()
    result = solve_staged(model_data, 5)

    assert [stage.name for stage in result.stages] == [
        StageName.CRITICAL_SERVICE,
        StageName.PLANNED_SERVICE_VALUE,
        StageName.TRAVEL_MINUTES,
        StageName.OVERTIME_MINUTES,
        StageName.STANDALONE_RECOVERY,
    ]
    assert all(stage.status is SolverStatus.OPTIMAL for stage in result.stages)
    assert result.maximum_claim_allowed is True

    selected_jobs = {model_data.patterns[index].job_id for index in result.selected_pattern_indices}
    selected_critical = sum(
        1
        for job in scenario.jobs
        if job.id in selected_jobs and job.priority.value == "critical"
    )
    selected_value = sum(
        job.service_value
        for job in scenario.jobs
        if job.id in selected_jobs
    )
    assert selected_critical == result.stages[0].objective_value
    assert selected_value == result.stages[1].objective_value


def test_zero_budget_returns_null_proof_values_and_no_maximum_claim() -> None:
    _, _, model_data = make_solved_model()
    result = solve_staged(model_data, 0)

    assert result.status is SolverStatus.UNKNOWN
    assert result.maximum_claim_allowed is False
    assert len(result.stages) == 1
    assert result.stages[0].status is SolverStatus.UNKNOWN
    assert result.stages[0].objective_value is None
    assert result.stages[0].best_bound is None


def test_feasible_only_never_allows_maximum_claim(monkeypatch) -> None:
    _, _, model_data = make_solved_model()

    class FakeParameters:
        max_time_in_seconds = 0.0
        random_seed = 0
        num_search_workers = 0
        log_search_progress = True

    class FakeSolver:
        def __init__(self) -> None:
            self.parameters = FakeParameters()

        def Solve(self, model):  # noqa: N802 - mirrors OR-Tools API
            return cp_model.FEASIBLE

        def ObjectiveValue(self):  # noqa: N802 - mirrors OR-Tools API
            return 2.0

        def BestObjectiveBound(self):  # noqa: N802 - mirrors OR-Tools API
            return 3.0

        def Value(self, variable):  # noqa: N802 - mirrors OR-Tools API
            return 0

    monkeypatch.setattr(optimizer, "_configured_solver", lambda remaining: FakeSolver())
    result = solve_staged(model_data, 1)

    assert result.status is SolverStatus.FEASIBLE
    assert result.maximum_claim_allowed is False
    assert len(result.stages) == 1
    assert result.stages[0].objective_value == 2
    assert result.stages[0].best_bound == 3


def test_solver_configuration_is_fixed_for_deterministic_runs() -> None:
    _, _, first_model = make_solved_model()
    _, _, second_model = make_solved_model()
    first = solve_staged(first_model, 5)
    second = solve_staged(second_model, 5)

    assert first.selected_pattern_ids == second.selected_pattern_ids
    assert first.selected_start_arc_ids == second.selected_start_arc_ids
    assert first.selected_route_arc_ids == second.selected_route_arc_ids
    assert first.selected_end_arc_ids == second.selected_end_arc_ids
    assert [(stage.name, stage.status, stage.objective_value, stage.best_bound) for stage in first.stages] == [
        (stage.name, stage.status, stage.objective_value, stage.best_bound)
        for stage in second.stages
    ]
    assert SOLVER_RANDOM_SEED == 7
    assert SOLVER_NUM_SEARCH_WORKERS == 1
