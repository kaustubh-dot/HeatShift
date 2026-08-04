from __future__ import annotations

from copy import deepcopy

from backend.heatshift.models import Crew, Job, Policy, Scenario
from backend.heatshift.patterns import (
    ExecutionPattern,
    generate_baseline_patterns,
    generate_policy_constrained_patterns,
)
from backend.heatshift.timegrid import format_time


def make_case(
    heat_bands: list[str],
    *,
    active_minutes: int = 45,
    window_start_slot: int = 1,
    window_end_slot: int | None = None,
    locked_start_slot: int | None = None,
    recovery_profile: str = "eligible",
    eligible_profiles: list[str] | None = None,
    rolling_window_slots: int = 4,
) -> tuple[Scenario, Policy]:
    slot_minutes = 15
    horizon_slots = len(heat_bands)
    day_start = "07:00"
    day_end = format_time(7 * 60 + horizon_slots * slot_minutes)
    window_end_slot = window_end_slot if window_end_slot is not None else horizon_slots
    locations = [
        {"id": "depot-central", "coordinates": [0, 0]},
        {"id": "loc-job", "coordinates": [1, 1]},
    ]
    scenario = Scenario.model_validate(
        {
            "id": "pattern-case",
            "date": "2026-08-04",
            "slot_minutes": slot_minutes,
            "day_start": day_start,
            "day_end": day_end,
            "policy_id": "pattern-policy",
            "crews": [
                {
                    "id": "crew-a",
                    "name": "Crew A",
                    "shift_start": day_start,
                    "shift_end": day_end,
                    "start_depot_id": "depot-central",
                    "end_depot_id": "depot-central",
                    "capabilities": ["work"],
                    "equipment": ["tool"],
                    "max_overtime_minutes": 0,
                    "recovery_profile": recovery_profile,
                }
            ],
            "jobs": [
                {
                    "id": "job-a",
                    "name": "Job A",
                    "location_id": "loc-job",
                    "active_minutes": active_minutes,
                    "exertion": "heavy",
                    "priority": "planned",
                    "service_value": 8,
                    "window_start": format_time(7 * 60 + window_start_slot * slot_minutes),
                    "window_end": format_time(7 * 60 + window_end_slot * slot_minutes),
                    "required_capabilities": ["work"],
                    "required_equipment": ["tool"],
                    "locked": False,
                    "locked_crew_id": None,
                    "locked_start": (
                        format_time(7 * 60 + locked_start_slot * slot_minutes)
                        if locked_start_slot is not None
                        else None
                    ),
                }
            ],
            "locations": locations,
            "heat_series": [
                {
                    "slot": index,
                    "start": format_time(7 * 60 + index * slot_minutes),
                    "temperature_c": {
                        "normal": 30,
                        "elevated": 33,
                        "severe": 39,
                        "extreme": 43,
                    }[band],
                    "band": band,
                }
                for index, band in enumerate(heat_bands)
            ],
            "travel_matrix_location_ids": ["depot-central", "loc-job"],
            "travel_matrix_minutes": [[0, 1], [1, 0]],
        }
    )

    rules = []
    values = {
        "normal": (4, 0, False),
        "elevated": (3, 1, False),
        "severe": (2, 2, False),
        "extreme": (0, 4, True),
    }
    for band, (maximum, minimum, stop_work) in values.items():
        rules.append(
            {
                "id": f"rule-heavy-{band}",
                "band": band,
                "exertion": "heavy",
                "max_active_slots": maximum,
                "min_recovery_slots": minimum,
                "stop_work": stop_work,
            }
        )
        rules.append(
            {
                "id": f"rule-moderate-{band}",
                "band": band,
                "exertion": "moderate",
                "max_active_slots": 4,
                "min_recovery_slots": 0,
                "stop_work": False,
            }
        )
    policy = Policy.model_validate(
        {
            "id": "pattern-policy",
            "name": "Pattern Policy",
            "synthetic": True,
            "disclaimer": "Synthetic policy for tests.",
            "band_thresholds_c": {"elevated": 32, "severe": 38, "extreme": 42},
            "rolling_window_slots": rolling_window_slots,
            "eligible_recovery_profiles": eligible_profiles or ["eligible"],
            "travel_counts_as_recovery": False,
            "rules": rules,
        }
    )
    return scenario, policy


def first_pattern(patterns: list[ExecutionPattern]) -> ExecutionPattern:
    assert patterns
    return patterns[0]


def test_continuous_work_pattern_has_only_required_work_slots() -> None:
    scenario, policy = make_case(["normal"] * 7, active_minutes=45)
    pattern = first_pattern(generate_policy_constrained_patterns(scenario, policy))

    assert pattern.work_slots == (1, 2, 3)
    assert pattern.committed_recovery_slots == ()
    assert [(segment.state.value, segment.start_slot, segment.end_slot) for segment in pattern.segments] == [
        ("work", 1, 4)
    ]


def test_45_15_policy_inserts_recovery_and_extends_elapsed_time() -> None:
    scenario, policy = make_case(["elevated"] * 9, active_minutes=90)
    pattern = first_pattern(generate_policy_constrained_patterns(scenario, policy))

    assert len(pattern.work_slots) == 6
    assert pattern.committed_recovery_slots == (4,)
    assert pattern.end_slot - pattern.start_slot == 7
    assert [(segment.state.value, segment.start_slot, segment.end_slot) for segment in pattern.segments] == [
        ("work", 1, 4),
        ("recovery", 4, 5),
        ("work", 5, 8),
    ]


def test_severe_band_transition_changes_the_local_sequence() -> None:
    scenario, policy = make_case(
        ["normal", "normal", "severe", "severe", "severe", "severe", "normal", "normal"],
        active_minutes=60,
    )
    pattern = first_pattern(generate_policy_constrained_patterns(scenario, policy))

    assert len(pattern.work_slots) == 4
    assert pattern.committed_recovery_slots
    severe_slots = {2, 3, 4, 5}
    assert not (set(pattern.work_slots) & severe_slots) == severe_slots
    assert any(
        segment.state.value == "recovery" and segment.start_slot in severe_slots
        for segment in pattern.segments
    )


def test_stop_work_slot_cannot_contain_active_work() -> None:
    scenario, policy = make_case(
        ["normal", "normal", "extreme", "normal", "normal", "normal", "normal"],
        active_minutes=45,
    )
    pattern = first_pattern(generate_policy_constrained_patterns(scenario, policy))

    assert 2 not in pattern.work_slots
    assert 2 in pattern.committed_recovery_slots
    assert all(slot != 2 for slot in pattern.work_slots)


def test_ineligible_recovery_profile_rejects_a_pattern_that_needs_recovery() -> None:
    scenario, policy = make_case(
        ["elevated"] * 9,
        active_minutes=90,
        recovery_profile="not-eligible",
    )
    assert generate_policy_constrained_patterns(scenario, policy) == []


def test_recovery_that_overflows_the_job_window_is_rejected() -> None:
    scenario, policy = make_case(
        ["elevated"] * 8,
        active_minutes=90,
        window_end_slot=7,
    )
    assert generate_policy_constrained_patterns(scenario, policy) == []


def test_locked_start_produces_no_alternate_start() -> None:
    scenario, policy = make_case(
        ["normal"] * 9,
        active_minutes=45,
        locked_start_slot=4,
    )
    patterns = generate_policy_constrained_patterns(scenario, policy)
    assert patterns
    assert {pattern.start_slot for pattern in patterns} == {4}


def test_baseline_ignores_heat_rules_but_keeps_operational_constraints() -> None:
    scenario, policy = make_case(["extreme"] * 8, active_minutes=60)
    patterns = generate_baseline_patterns(scenario)
    pattern = first_pattern(patterns)

    assert len(pattern.work_slots) == 4
    assert pattern.committed_recovery_slots == ()
    assert all(segment.state.value == "work" for segment in pattern.segments)


def test_pattern_has_exact_work_count_and_no_work_in_heavy_extreme_slots() -> None:
    scenario, policy = make_case(
        ["normal", "normal", "extreme", "normal", "normal", "normal", "normal", "normal"],
        active_minutes=45,
    )
    pattern = first_pattern(generate_policy_constrained_patterns(scenario, policy))
    assert len(pattern.work_slots) == 3
    assert 2 not in pattern.work_slots


def test_pattern_ids_and_order_are_stable_without_mutating_inputs() -> None:
    scenario, policy = make_case(["normal"] * 9, active_minutes=45)
    before_scenario = deepcopy(scenario.model_dump(mode="json"))
    before_policy = deepcopy(policy.model_dump(mode="json"))

    first = generate_policy_constrained_patterns(scenario, policy)
    second = generate_policy_constrained_patterns(scenario, policy)

    assert [pattern.pattern_id for pattern in first] == [pattern.pattern_id for pattern in second]
    assert [
        (pattern.job_id, pattern.crew_id, pattern.start_slot, pattern.end_slot, pattern.pattern_id)
        for pattern in first
    ] == sorted(
        (pattern.job_id, pattern.crew_id, pattern.start_slot, pattern.end_slot, pattern.pattern_id)
        for pattern in first
    )
    assert scenario.model_dump(mode="json") == before_scenario
    assert policy.model_dump(mode="json") == before_policy
