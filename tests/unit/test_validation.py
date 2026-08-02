from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.heatshift.models import HeatThresholdBand, Policy, Scenario
from backend.heatshift.validation import (
    ScenarioValidationError,
    require_valid_scenario,
    validate_scenario,
)


FIXTURE_DIR = Path(__file__).parents[2] / "backend" / "heatshift" / "fixtures"


def load_valid() -> tuple[Scenario, Policy]:
    scenario = Scenario.model_validate(
        json.loads((FIXTURE_DIR / "scenario.json").read_text(encoding="utf-8"))
    )
    policy = Policy.model_validate(
        json.loads((FIXTURE_DIR / "policy.json").read_text(encoding="utf-8"))
    )
    return scenario, policy


def test_valid_fixtures_have_no_semantic_errors() -> None:
    scenario, policy = load_valid()
    assert validate_scenario(scenario, policy) == []


def test_duplicate_ids_are_reported_for_all_owned_collections() -> None:
    scenario, policy = load_valid()
    scenario.crews[1].id = scenario.crews[0].id
    scenario.jobs[1].id = scenario.jobs[0].id
    scenario.locations[1].id = scenario.locations[0].id
    scenario.heat_series[1].slot = scenario.heat_series[0].slot
    policy.rules[1].id = policy.rules[0].id

    issues = validate_scenario(scenario, policy)
    duplicate_paths = {issue.path for issue in issues if issue.code == "DUPLICATE_ID"}
    assert duplicate_paths == {
        "crews[1].id",
        "jobs[1].id",
        "locations[1].id",
        "heat_series[1].slot",
        "rules[1].id",
    }


def test_policy_id_must_match() -> None:
    scenario, policy = load_valid()
    scenario.policy_id = "other-policy"
    issues = validate_scenario(scenario, policy)
    assert {(issue.path, issue.code) for issue in issues} >= {
        ("policy_id", "POLICY_MISMATCH"),
    }


def test_horizon_must_be_ordered_and_divide_into_slots() -> None:
    scenario, policy = load_valid()
    scenario.day_end = "07:10"
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "day_end" and issue.code == "NOT_SLOT_ALIGNED" for issue in issues)

    scenario.day_start = "17:00"
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "day_start" and issue.code == "INVALID_TIME_WINDOW" for issue in issues)


def test_shift_window_job_window_duration_and_lock_start_are_aligned() -> None:
    scenario, policy = load_valid()
    scenario.crews[0].shift_start = "07:05"
    scenario.jobs[0].window_end = "10:20"
    scenario.jobs[0].active_minutes = 10
    scenario.jobs[0].locked_start = "07:20"
    issues = validate_scenario(scenario, policy)
    assert {issue.code for issue in issues} >= {"NOT_SLOT_ALIGNED"}
    assert any(issue.path == "jobs[0].active_minutes" for issue in issues)
    assert any(issue.path == "jobs[0].locked_start" for issue in issues)


def test_depots_and_job_locations_must_exist() -> None:
    scenario, policy = load_valid()
    scenario.crews[0].start_depot_id = "loc-missing"
    scenario.jobs[0].location_id = "loc-missing"
    issues = validate_scenario(scenario, policy)
    assert ("crews[0].start_depot_id", "UNKNOWN_REFERENCE") in {
        (issue.path, issue.code) for issue in issues
    }
    assert ("jobs[0].location_id", "UNKNOWN_REFERENCE") in {
        (issue.path, issue.code) for issue in issues
    }


def test_lock_crew_must_exist_and_be_eligible() -> None:
    scenario, policy = load_valid()
    scenario.jobs[0].locked_crew_id = "crew-general"
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "jobs[0].locked_crew_id" and issue.code == "INELIGIBLE_CREW" for issue in issues)

    scenario.jobs[0].locked_crew_id = "crew-missing"
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "jobs[0].locked_crew_id" and issue.code == "UNKNOWN_REFERENCE" for issue in issues)


def test_required_tags_and_locked_job_eligibility_are_checked() -> None:
    scenario, policy = load_valid()
    scenario.jobs[0].required_equipment[0] = "missing-equipment"
    issues = validate_scenario(scenario, policy)
    assert any(
        issue.path == "jobs[0].required_equipment[0]" and issue.code == "UNKNOWN_REFERENCE"
        for issue in issues
    )

    scenario.jobs[0].locked = True
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "jobs[0].id" and issue.code == "NO_ELIGIBLE_CREW" for issue in issues)


def test_heat_series_is_complete_ordered_aligned_and_remapped() -> None:
    scenario, policy = load_valid()
    scenario.heat_series[2].slot, scenario.heat_series[3].slot = (
        scenario.heat_series[3].slot,
        scenario.heat_series[2].slot,
    )
    scenario.heat_series[2].start = "07:30"
    scenario.heat_series[2].band = "severe"
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "heat_series[2].slot" for issue in issues)
    assert any(issue.path == "heat_series[2].start" for issue in issues)
    assert any(issue.path == "heat_series[2].band" and issue.code == "INVALID_HEAT_BAND" for issue in issues)


def test_threshold_keys_and_order_are_strict() -> None:
    scenario, policy = load_valid()
    del policy.band_thresholds_c[HeatThresholdBand.SEVERE]
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "band_thresholds_c" and issue.code == "INVALID_THRESHOLD" for issue in issues)

    scenario, policy = load_valid()
    policy.band_thresholds_c[HeatThresholdBand.SEVERE] = 31
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "band_thresholds_c" and issue.code == "INVALID_THRESHOLD" for issue in issues)


def test_used_heat_band_and_exertion_pairs_need_one_rule() -> None:
    scenario, policy = load_valid()
    policy.rules = [rule for rule in policy.rules if rule.id != "hs01-heavy-elevated"]
    issues = validate_scenario(scenario, policy)
    assert any(issue.code == "MISSING_POLICY_RULE" for issue in issues)

    scenario, policy = load_valid()
    policy.rules.append(policy.rules[2].model_copy(update={"id": "hs01-heavy-elevated-copy"}))
    issues = validate_scenario(scenario, policy)
    assert any(issue.code == "DUPLICATE_POLICY_RULE" for issue in issues)


def test_policy_rule_values_and_stop_work_are_valid() -> None:
    scenario, policy = load_valid()
    policy.rules[0].max_active_slots = policy.rolling_window_slots + 1
    policy.rules[6].stop_work = True
    policy.rules[6].max_active_slots = 1
    issues = validate_scenario(scenario, policy)
    assert any(issue.path == "rules[0].max_active_slots" for issue in issues)
    assert any(issue.path == "rules[6].max_active_slots" for issue in issues)


def test_matrix_ids_shape_diagonal_and_positive_off_diagonal_values() -> None:
    scenario, policy = load_valid()
    scenario.travel_matrix_location_ids[1] = scenario.travel_matrix_location_ids[0]
    scenario.travel_matrix_minutes[0][0] = 1
    scenario.travel_matrix_minutes[0][1] = 0
    scenario.travel_matrix_minutes.pop()
    issues = validate_scenario(scenario, policy)
    assert any(issue.code == "DUPLICATE_ID" for issue in issues)
    assert any(issue.path == "travel_matrix_minutes" and issue.code == "INVALID_MATRIX" for issue in issues)
    assert any(issue.path == "travel_matrix_minutes[0][0]" for issue in issues)
    assert any(issue.path == "travel_matrix_minutes[0][1]" for issue in issues)


def test_duplicate_matrix_location_ids_are_reported() -> None:
    scenario, policy = load_valid()
    scenario.travel_matrix_location_ids[2] = scenario.travel_matrix_location_ids[1]
    issues = validate_scenario(scenario, policy)
    assert any(
        issue.path == "travel_matrix_location_ids[2]" and issue.code == "DUPLICATE_ID"
        for issue in issues
    )


def test_all_errors_are_returned_in_deterministic_path_order() -> None:
    scenario, policy = load_valid()
    scenario.jobs[0].location_id = "missing-location"
    scenario.jobs[0].required_equipment[0] = "missing-equipment"
    scenario.travel_matrix_minutes[0][0] = 1
    scenario.policy_id = "other-policy"

    first = validate_scenario(scenario, policy)
    second = validate_scenario(scenario, policy)
    assert [(issue.path, issue.code, issue.message) for issue in first] == [
        (issue.path, issue.code, issue.message) for issue in second
    ]
    assert [issue.path for issue in first] == sorted(issue.path for issue in first)
    assert {issue.path for issue in first} >= {
        "jobs[0].location_id",
        "jobs[0].required_equipment[0]",
        "policy_id",
        "travel_matrix_minutes[0][0]",
    }


def test_boundary_helper_raises_one_exception_with_all_details() -> None:
    scenario, policy = load_valid()
    scenario.policy_id = "other-policy"
    with pytest.raises(ScenarioValidationError) as caught:
        require_valid_scenario(scenario, policy)
    assert len(caught.value.issues) == 1
    assert caught.value.issues[0].path == "policy_id"
