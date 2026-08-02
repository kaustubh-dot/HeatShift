"""Extraction, serialization facts, and independent policy reconciliation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .models import (
    Crew,
    Exertion,
    JobResult,
    Metrics,
    Policy,
    PolicyRule,
    Priority,
    RouteSegment,
    Scenario,
    TimelineSegment,
    TimelineState,
)
from .optimizer import OptimizerModel, StagedSolveResult
from .patterns import ExecutionPattern
from .timegrid import format_time, parse_time, slot_to_time


class ModelReconciliationError(ValueError):
    """Raised when selected solver facts cannot form a coherent plan."""


@dataclass(frozen=True, slots=True)
class PolicyConflict:
    crew_id: str
    window_start_slot: int
    window_end_slot: int
    rule_ids: tuple[str, ...]
    job_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConflictEvidence:
    count: int
    rule_ids: tuple[str, ...]
    job_ids: tuple[str, ...]
    conflicts: tuple[PolicyConflict, ...]


@dataclass(frozen=True, slots=True)
class PlanFacts:
    """Canonical plan facts before B09 adds labels, stages, and status."""

    scenario: Scenario
    policy: Policy
    selected_pattern_indices: tuple[int, ...]
    selected_pattern_ids: tuple[str, ...]
    jobs: tuple[JobResult, ...]
    timeline_segments: tuple[TimelineSegment, ...]
    route_segments: tuple[RouteSegment, ...]
    metrics: Metrics
    conflicts: ConflictEvidence


@dataclass(frozen=True, slots=True)
class _SlotFact:
    crew_id: str
    slot: int
    state: TimelineState
    job_id: str | None = None
    location_id: str | None = None
    exertion: Exertion | None = None
    policy_rule_ids: tuple[str, ...] = ()


def extract_plan_facts(
    optimizer_model: OptimizerModel,
    solve_result: StagedSolveResult,
) -> PlanFacts:
    """Extract selected patterns, route order, timeline, jobs, and metrics."""

    selected_indices = tuple(sorted(solve_result.selected_pattern_indices))
    patterns = optimizer_model.patterns
    if any(index < 0 or index >= len(patterns) for index in selected_indices):
        raise ModelReconciliationError("solver result references an unknown pattern index")
    selected_set = set(selected_indices)
    orders = _build_route_orders(optimizer_model, solve_result, selected_set)
    route_segments = _build_route_segments(optimizer_model, orders)
    slot_facts = _paint_slots(optimizer_model, solve_result, selected_set)
    timeline_segments = _merge_timeline_segments(optimizer_model.scenario, slot_facts)
    jobs = _build_job_results(optimizer_model.scenario, patterns, selected_indices)
    conflicts = evaluate_policy_conflicts(
        optimizer_model.scenario,
        optimizer_model.policy,
        timeline_segments,
    )
    metrics = _compute_metrics(
        optimizer_model.scenario,
        jobs,
        timeline_segments,
        route_segments,
        conflicts,
    )
    facts = PlanFacts(
        scenario=optimizer_model.scenario,
        policy=optimizer_model.policy,
        selected_pattern_indices=selected_indices,
        selected_pattern_ids=tuple(patterns[index].pattern_id for index in selected_indices),
        jobs=jobs,
        timeline_segments=timeline_segments,
        route_segments=route_segments,
        metrics=metrics,
        conflicts=conflicts,
    )
    reconcile_plan_facts(facts)
    return facts


def reconcile_plan_facts(facts: PlanFacts) -> None:
    """Recompute serialized metrics and conflicts and reject any mismatch."""

    recalculated_conflicts = evaluate_policy_conflicts(
        facts.scenario,
        facts.policy,
        facts.timeline_segments,
    )
    if recalculated_conflicts != facts.conflicts:
        raise ModelReconciliationError("serialized policy conflict evidence does not reconcile")
    recalculated_metrics = _compute_metrics(
        facts.scenario,
        facts.jobs,
        facts.timeline_segments,
        facts.route_segments,
        recalculated_conflicts,
    )
    if recalculated_metrics != facts.metrics:
        raise ModelReconciliationError("serialized metrics do not reconcile with extracted facts")


def evaluate_policy_conflicts(
    scenario: Scenario,
    policy: Policy,
    timeline_segments: Iterable[TimelineSegment],
) -> ConflictEvidence:
    """Independently evaluate every full heat-policy window from timeline facts."""

    slot_facts = _slot_facts_from_segments(scenario, timeline_segments)
    heat_by_slot = {heat_slot.slot: heat_slot for heat_slot in scenario.heat_series}
    rules_by_pair: dict[tuple[str, Exertion], tuple[PolicyRule, ...]] = defaultdict(tuple)
    mutable_rules: dict[tuple[str, Exertion], list[PolicyRule]] = defaultdict(list)
    for rule in policy.rules:
        mutable_rules[(_value(rule.band), rule.exertion)].append(rule)
    rules_by_pair = {key: tuple(value) for key, value in mutable_rules.items()}
    horizon_slots = _horizon_slots(scenario)
    rolling_slots = policy.rolling_window_slots
    if rolling_slots <= 0:
        raise ModelReconciliationError("policy rolling_window_slots must be positive")

    conflicts: list[PolicyConflict] = []
    for crew in sorted(scenario.crews, key=lambda item: item.id):
        for window_start in range(0, horizon_slots - rolling_slots + 1):
            window_slots = range(window_start, window_start + rolling_slots)
            work_facts = [
                slot_facts[(crew.id, slot)]
                for slot in window_slots
                if slot_facts[(crew.id, slot)].state is TimelineState.WORK
            ]
            if not work_facts:
                continue
            triggered_rules: dict[str, PolicyRule] = {}
            for fact in work_facts:
                if fact.exertion is None:
                    raise ModelReconciliationError(
                        f"work slot {crew.id}[{fact.slot}] has no exertion"
                    )
                try:
                    heat_band = _value(heat_by_slot[fact.slot].band)
                except KeyError as error:
                    raise ModelReconciliationError(
                        f"timeline references missing heat slot {fact.slot}"
                    ) from error
                for rule in rules_by_pair.get((heat_band, fact.exertion), ()):
                    triggered_rules[rule.id] = rule

            recovery_count = sum(
                slot_facts[(crew.id, slot)].state is TimelineState.RECOVERY
                for slot in window_slots
            )
            active_count = len(work_facts)
            failed_rules = [
                rule
                for rule in triggered_rules.values()
                if active_count > rule.max_active_slots
                or recovery_count < rule.min_recovery_slots
                or rule.stop_work
            ]
            if failed_rules:
                conflicts.append(
                    PolicyConflict(
                        crew_id=crew.id,
                        window_start_slot=window_start,
                        window_end_slot=window_start + rolling_slots,
                        rule_ids=tuple(sorted(rule.id for rule in failed_rules)),
                        job_ids=tuple(sorted({fact.job_id for fact in work_facts if fact.job_id})),
                    )
                )

    rule_ids = tuple(sorted({rule_id for conflict in conflicts for rule_id in conflict.rule_ids}))
    job_ids = tuple(sorted({job_id for conflict in conflicts for job_id in conflict.job_ids}))
    return ConflictEvidence(
        count=len(conflicts),
        rule_ids=rule_ids,
        job_ids=job_ids,
        conflicts=tuple(conflicts),
    )


def _build_route_orders(
    optimizer_model: OptimizerModel,
    solve_result: StagedSolveResult,
    selected_set: set[int],
) -> dict[str, tuple[int, ...]]:
    patterns = optimizer_model.patterns
    starts = set(solve_result.selected_start_arc_indices)
    ends = set(solve_result.selected_end_arc_indices)
    successors: dict[int, int] = {}
    for left_index, right_index in solve_result.selected_route_arc_indices:
        if left_index in successors:
            raise ModelReconciliationError("a selected pattern has multiple route successors")
        successors[left_index] = right_index

    for index in starts | ends | set(successors) | {
        right for _, right in solve_result.selected_route_arc_indices
    }:
        if index < 0 or index >= len(patterns):
            raise ModelReconciliationError("selected route arc references an unknown pattern")
    if not starts.issubset(selected_set) or not ends.issubset(selected_set):
        raise ModelReconciliationError("selected route arc is not attached to a selected pattern")
    if not set(successors).issubset(selected_set):
        raise ModelReconciliationError("selected route arc starts from an unselected pattern")
    if any(right not in selected_set for right in successors.values()):
        raise ModelReconciliationError("selected route successor is not selected")

    selected_by_crew: dict[str, list[int]] = defaultdict(list)
    for index in selected_set:
        selected_by_crew[patterns[index].crew_id].append(index)

    orders: dict[str, tuple[int, ...]] = {}
    for crew_id, crew_indices in sorted(selected_by_crew.items()):
        crew_set = set(crew_indices)
        crew_starts = sorted(index for index in starts if patterns[index].crew_id == crew_id)
        crew_ends = {index for index in ends if patterns[index].crew_id == crew_id}
        if len(crew_starts) != 1 or len(crew_ends) != 1:
            raise ModelReconciliationError("each used crew must have one start and end arc")
        order: list[int] = []
        current = crew_starts[0]
        while True:
            if current in order:
                raise ModelReconciliationError("selected route contains a cycle")
            order.append(current)
            successor = successors.get(current)
            if successor is None:
                if current not in crew_ends:
                    raise ModelReconciliationError("selected route does not terminate at the depot")
                break
            if current in crew_ends:
                raise ModelReconciliationError("selected pattern has both route and end arcs")
            if patterns[successor].crew_id != crew_id:
                raise ModelReconciliationError("selected route changes crew")
            current = successor
        if set(order) != crew_set:
            raise ModelReconciliationError("selected route does not visit every selected pattern once")
        orders[crew_id] = tuple(order)

    if orders:
        visited = set().union(*(set(order) for order in orders.values()))
        if visited != selected_set:
            raise ModelReconciliationError("some selected pattern is not present in a route order")
    return orders


def _build_route_segments(
    optimizer_model: OptimizerModel,
    orders: dict[str, tuple[int, ...]],
) -> tuple[RouteSegment, ...]:
    scenario = optimizer_model.scenario
    patterns = optimizer_model.patterns
    locations = {location.id: location for location in scenario.locations}
    matrix_index = {
        location_id: index
        for index, location_id in enumerate(scenario.travel_matrix_location_ids)
    }
    segments: list[RouteSegment] = []
    for crew_id in sorted(orders):
        crew = next(crew for crew in scenario.crews if crew.id == crew_id)
        order = orders[crew_id]
        first = patterns[order[0]]
        segments.append(
            _make_route_segment(
                scenario,
                locations,
                matrix_index,
                crew_id,
                crew.start_depot_id,
                first.location_id,
                arrival_slot=first.start_slot,
                departure_minutes=None,
                arrival_minutes=None,
            )
        )
        for left_index, right_index in zip(order, order[1:]):
            left = patterns[left_index]
            right = patterns[right_index]
            segments.append(
                _make_route_segment(
                    scenario,
                    locations,
                    matrix_index,
                    crew_id,
                    left.location_id,
                    right.location_id,
                    arrival_slot=right.start_slot,
                    departure_minutes=None,
                    arrival_minutes=None,
                )
            )
        last = patterns[order[-1]]
        segments.append(
            _make_route_segment(
                scenario,
                locations,
                matrix_index,
                crew_id,
                last.location_id,
                crew.end_depot_id,
                arrival_slot=None,
                departure_minutes=parse_time(scenario.day_start) + last.end_slot * scenario.slot_minutes,
                arrival_minutes=None,
            )
        )
    return tuple(segments)


def _make_route_segment(
    scenario: Scenario,
    locations: dict[str, object],
    matrix_index: dict[str, int],
    crew_id: str,
    from_location_id: str,
    to_location_id: str,
    *,
    arrival_slot: int | None,
    departure_minutes: int | None,
    arrival_minutes: int | None,
) -> RouteSegment:
    travel_minutes = _matrix_value(scenario, matrix_index, from_location_id, to_location_id)
    if arrival_slot is not None:
        arrival_absolute = parse_time(scenario.day_start) + arrival_slot * scenario.slot_minutes
        arrival_minutes = arrival_absolute
        departure_minutes = arrival_absolute - travel_minutes
    assert departure_minutes is not None
    if arrival_minutes is None:
        arrival_minutes = departure_minutes + travel_minutes
    assert arrival_minutes is not None
    return RouteSegment(
        crew_id=crew_id,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        departure=format_time(departure_minutes),
        arrival=format_time(arrival_minutes),
        travel_minutes=travel_minutes,
        from_coordinates=list(locations[from_location_id].coordinates),
        to_coordinates=list(locations[to_location_id].coordinates),
    )


def _paint_slots(
    optimizer_model: OptimizerModel,
    solve_result: StagedSolveResult,
    selected_set: set[int],
) -> dict[tuple[str, int], _SlotFact]:
    scenario = optimizer_model.scenario
    horizon_slots = _horizon_slots(scenario)
    facts: dict[tuple[str, int], _SlotFact] = {}
    for crew in scenario.crews:
        for slot in range(horizon_slots):
            state = (
                TimelineState.IDLE
                if _slot_inside_crew_availability(scenario, crew, slot)
                else TimelineState.UNAVAILABLE
            )
            facts[(crew.id, slot)] = _SlotFact(crew_id=crew.id, slot=slot, state=state)

    patterns = optimizer_model.patterns
    for index in sorted(selected_set):
        pattern = patterns[index]
        rule_ids = dict(pattern.rule_ids_by_work_slot)
        for slot in pattern.work_slots:
            _paint_slot(
                facts,
                _SlotFact(
                    crew_id=pattern.crew_id,
                    slot=slot,
                    state=TimelineState.WORK,
                    job_id=pattern.job_id,
                    location_id=pattern.location_id,
                    exertion=pattern.exertion,
                    policy_rule_ids=rule_ids.get(slot, ()),
                ),
            )
        for slot in pattern.committed_recovery_slots:
            _paint_slot(
                facts,
                _SlotFact(
                    crew_id=pattern.crew_id,
                    slot=slot,
                    state=TimelineState.RECOVERY,
                    job_id=pattern.job_id,
                    location_id=pattern.location_id,
                    exertion=pattern.exertion,
                ),
            )

    for index in sorted(solve_result.selected_start_arc_indices):
        _paint_travel(facts, optimizer_model.patterns[index].crew_id, optimizer_model.start_travel_slots[index])
    for left_index, right_index in sorted(solve_result.selected_route_arc_indices):
        _paint_travel(
            facts,
            optimizer_model.patterns[left_index].crew_id,
            optimizer_model.route_travel_slots[(left_index, right_index)],
        )
    for index in sorted(solve_result.selected_end_arc_indices):
        _paint_travel(facts, optimizer_model.patterns[index].crew_id, optimizer_model.end_travel_slots[index])

    for crew_id, slot in sorted(solve_result.selected_standalone_recovery):
        _paint_slot(
            facts,
            _SlotFact(
                crew_id=crew_id,
                slot=slot,
                state=TimelineState.RECOVERY,
            ),
        )
    return facts


def _paint_travel(facts: dict[tuple[str, int], _SlotFact], crew_id: str, slots: Iterable[int]) -> None:
    for slot in slots:
        _paint_slot(
            facts,
            _SlotFact(crew_id=crew_id, slot=slot, state=TimelineState.TRAVEL),
        )


def _paint_slot(facts: dict[tuple[str, int], _SlotFact], incoming: _SlotFact) -> None:
    key = (incoming.crew_id, incoming.slot)
    if key not in facts:
        raise ModelReconciliationError("selected state lies outside the planning horizon")
    existing = facts[key]
    if existing.state not in (TimelineState.IDLE, TimelineState.UNAVAILABLE):
        raise ModelReconciliationError(f"timeline collision at {incoming.crew_id}[{incoming.slot}]")
    if existing.state is TimelineState.UNAVAILABLE:
        raise ModelReconciliationError(f"selected state lies outside crew availability at {key}")
    facts[key] = incoming


def _merge_timeline_segments(
    scenario: Scenario,
    slot_facts: dict[tuple[str, int], _SlotFact],
) -> tuple[TimelineSegment, ...]:
    segments: list[TimelineSegment] = []
    horizon_slots = _horizon_slots(scenario)
    for crew in sorted(scenario.crews, key=lambda item: item.id):
        current: _SlotFact | None = None
        segment_start = 0
        for slot in range(horizon_slots):
            fact = slot_facts[(crew.id, slot)]
            if current is None:
                current = fact
                segment_start = slot
                continue
            if _same_segment_fields(current, fact):
                continue
            segments.append(_make_timeline_segment(scenario, current, segment_start, slot))
            current = fact
            segment_start = slot
        if current is not None:
            segments.append(_make_timeline_segment(scenario, current, segment_start, horizon_slots))
    return tuple(segments)


def _same_segment_fields(left: _SlotFact, right: _SlotFact) -> bool:
    return (
        left.state is right.state
        and left.job_id == right.job_id
        and left.location_id == right.location_id
        and left.exertion is right.exertion
        and left.policy_rule_ids == right.policy_rule_ids
    )


def _make_timeline_segment(
    scenario: Scenario,
    fact: _SlotFact,
    start_slot: int,
    end_slot: int,
) -> TimelineSegment:
    return TimelineSegment(
        crew_id=fact.crew_id,
        state=fact.state,
        job_id=fact.job_id,
        start_slot=start_slot,
        end_slot=end_slot,
        start=slot_to_time(start_slot, scenario.day_start, scenario.slot_minutes),
        end=slot_to_time(end_slot, scenario.day_start, scenario.slot_minutes),
        exertion=fact.exertion,
        location_id=fact.location_id,
        policy_rule_ids=list(fact.policy_rule_ids),
    )


def _build_job_results(
    scenario: Scenario,
    patterns: tuple[ExecutionPattern, ...],
    selected_indices: tuple[int, ...],
) -> tuple[JobResult, ...]:
    selected_by_job = {patterns[index].job_id: patterns[index] for index in selected_indices}
    results: list[JobResult] = []
    for job in sorted(scenario.jobs, key=lambda item: item.id):
        pattern = selected_by_job.get(job.id)
        if pattern is None:
            results.append(
                JobResult(
                    job_id=job.id,
                    served=False,
                    status_reason_code="NOT_SELECTED",
                )
            )
        else:
            results.append(
                JobResult(
                    job_id=job.id,
                    served=True,
                    crew_id=pattern.crew_id,
                    start=slot_to_time(pattern.start_slot, scenario.day_start, scenario.slot_minutes),
                    end=slot_to_time(pattern.end_slot, scenario.day_start, scenario.slot_minutes),
                )
            )
    return tuple(results)


def _compute_metrics(
    scenario: Scenario,
    jobs: tuple[JobResult, ...],
    timeline_segments: tuple[TimelineSegment, ...],
    route_segments: tuple[RouteSegment, ...],
    conflicts: ConflictEvidence,
) -> Metrics:
    scenario_jobs = {job.id: job for job in scenario.jobs}
    critical_total = sum(job.priority is Priority.CRITICAL for job in scenario.jobs)
    critical_scheduled = sum(
        result.served
        and scenario_jobs[result.job_id].priority is Priority.CRITICAL
        for result in jobs
    )
    planned_value = sum(
        scenario_jobs[result.job_id].service_value
        for result in jobs
        if result.served
    )
    active_slots = 0
    recovery_slots = 0
    for segment in timeline_segments:
        count = segment.end_slot - segment.start_slot
        if segment.state is TimelineState.WORK:
            active_slots += count
        elif segment.state is TimelineState.RECOVERY:
            recovery_slots += count

    regular_shift_end = {crew.id: parse_time(crew.shift_end) for crew in scenario.crews}
    overtime_by_crew: dict[str, int] = defaultdict(int)
    crew_end_depots = {crew.id: crew.end_depot_id for crew in scenario.crews}
    for segment in route_segments:
        if segment.to_location_id != crew_end_depots[segment.crew_id]:
            continue
        arrival = parse_time(segment.arrival)
        overtime_by_crew[segment.crew_id] = max(
            overtime_by_crew[segment.crew_id],
            max(0, arrival - regular_shift_end[segment.crew_id]),
        )

    return Metrics(
        critical_jobs_scheduled=critical_scheduled,
        critical_jobs_total=critical_total,
        planned_service_value=planned_value,
        mandatory_policy_conflicts=conflicts.count,
        travel_minutes=sum(segment.travel_minutes for segment in route_segments),
        overtime_minutes=sum(overtime_by_crew.values()),
        active_work_minutes=active_slots * scenario.slot_minutes,
        eligible_recovery_minutes=recovery_slots * scenario.slot_minutes,
    )


def _slot_facts_from_segments(
    scenario: Scenario,
    timeline_segments: Iterable[TimelineSegment],
) -> dict[tuple[str, int], _SlotFact]:
    horizon_slots = _horizon_slots(scenario)
    facts: dict[tuple[str, int], _SlotFact] = {}
    for crew in scenario.crews:
        for slot in range(horizon_slots):
            facts[(crew.id, slot)] = _SlotFact(
                crew_id=crew.id,
                slot=slot,
                state=TimelineState.IDLE,
            )
    for segment in timeline_segments:
        if segment.crew_id not in {crew.id for crew in scenario.crews}:
            raise ModelReconciliationError(f"timeline references unknown crew {segment.crew_id!r}")
        for slot in range(segment.start_slot, segment.end_slot):
            key = (segment.crew_id, slot)
            if key not in facts:
                raise ModelReconciliationError("timeline segment lies outside the planning horizon")
            existing = facts[key]
            if existing.state is not TimelineState.IDLE:
                raise ModelReconciliationError(f"serialized timeline collision at {key}")
            facts[key] = _SlotFact(
                crew_id=segment.crew_id,
                slot=slot,
                state=segment.state,
                job_id=segment.job_id,
                location_id=segment.location_id,
                exertion=segment.exertion,
                policy_rule_ids=tuple(segment.policy_rule_ids),
            )
    return facts


def _slot_inside_crew_availability(scenario: Scenario, crew: Crew, slot: int) -> bool:
    day_start = parse_time(scenario.day_start)
    slot_start = day_start + slot * scenario.slot_minutes
    slot_end = slot_start + scenario.slot_minutes
    latest_end = min(
        parse_time(scenario.day_end),
        parse_time(crew.shift_end) + crew.max_overtime_minutes,
    )
    return slot_start >= parse_time(crew.shift_start) and slot_end <= latest_end


def _horizon_slots(scenario: Scenario) -> int:
    horizon_minutes = parse_time(scenario.day_end) - parse_time(scenario.day_start)
    if scenario.slot_minutes <= 0 or horizon_minutes <= 0 or horizon_minutes % scenario.slot_minutes:
        raise ModelReconciliationError("scenario horizon is not slot aligned")
    return horizon_minutes // scenario.slot_minutes


def _matrix_value(
    scenario: Scenario,
    matrix_index: dict[str, int],
    from_location_id: str,
    to_location_id: str,
) -> int:
    try:
        return scenario.travel_matrix_minutes[matrix_index[from_location_id]][matrix_index[to_location_id]]
    except (KeyError, IndexError) as error:
        raise ModelReconciliationError("route references an invalid travel matrix location") from error


def _value(value: object) -> object:
    return getattr(value, "value", value)
