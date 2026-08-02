from __future__ import annotations

from backend.heatshift.models import HeatBand, HeatSlot
from backend.heatshift.service import solve_scenario
from backend.heatshift.timegrid import adjust_heat_series
from tests.unit.test_patterns import make_case


def test_plus_two_remaps_each_inclusive_threshold_without_mutation() -> None:
    source = [
        HeatSlot(slot=0, start="07:00", temperature_c=30, band="normal"),
        HeatSlot(slot=1, start="07:15", temperature_c=36, band="elevated"),
        HeatSlot(slot=2, start="07:30", temperature_c=40, band="severe"),
    ]

    adjusted = adjust_heat_series(source, 2, {"elevated": 32, "severe": 38, "extreme": 42})

    assert [slot.temperature_c for slot in adjusted] == [32, 38, 42]
    assert [slot.band for slot in adjusted] == [
        HeatBand.ELEVATED,
        HeatBand.SEVERE,
        HeatBand.EXTREME,
    ]
    assert [slot.temperature_c for slot in source] == [30, 36, 40]
    assert [slot.band for slot in source] == [
        HeatBand.NORMAL,
        HeatBand.ELEVATED,
        HeatBand.SEVERE,
    ]


def test_heat_shock_keeps_base_plans_and_compares_unadjusted_to_shock() -> None:
    scenario, policy = make_case(["normal"] * 8, active_minutes=45)
    original_scenario = scenario.model_dump(mode="json")
    original_policy = policy.model_dump(mode="json")

    base_response = solve_scenario(scenario, policy, heat_adjustment_c=0, time_limit_seconds=5)
    shock_response = solve_scenario(scenario, policy, heat_adjustment_c=2, time_limit_seconds=5)

    assert base_response.plans.heat_shock is None
    assert shock_response.plans.heat_shock is not None
    assert shock_response.scenario.heat_adjustment_c == 2
    assert scenario.model_dump(mode="json") == original_scenario
    assert policy.model_dump(mode="json") == original_policy

    base_policy_plan = base_response.plans.policy_constrained
    shock_policy_plan = shock_response.plans.policy_constrained
    assert shock_policy_plan.jobs == base_policy_plan.jobs
    assert shock_policy_plan.metrics == base_policy_plan.metrics
    assert shock_policy_plan.timeline_segments == base_policy_plan.timeline_segments
    assert shock_policy_plan.route_segments == base_policy_plan.route_segments

    shock_plan = shock_response.plans.heat_shock
    assert shock_plan is not None
    assert shock_plan.metrics.planned_service_value < shock_policy_plan.metrics.planned_service_value
    assert any(diff.change.value == "deferred" for diff in shock_response.plan_diff)

    policy_jobs = {job.job_id: job for job in shock_policy_plan.jobs}
    shock_jobs = {job.job_id: job for job in shock_plan.jobs}
    for difference in shock_response.plan_diff:
        before = policy_jobs[difference.job_id]
        after = shock_jobs[difference.job_id]
        expected_before = (
            None
            if not before.served
            else {"crew_id": before.crew_id, "start": before.start, "end": before.end}
        )
        expected_after = (
            None
            if not after.served
            else {"crew_id": after.crew_id, "start": after.start, "end": after.end}
        )
        assert (difference.before.model_dump() if difference.before else None) == expected_before
        assert (difference.after.model_dump() if difference.after else None) == expected_after
