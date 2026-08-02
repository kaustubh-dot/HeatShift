"""Deterministic job-local execution-pattern generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import TypeAlias

from .models import Crew, Exertion, HeatBand, Job, Policy, PolicyRule, Scenario, TimelineState
from .timegrid import duration_to_slots, parse_time, time_to_slot


@dataclass(frozen=True, slots=True)
class PatternSegment:
    """An immutable normalized state segment inside an execution pattern."""

    crew_id: str
    state: TimelineState
    start_slot: int
    end_slot: int
    job_id: str
    location_id: str
    exertion: Exertion | None
    policy_rule_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionPattern:
    """One complete, crew-committed way to execute a job."""

    pattern_id: str
    job_id: str
    crew_id: str
    start_slot: int
    end_slot: int
    work_slots: tuple[int, ...]
    committed_recovery_slots: tuple[int, ...]
    location_id: str
    exertion: Exertion
    rule_ids_by_work_slot: tuple[tuple[int, tuple[str, ...]], ...]
    segments: tuple[PatternSegment, ...]

    @property
    def normalized_segments(self) -> tuple[PatternSegment, ...]:
        """Compatibility name for consumers that call the list normalized."""

        return self.segments

    @property
    def recovery_slots(self) -> tuple[int, ...]:
        """Short alias used by slot-occupancy consumers."""

        return self.committed_recovery_slots


PatternMode: TypeAlias = str


def crew_is_eligible(job: Job, crew: Crew) -> bool:
    """Return whether a crew contains every required capability and tool."""

    return set(job.required_capabilities).issubset(crew.capabilities) and set(
        job.required_equipment
    ).issubset(crew.equipment)


def eligible_crews(job: Job, crews: tuple[Crew, ...] | list[Crew]) -> tuple[Crew, ...]:
    """Return eligible crews in stable ID order, applying the crew lock."""

    candidates = [crew for crew in crews if crew_is_eligible(job, crew)]
    if job.locked_crew_id is not None:
        candidates = [crew for crew in candidates if crew.id == job.locked_crew_id]
    return tuple(sorted(candidates, key=lambda crew: crew.id))


def generate_baseline_patterns(scenario: Scenario) -> list[ExecutionPattern]:
    """Generate continuous-work patterns without heat-policy constraints."""

    return _generate_patterns(scenario, policy=None, mode="baseline")


def generate_policy_constrained_patterns(
    scenario: Scenario,
    policy: Policy,
) -> list[ExecutionPattern]:
    """Generate recovery-interruptible patterns constrained by the policy."""

    return _generate_patterns(scenario, policy=policy, mode="constrained")


def generate_constrained_patterns(scenario: Scenario, policy: Policy) -> list[ExecutionPattern]:
    """Alias with the shorter name used by the optimizer packet."""

    return generate_policy_constrained_patterns(scenario, policy)


def generate_patterns(
    scenario: Scenario,
    policy: Policy | None = None,
    *,
    constrained: bool = True,
) -> list[ExecutionPattern]:
    """Generate either policy-constrained or service-first patterns."""

    if constrained:
        if policy is None:
            raise ValueError("policy is required for constrained pattern generation")
        return generate_policy_constrained_patterns(scenario, policy)
    return generate_baseline_patterns(scenario)


def _generate_patterns(
    scenario: Scenario,
    policy: Policy | None,
    mode: PatternMode,
) -> list[ExecutionPattern]:
    day_start_minutes = parse_time(scenario.day_start)
    day_end_minutes = parse_time(scenario.day_end)
    horizon_minutes = day_end_minutes - day_start_minutes
    if scenario.slot_minutes <= 0 or horizon_minutes <= 0 or horizon_minutes % scenario.slot_minutes:
        raise ValueError("scenario must have a positive, slot-aligned planning horizon")
    horizon_slots = horizon_minutes // scenario.slot_minutes
    matrix_index = {
        location_id: index
        for index, location_id in enumerate(scenario.travel_matrix_location_ids)
    }
    heat_by_slot = {heat_slot.slot: heat_slot for heat_slot in scenario.heat_series}

    rules_by_pair: dict[tuple[str, Exertion], tuple[PolicyRule, ...]] = {}
    if policy is not None:
        by_pair: dict[tuple[str, Exertion], list[PolicyRule]] = {}
        for rule in policy.rules:
            pair = (_enum_value(rule.band), rule.exertion)
            by_pair.setdefault(pair, []).append(rule)
        rules_by_pair = {pair: tuple(rules) for pair, rules in by_pair.items()}

    patterns: list[ExecutionPattern] = []
    for job in sorted(scenario.jobs, key=lambda item: item.id):
        active_slots = duration_to_slots(job.active_minutes, scenario.slot_minutes)
        start_slots = _candidate_start_slots(job, scenario, active_slots)
        for crew in eligible_crews(job, scenario.crews):
            for start_slot in start_slots:
                if mode == "baseline":
                    pattern = _build_baseline_pattern(
                        scenario,
                        job,
                        crew,
                        start_slot,
                        active_slots,
                        horizon_slots,
                        matrix_index,
                    )
                else:
                    assert policy is not None
                    pattern = _build_constrained_pattern(
                        scenario,
                        policy,
                        job,
                        crew,
                        start_slot,
                        active_slots,
                        horizon_slots,
                        matrix_index,
                        heat_by_slot,
                        rules_by_pair,
                    )
                if pattern is not None:
                    patterns.append(pattern)

    patterns.sort(
        key=lambda pattern: (
            pattern.job_id,
            pattern.crew_id,
            pattern.start_slot,
            pattern.end_slot,
            pattern.pattern_id,
        )
    )
    return patterns


def _candidate_start_slots(job: Job, scenario: Scenario, active_slots: int) -> tuple[int, ...]:
    try:
        window_start = time_to_slot(job.window_start, scenario.day_start, scenario.slot_minutes)
        window_end = time_to_slot(job.window_end, scenario.day_start, scenario.slot_minutes)
    except (TypeError, ValueError) as error:
        raise ValueError(f"job {job.id} has an invalid slot-aligned window") from error

    last_start = window_end - active_slots
    if last_start < window_start:
        return ()
    candidates = tuple(range(window_start, last_start + 1))
    if job.locked_start is None:
        return candidates
    try:
        locked_start = time_to_slot(job.locked_start, scenario.day_start, scenario.slot_minutes)
    except (TypeError, ValueError) as error:
        raise ValueError(f"job {job.id} has an invalid locked_start") from error
    return (locked_start,) if locked_start in candidates else ()


def _build_baseline_pattern(
    scenario: Scenario,
    job: Job,
    crew: Crew,
    start_slot: int,
    active_slots: int,
    horizon_slots: int,
    matrix_index: dict[str, int],
) -> ExecutionPattern | None:
    end_slot = start_slot + active_slots
    if not _operationally_reachable(
        scenario,
        job,
        crew,
        start_slot,
        end_slot,
        horizon_slots,
        matrix_index,
    ):
        return None

    work_slots = tuple(range(start_slot, end_slot))
    rule_ids_by_work_slot = tuple((slot, ()) for slot in work_slots)
    states = {slot: TimelineState.WORK for slot in work_slots}
    return _make_pattern(
        mode="baseline",
        scenario=scenario,
        job=job,
        crew=crew,
        start_slot=start_slot,
        end_slot=end_slot,
        work_slots=work_slots,
        recovery_slots=(),
        rule_ids_by_work_slot=rule_ids_by_work_slot,
        states=states,
    )


def _build_constrained_pattern(
    scenario: Scenario,
    policy: Policy,
    job: Job,
    crew: Crew,
    start_slot: int,
    active_slots: int,
    horizon_slots: int,
    matrix_index: dict[str, int],
    heat_by_slot: dict[int, object],
    rules_by_pair: dict[tuple[str, Exertion], tuple[PolicyRule, ...]],
) -> ExecutionPattern | None:
    if active_slots == 0:
        return _build_baseline_pattern(
            scenario,
            job,
            crew,
            start_slot,
            active_slots,
            horizon_slots,
            matrix_index,
        )

    recovery_is_eligible = crew.recovery_profile in policy.eligible_recovery_profiles
    try:
        window_end_slot = time_to_slot(job.window_end, scenario.day_start, scenario.slot_minutes)
    except (TypeError, ValueError) as error:
        raise ValueError(f"job {job.id} has an invalid slot-aligned window") from error

    rules_by_slot: dict[int, tuple[PolicyRule, ...]] = {}
    for slot in range(start_slot, min(window_end_slot, horizon_slots)):
        try:
            heat_slot = heat_by_slot[slot]
        except KeyError:
            return None
        rules = rules_by_pair.get((_enum_value(heat_slot.band), job.exertion), ())
        if not rules:
            raise ValueError(
                f"policy has no rule for heat band {heat_slot.band!r} and exertion {job.exertion!r}"
            )
        rules_by_slot[slot] = rules

    @lru_cache(maxsize=None)
    def search(current_slot: int, work_count: int, states: tuple[TimelineState, ...]) -> tuple[TimelineState, ...] | None:
        if work_count == active_slots:
            end_slot = start_slot + len(states)
            if _operationally_reachable(
                scenario,
                job,
                crew,
                start_slot,
                end_slot,
                horizon_slots,
                matrix_index,
            ):
                return states
            return None
        if current_slot >= horizon_slots or current_slot >= window_end_slot:
            return None

        rules = rules_by_slot.get(current_slot, ())
        if not rules:
            return None
        prohibited = any(rule.stop_work or rule.max_active_slots == 0 for rule in rules)
        choices: tuple[TimelineState, ...]
        if prohibited:
            choices = (TimelineState.RECOVERY,) if current_slot != start_slot else ()
        elif recovery_is_eligible and current_slot != start_slot:
            choices = (TimelineState.WORK, TimelineState.RECOVERY)
        else:
            choices = (TimelineState.WORK,)

        for state in choices:
            next_states = states + (state,)
            if state is TimelineState.WORK:
                next_work_count = work_count + 1
                if not _windows_valid(
                    start_slot,
                    next_states,
                    rules_by_slot,
                    policy,
                ):
                    continue
            else:
                next_work_count = work_count
                if not _windows_valid(
                    start_slot,
                    next_states,
                    rules_by_slot,
                    policy,
                ):
                    continue
            result = search(current_slot + 1, next_work_count, next_states)
            if result is not None:
                return result
        return None

    state_sequence = search(start_slot, 0, ())
    if state_sequence is None:
        return None

    end_slot = start_slot + len(state_sequence)
    states = {
        start_slot + offset: state
        for offset, state in enumerate(state_sequence)
    }
    work_slots = [slot for slot, state in states.items() if state is TimelineState.WORK]
    recovery_slots = [slot for slot, state in states.items() if state is TimelineState.RECOVERY]
    rule_ids_by_slot = {
        slot: tuple(rule.id for rule in rules_by_slot[slot])
        for slot in work_slots
    }
    if not _operationally_reachable(
        scenario,
        job,
        crew,
        start_slot,
        end_slot,
        horizon_slots,
        matrix_index,
    ):
        return None

    ordered_rule_ids = tuple(
        (slot, rule_ids_by_slot[slot]) for slot in sorted(rule_ids_by_slot)
    )
    return _make_pattern(
        mode="constrained",
        scenario=scenario,
        job=job,
        crew=crew,
        start_slot=start_slot,
        end_slot=end_slot,
        work_slots=tuple(work_slots),
        recovery_slots=tuple(recovery_slots),
        rule_ids_by_work_slot=ordered_rule_ids,
        states=states,
    )


def _windows_valid(
    start_slot: int,
    states: tuple[TimelineState, ...],
    rules_by_slot: dict[int, tuple[PolicyRule, ...]],
    policy: Policy,
) -> bool:
    rolling_slots = policy.rolling_window_slots
    if rolling_slots <= 0:
        return False
    if len(states) < rolling_slots:
        return True

    for window_offset in range(0, len(states) - rolling_slots + 1):
        window_offsets = range(window_offset, window_offset + rolling_slots)
        work_offsets = [offset for offset in window_offsets if states[offset] is TimelineState.WORK]
        work_slots = [start_slot + offset for offset in work_offsets]
        if not work_slots:
            continue
        triggered_rules = {
            rule.id: rule
            for slot in work_slots
            for rule in rules_by_slot.get(slot, ())
        }
        recovery_count = sum(states[offset] is TimelineState.RECOVERY for offset in window_offsets)
        for rule in sorted(triggered_rules.values(), key=lambda item: item.id):
            if len(work_slots) > rule.max_active_slots:
                return False
            if recovery_count < rule.min_recovery_slots:
                return False
    return True


def _operationally_reachable(
    scenario: Scenario,
    job: Job,
    crew: Crew,
    start_slot: int,
    end_slot: int,
    horizon_slots: int,
    matrix_index: dict[str, int],
) -> bool:
    if start_slot < 0 or end_slot < start_slot or end_slot > horizon_slots:
        return False

    day_start = parse_time(scenario.day_start)
    day_end = parse_time(scenario.day_end)
    shift_start = parse_time(crew.shift_start)
    shift_end = parse_time(crew.shift_end)
    job_start = day_start + start_slot * scenario.slot_minutes
    job_end = day_start + end_slot * scenario.slot_minutes
    latest_crew_end = min(day_end, shift_end + crew.max_overtime_minutes)
    earliest_crew_start = max(day_start, shift_start)

    depot_to_job = _matrix_value(
        scenario,
        matrix_index,
        crew.start_depot_id,
        job.location_id,
    )
    job_to_depot = _matrix_value(
        scenario,
        matrix_index,
        job.location_id,
        crew.end_depot_id,
    )
    return (
        job_start >= earliest_crew_start + depot_to_job
        and job_end <= latest_crew_end
        and job_end + job_to_depot <= latest_crew_end
    )


def _matrix_value(
    scenario: Scenario,
    matrix_index: dict[str, int],
    from_location_id: str,
    to_location_id: str,
) -> int:
    try:
        return scenario.travel_matrix_minutes[matrix_index[from_location_id]][matrix_index[to_location_id]]
    except (KeyError, IndexError) as error:
        raise ValueError("scenario travel matrix must be validated before pattern generation") from error


def _make_pattern(
    *,
    mode: str,
    scenario: Scenario,
    job: Job,
    crew: Crew,
    start_slot: int,
    end_slot: int,
    work_slots: tuple[int, ...],
    recovery_slots: tuple[int, ...],
    rule_ids_by_work_slot: tuple[tuple[int, tuple[str, ...]], ...],
    states: dict[int, TimelineState],
) -> ExecutionPattern:
    segments = _normalize_segments(
        scenario=scenario,
        job=job,
        crew=crew,
        start_slot=start_slot,
        end_slot=end_slot,
        states=states,
        rule_ids_by_work_slot=dict(rule_ids_by_work_slot),
    )
    pattern_id = f"{mode}-{job.id}-{crew.id}-{start_slot:03d}-{end_slot:03d}"
    return ExecutionPattern(
        pattern_id=pattern_id,
        job_id=job.id,
        crew_id=crew.id,
        start_slot=start_slot,
        end_slot=end_slot,
        work_slots=work_slots,
        committed_recovery_slots=recovery_slots,
        location_id=job.location_id,
        exertion=job.exertion,
        rule_ids_by_work_slot=rule_ids_by_work_slot,
        segments=segments,
    )


def _normalize_segments(
    *,
    scenario: Scenario,
    job: Job,
    crew: Crew,
    start_slot: int,
    end_slot: int,
    states: dict[int, TimelineState],
    rule_ids_by_work_slot: dict[int, tuple[str, ...]],
) -> tuple[PatternSegment, ...]:
    segments: list[PatternSegment] = []
    current_state: TimelineState | None = None
    segment_start = start_slot
    segment_rule_ids: list[str] = []

    for slot in range(start_slot, end_slot):
        state = states.get(slot)
        if state is None:
            raise ValueError(f"pattern has no state for slot {slot}")
        if current_state is None:
            current_state = state
            segment_start = slot
        elif state is not current_state:
            segments.append(
                _make_segment(
                    crew,
                    job,
                    current_state,
                    segment_start,
                    slot,
                    segment_rule_ids,
                )
            )
            current_state = state
            segment_start = slot
            segment_rule_ids = []
        if state is TimelineState.WORK:
            for rule_id in rule_ids_by_work_slot.get(slot, ()):
                if rule_id not in segment_rule_ids:
                    segment_rule_ids.append(rule_id)

    if current_state is not None:
        segments.append(
            _make_segment(
                crew,
                job,
                current_state,
                segment_start,
                end_slot,
                segment_rule_ids,
            )
        )
    return tuple(segments)


def _make_segment(
    crew: Crew,
    job: Job,
    state: TimelineState,
    start_slot: int,
    end_slot: int,
    rule_ids: list[str],
) -> PatternSegment:
    return PatternSegment(
        crew_id=crew.id,
        state=state,
        start_slot=start_slot,
        end_slot=end_slot,
        job_id=job.id,
        location_id=job.location_id,
        exertion=job.exertion if state is TimelineState.WORK else None,
        policy_rule_ids=tuple(rule_ids),
    )


def _enum_value(value: object) -> object:
    return value.value if isinstance(value, Enum) else value
