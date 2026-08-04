from __future__ import annotations

from ortools.sat.python import cp_model

from backend.heatshift.models import Policy, Scenario
from backend.heatshift.optimizer import build_optimizer_model
from backend.heatshift.patterns import (
    generate_baseline_patterns,
    generate_policy_constrained_patterns,
)
from tests.unit.test_patterns import make_case


def solve(model_data):
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 7
    solver.parameters.max_time_in_seconds = 2
    status = solver.Solve(model_data.model)
    return solver, status


def test_pattern_selection_has_no_double_selection_and_keeps_eligibility() -> None:
    scenario, policy = make_case(["normal"] * 9, active_minutes=45)
    patterns = generate_baseline_patterns(scenario)
    model_data = build_optimizer_model(scenario, policy, patterns, enforce_policy=False)
    model_data.model.Maximize(model_data.objective_expressions.planned_service_value)
    solver, status = solve(model_data)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    for job_id, variable in model_data.serve.items():
        selected = [
            index
            for index, pattern in enumerate(model_data.patterns)
            if pattern.job_id == job_id and solver.Value(model_data.x[index])
        ]
        assert len(selected) <= 1
        assert solver.Value(variable) == len(selected)
    assert {pattern.crew_id for index, pattern in enumerate(model_data.patterns) if solver.Value(model_data.x[index])} == {
        "crew-a"
    }


def test_overlapping_patterns_cannot_double_occupy_a_crew_slot() -> None:
    scenario, policy = make_case(["normal"] * 9, active_minutes=60)
    scenario.jobs.append(scenario.jobs[0].model_copy(update={"id": "job-b", "name": "Job B"}))
    patterns = generate_baseline_patterns(scenario)
    model_data = build_optimizer_model(scenario, policy, patterns, enforce_policy=False)
    solver, status = solve(model_data)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    for slot in range(9):
        selected = [
            index
            for index, pattern in enumerate(model_data.patterns)
            if pattern.crew_id == "crew-a"
            and slot in pattern.work_slots + pattern.committed_recovery_slots
            and solver.Value(model_data.x[index])
        ]
        assert len(selected) <= 1
        assert solver.Value(model_data.occupancy_expressions[("crew-a", slot)]) <= 1


def test_route_flow_connects_selected_patterns_to_start_and_end_depots() -> None:
    scenario, policy = make_case(["normal"] * 12, active_minutes=30)
    scenario.jobs.append(
        scenario.jobs[0].model_copy(
            update={
                "id": "job-b",
                "name": "Job B",
                "window_start": "08:30",
                "window_end": "10:00",
            }
        )
    )
    patterns = generate_baseline_patterns(scenario)
    model_data = build_optimizer_model(scenario, policy, patterns, enforce_policy=False)
    solver, status = solve(model_data)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    for index, pattern in enumerate(model_data.patterns):
        if not solver.Value(model_data.x[index]):
            continue
        incoming = solver.Value(model_data.start_arc[index]) if index in model_data.start_arc else 0
        incoming += sum(
            solver.Value(variable)
            for (left_index, right_index), variable in model_data.route_arc.items()
            if right_index == index
        )
        outgoing = solver.Value(model_data.end_arc[index]) if index in model_data.end_arc else 0
        outgoing += sum(
            solver.Value(variable)
            for (left_index, right_index), variable in model_data.route_arc.items()
            if left_index == index
        )
        assert incoming == 1
        assert outgoing == 1


def test_directed_travel_uses_ceiling_reserved_slots_for_route_arcs() -> None:
    scenario, policy = make_case(["normal"] * 12, active_minutes=15)
    scenario.jobs.append(
        scenario.jobs[0].model_copy(
            update={
                "id": "job-b",
                "name": "Job B",
                "location_id": "loc-job-b",
                "window_start": "08:00",
                "window_end": "09:00",
            }
        )
    )
    scenario.locations.append({"id": "loc-job-b", "coordinates": [2, 2]})
    scenario.travel_matrix_location_ids = ["depot-central", "loc-job", "loc-job-b"]
    scenario.travel_matrix_minutes = [
        [0, 14, 14],
        [14, 0, 16],
        [14, 16, 0],
    ]
    patterns = generate_baseline_patterns(scenario)
    model_data = build_optimizer_model(scenario, policy, patterns, enforce_policy=False)

    left = next(index for index, pattern in enumerate(model_data.patterns) if pattern.job_id == "job-a" and pattern.start_slot == 1)
    right = next(index for index, pattern in enumerate(model_data.patterns) if pattern.job_id == "job-b" and pattern.start_slot == 4)
    assert (left, right) in model_data.route_arc
    assert model_data.route_travel_slots[(left, right)] == (2, 3)
    assert model_data.arc_travel_minutes[("route", left, right)] == 16


def test_consecutive_locally_valid_jobs_are_rejected_by_global_policy() -> None:
    scenario, policy = make_case(["elevated"] * 8, active_minutes=30)
    scenario.jobs[0].locked = True
    scenario.jobs[0].locked_start = "07:15"
    scenario.jobs.append(
        scenario.jobs[0].model_copy(
            update={
                "id": "job-b",
                "name": "Job B",
                "locked_start": "07:45",
                "window_start": "07:45",
                "window_end": "09:00",
            }
        )
    )
    patterns = generate_policy_constrained_patterns(scenario, policy)
    model_data = build_optimizer_model(scenario, policy, patterns)
    _, status = solve(model_data)
    assert status == cp_model.INFEASIBLE


def test_travel_does_not_count_as_recovery_for_global_policy() -> None:
    scenario, policy = make_case(["elevated"] * 7, active_minutes=45)
    scenario.jobs[0].locked = True
    scenario.jobs[0].locked_start = "07:15"
    model_data = build_optimizer_model(
        scenario,
        policy,
        generate_policy_constrained_patterns(scenario, policy),
    )
    _, status = solve(model_data)
    assert status == cp_model.INFEASIBLE


def test_stop_work_slots_have_no_active_work_in_selected_patterns() -> None:
    scenario, policy = make_case(
        ["normal", "normal", "extreme", "normal", "normal", "normal", "normal"],
        active_minutes=45,
    )
    patterns = generate_policy_constrained_patterns(scenario, policy)
    assert patterns
    assert all(2 not in pattern.work_slots for pattern in patterns)


def test_locked_crew_and_start_dimensions_are_preserved() -> None:
    scenario, policy = make_case(["normal"] * 9, active_minutes=45, locked_start_slot=4)
    scenario.jobs[0].locked = True
    scenario.jobs[0].locked_crew_id = "crew-a"
    model_data = build_optimizer_model(
        scenario,
        policy,
        generate_policy_constrained_patterns(scenario, policy),
    )
    solver, status = solve(model_data)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    selected = [
        pattern
        for index, pattern in enumerate(model_data.patterns)
        if solver.Value(model_data.x[index])
    ]
    assert len(selected) == 1
    assert selected[0].crew_id == "crew-a"
    assert selected[0].start_slot == 4
