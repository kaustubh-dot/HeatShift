from __future__ import annotations

import json
from pathlib import Path

from backend.heatshift.models import Policy, Scenario
from backend.heatshift.timegrid import remap_temperature


FIXTURE_DIR = Path(__file__).parents[2] / "backend" / "heatshift" / "fixtures"


def load_json(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_deterministic_fixture_shape_and_stable_ids() -> None:
    scenario = Scenario.model_validate(load_json("scenario.json"))
    policy = Policy.model_validate(load_json("policy.json"))

    assert scenario.id == "demo-city-day-01"
    assert scenario.policy_id == policy.id == "demo-city-hs-01"
    assert scenario.slot_minutes == 15
    assert len(scenario.crews) == 3
    assert len(scenario.jobs) == 12
    assert len(scenario.locations) == 13
    assert len(scenario.heat_series) == 40
    assert len(scenario.travel_matrix_location_ids) == 13
    assert len(scenario.travel_matrix_minutes) == 13
    assert all(len(row) == 13 for row in scenario.travel_matrix_minutes)

    assert [crew.id for crew in scenario.crews] == [
        "crew-asphalt",
        "crew-drainage",
        "crew-general",
    ]
    assert [job.id for job in scenario.jobs] == [
        "job-school-potholes",
        "job-bus-route",
        "job-residential",
        "job-utility-cut",
        "job-blocked-inlet",
        "job-catch-basin",
        "job-culvert",
        "job-drain-inspection",
        "job-stop-sign",
        "job-roadside-debris",
        "job-guardrail",
        "job-sidewalk",
    ]
    assert scenario.travel_matrix_location_ids == [
        "depot-central",
        "loc-school",
        "loc-bus-route",
        "loc-residential",
        "loc-utility-cut",
        "loc-blocked-inlet",
        "loc-catch-basin",
        "loc-culvert",
        "loc-drain-inspection",
        "loc-stop-sign",
        "loc-roadside-debris",
        "loc-guardrail",
        "loc-sidewalk",
    ]

    assert len(policy.rules) == 8
    assert [rule.id for rule in policy.rules] == [
        "hs01-heavy-normal",
        "hs01-moderate-normal",
        "hs01-heavy-elevated",
        "hs01-moderate-elevated",
        "hs01-heavy-severe",
        "hs01-moderate-severe",
        "hs01-heavy-extreme",
        "hs01-moderate-extreme",
    ]


def test_heat_bands_are_derived_from_policy_thresholds() -> None:
    scenario = Scenario.model_validate(load_json("scenario.json"))
    policy = Policy.model_validate(load_json("policy.json"))

    assert all(
        slot.band == remap_temperature(slot.temperature_c, policy.band_thresholds_c)
        for slot in scenario.heat_series
    )
    assert scenario.heat_series[8].band == "elevated"
    assert scenario.heat_series[19].band == "severe"
    assert scenario.heat_series[-1].band == "elevated"


def test_expected_crew_eligibility_from_capabilities_and_equipment() -> None:
    scenario = Scenario.model_validate(load_json("scenario.json"))

    expected = {
        "job-school-potholes": {"crew-asphalt"},
        "job-bus-route": {"crew-asphalt"},
        "job-residential": {"crew-asphalt"},
        "job-utility-cut": {"crew-asphalt"},
        "job-blocked-inlet": {"crew-drainage", "crew-general", "crew-asphalt"},
        "job-catch-basin": {"crew-drainage"},
        "job-culvert": {"crew-drainage", "crew-general", "crew-asphalt"},
        "job-drain-inspection": {"crew-drainage", "crew-general"},
        "job-stop-sign": {"crew-general"},
        "job-roadside-debris": {"crew-asphalt", "crew-drainage", "crew-general"},
        "job-guardrail": {"crew-general"},
        "job-sidewalk": {"crew-asphalt", "crew-general"},
    }

    for job in scenario.jobs:
        eligible = {
            crew.id
            for crew in scenario.crews
            if set(job.required_capabilities).issubset(crew.capabilities)
            and set(job.required_equipment).issubset(crew.equipment)
        }
        assert eligible == expected[job.id]
