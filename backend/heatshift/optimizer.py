"""CP-SAT model construction for pattern selection and global constraints."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ortools.sat.python import cp_model

from .models import Crew, Job, Policy, Priority, Scenario
from .patterns import ExecutionPattern
from .timegrid import parse_time, travel_to_slots


@dataclass(slots=True)
class ObjectiveExpressions:
    """Linear expressions exposed for the staged solver in B07."""

    critical_service: Any
    planned_service_value: Any
    travel_minutes: Any
    overtime_minutes: Any
    standalone_recovery: Any


@dataclass(slots=True)
class OptimizerModel:
    """CP-SAT model plus deterministic handles for every decision family."""

    model: cp_model.CpModel
    scenario: Scenario
    policy: Policy
    patterns: tuple[ExecutionPattern, ...]
    enforce_policy: bool
    x: tuple[Any, ...]
    serve: dict[str, Any]
    crew_used: dict[str, Any]
    start_arc: dict[int, Any]
    route_arc: dict[tuple[int, int], Any]
    end_arc: dict[int, Any]
    standalone_recovery: dict[tuple[str, int], Any]
    objective_expressions: ObjectiveExpressions
    occupancy_expressions: dict[tuple[str, int], Any]
    start_travel_slots: dict[int, tuple[int, ...]]
    route_travel_slots: dict[tuple[int, int], tuple[int, ...]]
    end_travel_slots: dict[int, tuple[int, ...]]
    arc_travel_minutes: dict[tuple[str, int, int | None], int]

    @property
    def pattern_vars(self) -> tuple[Any, ...]:
        """Descriptive alias for the pattern-selection variables."""

        return self.x


def build_optimizer_model(
    scenario: Scenario,
    policy: Policy,
    patterns: list[ExecutionPattern] | tuple[ExecutionPattern, ...],
    *,
    enforce_policy: bool = True,
) -> OptimizerModel:
    """Build a solver model from validated inputs and sorted patterns.

    This function only constructs the CP-SAT model. It does not call a solver,
    read fixtures, or create API response objects.
    """

    ordered_patterns = tuple(
        sorted(
            patterns,
            key=lambda pattern: (
                pattern.job_id,
                pattern.crew_id,
                pattern.start_slot,
                pattern.end_slot,
                pattern.pattern_id,
            ),
        )
    )
    pattern_ids = [pattern.pattern_id for pattern in ordered_patterns]
    if len(pattern_ids) != len(set(pattern_ids)):
        raise ValueError("pattern IDs must be unique before model construction")

    model = cp_model.CpModel()
    jobs = {job.id: job for job in scenario.jobs}
    crews = {crew.id: crew for crew in scenario.crews}
    if len(jobs) != len(scenario.jobs) or len(crews) != len(scenario.crews):
        raise ValueError("scenario IDs must be unique before model construction")

    horizon_slots = _horizon_slots(scenario)
    matrix_index = {
        location_id: index
        for index, location_id in enumerate(scenario.travel_matrix_location_ids)
    }

    x = tuple(
        model.NewBoolVar(f"select_{index}_{pattern.pattern_id}")
        for index, pattern in enumerate(ordered_patterns)
    )
    serve = {
        job_id: model.NewBoolVar(f"serve_{job_id}")
        for job_id in sorted(jobs)
    }
    crew_used = {
        crew_id: model.NewBoolVar(f"crew_used_{crew_id}")
        for crew_id in sorted(crews)
    }

    patterns_by_job: dict[str, list[int]] = defaultdict(list)
    patterns_by_crew: dict[str, list[int]] = defaultdict(list)
    for index, pattern in enumerate(ordered_patterns):
        if pattern.job_id not in jobs:
            raise ValueError(f"pattern references unknown job {pattern.job_id!r}")
        if pattern.crew_id not in crews:
            raise ValueError(f"pattern references unknown crew {pattern.crew_id!r}")
        patterns_by_job[pattern.job_id].append(index)
        patterns_by_crew[pattern.crew_id].append(index)

    for job_id, job in jobs.items():
        model.Add(serve[job_id] == sum(x[index] for index in patterns_by_job[job_id]))
        if job.locked:
            model.Add(serve[job_id] == 1)

    for index, pattern in enumerate(ordered_patterns):
        job = jobs[pattern.job_id]
        if job.locked_crew_id is not None and pattern.crew_id != job.locked_crew_id:
            model.Add(x[index] == 0)
        if job.locked_start is not None:
            locked_start = _time_to_slot(job.locked_start, scenario)
            if pattern.start_slot != locked_start:
                model.Add(x[index] == 0)
        model.Add(crew_used[pattern.crew_id] >= x[index])

    start_arc: dict[int, Any] = {}
    route_arc: dict[tuple[int, int], Any] = {}
    end_arc: dict[int, Any] = {}
    start_travel_slots: dict[int, tuple[int, ...]] = {}
    route_travel_slots: dict[tuple[int, int], tuple[int, ...]] = {}
    end_travel_slots: dict[int, tuple[int, ...]] = {}
    arc_travel_minutes: dict[tuple[str, int, int | None], int] = {}

    for index, pattern in enumerate(ordered_patterns):
        start_slots = _start_travel_slots(scenario, crews[pattern.crew_id], pattern, matrix_index)
        if start_slots is not None:
            start_arc[index] = model.NewBoolVar(f"start_arc_{index}")
            start_travel_slots[index] = start_slots
            arc_travel_minutes[("start", index, None)] = _matrix_value(
                scenario,
                matrix_index,
                crews[pattern.crew_id].start_depot_id,
                pattern.location_id,
            )
        end_slots = _end_travel_slots(scenario, crews[pattern.crew_id], pattern, matrix_index)
        if end_slots is not None:
            end_arc[index] = model.NewBoolVar(f"end_arc_{index}")
            end_travel_slots[index] = end_slots
            arc_travel_minutes[("end", index, None)] = _matrix_value(
                scenario,
                matrix_index,
                pattern.location_id,
                crews[pattern.crew_id].end_depot_id,
            )

    for left_index, left in enumerate(ordered_patterns):
        for right_index, right in enumerate(ordered_patterns):
            if left_index == right_index or left.crew_id != right.crew_id:
                continue
            if left.job_id == right.job_id:
                continue
            travel_minutes = _matrix_value(
                scenario,
                matrix_index,
                left.location_id,
                right.location_id,
            )
            travel_slots = travel_to_slots(travel_minutes, scenario.slot_minutes)
            if left.end_slot + travel_slots > right.start_slot:
                continue
            key = (left_index, right_index)
            route_arc[key] = model.NewBoolVar(f"route_arc_{left_index}_{right_index}")
            route_travel_slots[key] = tuple(
                range(right.start_slot - travel_slots, right.start_slot)
            )
            arc_travel_minutes[("route", left_index, right_index)] = travel_minutes

    for index, pattern in enumerate(ordered_patterns):
        incoming = [start_arc[index]] + [
            variable
            for (left_index, right_index), variable in route_arc.items()
            if right_index == index
        ]
        outgoing = [end_arc[index]] + [
            variable
            for (left_index, right_index), variable in route_arc.items()
            if left_index == index
        ]
        model.Add(sum(incoming) == x[index])
        model.Add(sum(outgoing) == x[index])

    for crew_id in sorted(crews):
        model.Add(
            sum(variable for index, variable in start_arc.items() if ordered_patterns[index].crew_id == crew_id)
            == crew_used[crew_id]
        )
        model.Add(
            sum(variable for index, variable in end_arc.items() if ordered_patterns[index].crew_id == crew_id)
            == crew_used[crew_id]
        )

    standalone_recovery: dict[tuple[str, int], Any] = {}
    for crew_id in sorted(crews):
        crew = crews[crew_id]
        for slot in range(horizon_slots):
            variable = model.NewBoolVar(f"standalone_recovery_{crew_id}_{slot}")
            standalone_recovery[(crew_id, slot)] = variable
            if not _slot_inside_crew_availability(scenario, crew, slot):
                model.Add(variable == 0)
            if crew.recovery_profile not in policy.eligible_recovery_profiles:
                model.Add(variable == 0)

    occupancy_terms: dict[tuple[str, int], list[Any]] = defaultdict(list)
    for index, pattern in enumerate(ordered_patterns):
        for slot in pattern.work_slots:
            occupancy_terms[(pattern.crew_id, slot)].append(x[index])
        for slot in pattern.committed_recovery_slots:
            occupancy_terms[(pattern.crew_id, slot)].append(x[index])
    for index, slots in start_travel_slots.items():
        for slot in slots:
            occupancy_terms[(ordered_patterns[index].crew_id, slot)].append(start_arc[index])
    for (left_index, right_index), slots in route_travel_slots.items():
        crew_id = ordered_patterns[left_index].crew_id
        for slot in slots:
            occupancy_terms[(crew_id, slot)].append(route_arc[(left_index, right_index)])
    for index, slots in end_travel_slots.items():
        for slot in slots:
            occupancy_terms[(ordered_patterns[index].crew_id, slot)].append(end_arc[index])
    for key, variable in standalone_recovery.items():
        occupancy_terms[key].append(variable)

    occupancy_expressions: dict[tuple[str, int], Any] = {}
    for crew_id in sorted(crews):
        for slot in range(horizon_slots):
            expression = sum(occupancy_terms[(crew_id, slot)])
            occupancy_expressions[(crew_id, slot)] = expression
            model.Add(expression <= 1)

    if enforce_policy:
        _add_global_policy_constraints(
            model,
            scenario,
            policy,
            ordered_patterns,
            x,
            standalone_recovery,
            horizon_slots,
        )

    objective_expressions = ObjectiveExpressions(
        critical_service=sum(
            serve[job_id]
            for job_id, job in jobs.items()
            if job.priority is Priority.CRITICAL
        ),
        planned_service_value=sum(
            job.service_value * serve[job_id]
            for job_id, job in jobs.items()
        ),
        travel_minutes=_travel_objective(
            scenario,
            crews,
            ordered_patterns,
            start_arc,
            route_arc,
            end_arc,
            matrix_index,
        ),
        overtime_minutes=_overtime_objective(
            scenario,
            crews,
            ordered_patterns,
            end_arc,
        ),
        standalone_recovery=sum(standalone_recovery.values()),
    )

    return OptimizerModel(
        model=model,
        scenario=scenario,
        policy=policy,
        patterns=ordered_patterns,
        enforce_policy=enforce_policy,
        x=x,
        serve=serve,
        crew_used=crew_used,
        start_arc=start_arc,
        route_arc=route_arc,
        end_arc=end_arc,
        standalone_recovery=standalone_recovery,
        objective_expressions=objective_expressions,
        occupancy_expressions=occupancy_expressions,
        start_travel_slots=start_travel_slots,
        route_travel_slots=route_travel_slots,
        end_travel_slots=end_travel_slots,
        arc_travel_minutes=arc_travel_minutes,
    )


def build_model(
    scenario: Scenario,
    policy: Policy,
    patterns: list[ExecutionPattern] | tuple[ExecutionPattern, ...],
    *,
    enforce_policy: bool = True,
) -> OptimizerModel:
    """Short alias for callers that use the packet's model terminology."""

    return build_optimizer_model(
        scenario,
        policy,
        patterns,
        enforce_policy=enforce_policy,
    )


def _add_global_policy_constraints(
    model: cp_model.CpModel,
    scenario: Scenario,
    policy: Policy,
    patterns: tuple[ExecutionPattern, ...],
    x: tuple[Any, ...],
    standalone_recovery: dict[tuple[str, int], Any],
    horizon_slots: int,
) -> None:
    rolling_slots = policy.rolling_window_slots
    if rolling_slots <= 0:
        raise ValueError("policy rolling_window_slots must be positive")
    rules_by_id = {rule.id: rule for rule in policy.rules}
    crew_ids = sorted({pattern.crew_id for pattern in patterns} | set(standalone_id for standalone_id, _ in standalone_recovery))

    for crew_id in crew_ids:
        crew_pattern_indices = [
            index for index, pattern in enumerate(patterns) if pattern.crew_id == crew_id
        ]
        for window_start in range(0, horizon_slots - rolling_slots + 1):
            window = set(range(window_start, window_start + rolling_slots))
            work_terms = [
                x[index]
                for index in crew_pattern_indices
                for slot in patterns[index].work_slots
                if slot in window
            ]
            recovery_terms = [
                x[index]
                for index in crew_pattern_indices
                for slot in patterns[index].committed_recovery_slots
                if slot in window
            ] + [
                standalone_recovery[(crew_id, slot)]
                for slot in window
            ]
            work_expression = sum(work_terms)
            recovery_expression = sum(recovery_terms)

            for index in crew_pattern_indices:
                triggered_rule_ids = {
                    rule_id
                    for slot, rule_ids in patterns[index].rule_ids_by_work_slot
                    if slot in window
                    for rule_id in rule_ids
                }
                for rule_id in sorted(triggered_rule_ids):
                    try:
                        rule = rules_by_id[rule_id]
                    except KeyError as error:
                        raise ValueError(f"pattern references unknown policy rule {rule_id!r}") from error
                    model.Add(work_expression <= rule.max_active_slots).OnlyEnforceIf(x[index])
                    model.Add(recovery_expression >= rule.min_recovery_slots).OnlyEnforceIf(x[index])


def _travel_objective(
    scenario: Scenario,
    crews: dict[str, Crew],
    patterns: tuple[ExecutionPattern, ...],
    start_arc: dict[int, Any],
    route_arc: dict[tuple[int, int], Any],
    end_arc: dict[int, Any],
    matrix_index: dict[str, int],
) -> Any:
    terms: list[Any] = []
    for index, variable in start_arc.items():
        pattern = patterns[index]
        terms.append(
            _matrix_value(scenario, matrix_index, crews[pattern.crew_id].start_depot_id, pattern.location_id)
            * variable
        )
    for (left_index, right_index), variable in route_arc.items():
        terms.append(
            _matrix_value(scenario, matrix_index, patterns[left_index].location_id, patterns[right_index].location_id)
            * variable
        )
    for index, variable in end_arc.items():
        pattern = patterns[index]
        terms.append(
            _matrix_value(scenario, matrix_index, pattern.location_id, crews[pattern.crew_id].end_depot_id)
            * variable
        )
    return sum(terms)


def _overtime_objective(
    scenario: Scenario,
    crews: dict[str, Crew],
    patterns: tuple[ExecutionPattern, ...],
    end_arc: dict[int, Any],
) -> Any:
    day_start = parse_time(scenario.day_start)
    terms: list[Any] = []
    matrix_index = {
        location_id: index
        for index, location_id in enumerate(scenario.travel_matrix_location_ids)
    }
    for index, variable in end_arc.items():
        pattern = patterns[index]
        crew = crews[pattern.crew_id]
        return_travel = _matrix_value(
            scenario,
            matrix_index,
            pattern.location_id,
            crew.end_depot_id,
        )
        return_minutes = day_start + pattern.end_slot * scenario.slot_minutes + return_travel
        overtime = max(0, return_minutes - parse_time(crew.shift_end))
        terms.append(overtime * variable)
    return sum(terms)


def _start_travel_slots(
    scenario: Scenario,
    crew: Crew,
    pattern: ExecutionPattern,
    matrix_index: dict[str, int],
) -> tuple[int, ...] | None:
    travel_minutes = _matrix_value(
        scenario,
        matrix_index,
        crew.start_depot_id,
        pattern.location_id,
    )
    travel_slots = travel_to_slots(travel_minutes, scenario.slot_minutes)
    day_start = parse_time(scenario.day_start)
    pattern_start = day_start + pattern.start_slot * scenario.slot_minutes
    earliest_departure = max(day_start, parse_time(crew.shift_start))
    if pattern_start < earliest_departure + travel_minutes:
        return None
    first_slot = pattern.start_slot - travel_slots
    if first_slot < 0:
        return None
    return tuple(range(first_slot, pattern.start_slot))


def _end_travel_slots(
    scenario: Scenario,
    crew: Crew,
    pattern: ExecutionPattern,
    matrix_index: dict[str, int],
) -> tuple[int, ...] | None:
    travel_minutes = _matrix_value(
        scenario,
        matrix_index,
        pattern.location_id,
        crew.end_depot_id,
    )
    travel_slots = travel_to_slots(travel_minutes, scenario.slot_minutes)
    day_start = parse_time(scenario.day_start)
    day_end = parse_time(scenario.day_end)
    return_time = day_start + pattern.end_slot * scenario.slot_minutes + travel_minutes
    latest_crew_end = min(day_end, parse_time(crew.shift_end) + crew.max_overtime_minutes)
    if return_time > latest_crew_end:
        return None
    horizon_slots = _horizon_slots(scenario)
    if pattern.end_slot + travel_slots > horizon_slots:
        return None
    return tuple(range(pattern.end_slot, pattern.end_slot + travel_slots))


def _slot_inside_crew_availability(scenario: Scenario, crew: Crew, slot: int) -> bool:
    day_start = parse_time(scenario.day_start)
    slot_start = day_start + slot * scenario.slot_minutes
    slot_end = slot_start + scenario.slot_minutes
    latest_crew_end = min(
        parse_time(scenario.day_end),
        parse_time(crew.shift_end) + crew.max_overtime_minutes,
    )
    return slot_start >= parse_time(crew.shift_start) and slot_end <= latest_crew_end


def _horizon_slots(scenario: Scenario) -> int:
    horizon_minutes = parse_time(scenario.day_end) - parse_time(scenario.day_start)
    if scenario.slot_minutes <= 0 or horizon_minutes <= 0 or horizon_minutes % scenario.slot_minutes:
        raise ValueError("scenario must have a positive, slot-aligned planning horizon")
    return horizon_minutes // scenario.slot_minutes


def _time_to_slot(value: str, scenario: Scenario) -> int:
    elapsed = parse_time(value) - parse_time(scenario.day_start)
    if elapsed < 0 or elapsed % scenario.slot_minutes:
        raise ValueError(f"time {value!r} is not aligned to the scenario grid")
    return elapsed // scenario.slot_minutes


def _matrix_value(
    scenario: Scenario,
    matrix_index: dict[str, int],
    from_location_id: str,
    to_location_id: str,
) -> int:
    try:
        return scenario.travel_matrix_minutes[matrix_index[from_location_id]][matrix_index[to_location_id]]
    except (KeyError, IndexError) as error:
        raise ValueError("scenario travel matrix must be validated before model construction") from error
