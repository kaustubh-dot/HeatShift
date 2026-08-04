from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.heatshift.models import (
    ApiError,
    Crew,
    DemoResponse,
    DiagnoseRequest,
    DiagnosisResponse,
    HeatBand,
    Job,
    Plan,
    PlanChange,
    Policy,
    RouteSegment,
    Scenario,
    SolveRequest,
    SolveResponse,
    Stage,
    TimelineSegment,
)


def crew_payload() -> dict:
    return {
        "id": "crew-asphalt",
        "name": "Asphalt Crew",
        "shift_start": "07:00",
        "shift_end": "16:00",
        "start_depot_id": "depot-central",
        "end_depot_id": "depot-central",
        "capabilities": ["asphalt", "traffic-control"],
        "equipment": ["patch-truck", "roller"],
        "max_overtime_minutes": 30,
        "recovery_profile": "cooled-vehicle-stationary",
    }


def job_payload() -> dict:
    return {
        "id": "job-d107",
        "name": "Residential pothole batch",
        "location_id": "loc-d107",
        "active_minutes": 75,
        "exertion": "heavy",
        "priority": "planned",
        "service_value": 8,
        "window_start": "07:00",
        "window_end": "16:00",
        "required_capabilities": ["asphalt"],
        "required_equipment": ["patch-truck"],
        "locked": False,
        "locked_crew_id": None,
        "locked_start": None,
    }


def scenario_payload() -> dict:
    return {
        "id": "demo-city-day-01",
        "date": "2026-08-04",
        "slot_minutes": 15,
        "day_start": "07:00",
        "day_end": "17:00",
        "policy_id": "demo-city-hs-01",
        "crews": [crew_payload()],
        "jobs": [job_payload()],
        "locations": [
            {"id": "depot-central", "coordinates": [400, 300]},
            {"id": "loc-d107", "coordinates": [470, 330]},
        ],
        "heat_series": [
            {"slot": 0, "start": "07:00", "temperature_c": 29, "band": "normal"}
        ],
        "travel_matrix_location_ids": ["depot-central", "loc-d107"],
        "travel_matrix_minutes": [[0, 14], [13, 0]],
    }


def policy_payload() -> dict:
    return {
        "id": "demo-city-hs-01",
        "name": "Demo City Policy HS-01",
        "synthetic": True,
        "disclaimer": "Synthetic demonstration policy only. Not medical, legal, or workplace-safety guidance.",
        "band_thresholds_c": {"elevated": 32, "severe": 38, "extreme": 42},
        "rolling_window_slots": 4,
        "eligible_recovery_profiles": ["cooled-vehicle-stationary"],
        "travel_counts_as_recovery": False,
        "rules": [
            {
                "id": "hs01-heavy-elevated",
                "band": "elevated",
                "exertion": "heavy",
                "max_active_slots": 3,
                "min_recovery_slots": 1,
                "stop_work": False,
            }
        ],
    }


def stage_payload(**overrides: object) -> dict:
    payload = {
        "name": "critical_service",
        "status": "OPTIMAL",
        "objective_value": 4,
        "best_bound": 4,
        "wall_time_seconds": 0.31,
    }
    payload.update(overrides)
    return payload


def plan_payload() -> dict:
    return {
        "label": "maximum_service_compliant_plan",
        "status": "OPTIMAL",
        "maximum_claim_allowed": True,
        "wall_time_seconds": 1.84,
        "stages": [stage_payload()],
        "metrics": {
            "critical_jobs_scheduled": 4,
            "critical_jobs_total": 4,
            "planned_service_value": 71,
            "mandatory_policy_conflicts": 0,
            "travel_minutes": 126,
            "overtime_minutes": 0,
            "active_work_minutes": 525,
            "eligible_recovery_minutes": 105,
        },
        "timeline_segments": [],
        "route_segments": [],
        "jobs": [
            {
                "job_id": "job-d107",
                "served": False,
                "crew_id": None,
                "start": None,
                "end": None,
                "status_reason_code": "POLICY_CAPACITY_CONFLICT",
            }
        ],
    }


def solve_response_payload() -> dict:
    plan = plan_payload()
    return {
        "scenario": {
            "id": "demo-city-day-01",
            "policy_id": "demo-city-hs-01",
            "policy_disclaimer": "Synthetic demonstration policy only.",
            "slot_minutes": 15,
            "heat_adjustment_c": 0,
        },
        "plans": {
            "service_first": plan,
            "policy_constrained": plan,
            "heat_shock": None,
        },
        "plan_diff": [
            {
                "job_id": "job-d107",
                "change": "deferred",
                "before": {
                    "crew_id": "crew-asphalt",
                    "start": "13:00",
                    "end": "14:15",
                },
                "after": None,
                "binding_rule_ids": ["hs01-heavy-severe"],
                "explanation_code": "POLICY_CAPACITY_CONFLICT",
            }
        ],
        "diagnostics": {},
    }


def test_contract_input_examples_parse() -> None:
    scenario = Scenario.model_validate(scenario_payload())
    policy = Policy.model_validate(policy_payload())

    assert scenario.jobs[0].exertion == "heavy"
    assert policy.band_thresholds_c["elevated"] == 32

    plan = Plan.model_validate(plan_payload())
    response = SolveResponse.model_validate(solve_response_payload())
    assert plan.status == "OPTIMAL"
    assert response.plans.heat_shock is None

    TimelineSegment.model_validate(
        {
            "crew_id": "crew-asphalt",
            "state": "work",
            "job_id": "job-d107",
            "start_slot": 9,
            "end_slot": 12,
            "start": "09:15",
            "end": "10:00",
            "exertion": "heavy",
            "location_id": "loc-d107",
            "policy_rule_ids": ["hs01-heavy-elevated"],
        }
    )
    RouteSegment.model_validate(
        {
            "crew_id": "crew-asphalt",
            "from_location_id": "loc-d101",
            "to_location_id": "loc-d107",
            "departure": "09:01",
            "arrival": "09:15",
            "travel_minutes": 14,
            "from_coordinates": [180, 210],
            "to_coordinates": [470, 330],
        }
    )

    SolveRequest(
        scenario=scenario,
        policy=policy,
        heat_adjustment_c=0,
        time_limit_seconds=5,
    )
    DiagnoseRequest(
        scenario=scenario,
        policy=policy,
        job_id="job-d107",
        heat_adjustment_c=0,
        time_limit_seconds=5,
    )
    DemoResponse(
        scenario=scenario,
        policy=policy,
        display_coordinates={"depot-central": [400, 300]},
        saved_result_metadata={
            "fixture_version": "demo-v1",
            "generated_at": "2026-08-01T12:00:00Z",
            "solver_version": "implementation-defined",
            "sha256": "implementation-defined",
        },
    )
    DiagnosisResponse(
        job_id="job-d107",
        classification="feasible_with_cost",
        proof_status="OPTIMAL",
        retained_commitments=["all-mandatory-rules", "all-critical-jobs"],
        displaced_job_ids=["job-d104"],
        objective_delta={
            "critical_service": 0,
            "planned_service_value": -4,
            "travel_minutes": 18,
            "overtime_minutes": 0,
        },
        binding_rule_ids=["hs01-heavy-severe"],
        tested_interventions=[
            {
                "type": "deadline_extension",
                "value_minutes": 30,
                "status": "OPTIMAL",
                "objective_delta": {
                    "critical_service": 0,
                    "planned_service_value": 0,
                    "travel_minutes": 4,
                    "overtime_minutes": 0,
                },
            }
        ],
    )
    ApiError(
        code="INVALID_SCENARIO",
        message="Scenario validation failed.",
        details=[
            {
                "path": "jobs[2].required_equipment[0]",
                "code": "UNKNOWN_REFERENCE",
                "message": "Equipment 'vac-truck' is not present on any crew.",
            }
        ],
    )


def test_unknown_fields_are_rejected() -> None:
    payload = crew_payload()
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        Crew.model_validate(payload)


def test_primitive_fields_are_not_coerced() -> None:
    payload = crew_payload()
    payload["name"] = 123

    with pytest.raises(ValidationError):
        Crew.model_validate(payload)


@pytest.mark.parametrize(
    ("model", "payload", "field"),
    [
        (Job, {**job_payload(), "exertion": "light"}, "exertion"),
        (Plan, {**plan_payload(), "status": "DONE"}, "status"),
        (
            SolveResponse,
            {
                **solve_response_payload(),
                "plan_diff": [{
                    "job_id": "job-d107",
                    "change": "deleted",
                    "explanation_code": "UNKNOWN",
                }],
            },
            "change",
        ),
        (
            DiagnosisResponse,
            {
                "job_id": "job-d107",
                "classification": "impossible",
                "proof_status": "OPTIMAL",
                "retained_commitments": [],
                "displaced_job_ids": [],
                "objective_delta": {
                    "critical_service": 0,
                    "planned_service_value": 0,
                    "travel_minutes": 0,
                    "overtime_minutes": 0,
                },
                "binding_rule_ids": [],
                "tested_interventions": [],
            },
            "classification",
        ),
    ],
)
def test_unknown_finite_values_are_rejected(model: type, payload: dict, field: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        model.model_validate(payload)

    assert field in str(exc_info.value)


def test_stage_objective_and_bound_can_be_null() -> None:
    stage = Stage.model_validate(stage_payload(objective_value=None, best_bound=None))

    assert stage.objective_value is None
    assert stage.best_bound is None


def test_models_round_trip_through_json_dump() -> None:
    response = SolveResponse.model_validate(solve_response_payload())
    encoded = response.model_dump(mode="json")
    restored = SolveResponse.model_validate(encoded)

    assert restored == response
    assert encoded["plans"]["heat_shock"] is None
    assert encoded["plan_diff"][0]["change"] == PlanChange.DEFERRED.value
    assert HeatBand.NORMAL.value == "normal"
