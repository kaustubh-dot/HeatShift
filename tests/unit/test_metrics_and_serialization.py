from __future__ import annotations

from dataclasses import replace

import pytest

from backend.heatshift.metrics import (
    ModelReconciliationError,
    evaluate_policy_conflicts,
    extract_plan_facts,
    reconcile_plan_facts,
)
from backend.heatshift.optimizer import build_optimizer_model, solve_staged
from backend.heatshift.patterns import generate_baseline_patterns
from tests.unit.test_patterns import make_case


def build_facts(*, elevated: bool = False):
    bands = ["elevated"] * 8 if elevated else ["normal"] * 8
    scenario, policy = make_case(bands, active_minutes=45)
    model_data = build_optimizer_model(
        scenario,
        policy,
        generate_baseline_patterns(scenario),
        enforce_policy=False,
    )
    result = solve_staged(model_data, 5)
    return extract_plan_facts(model_data, result)


def test_extraction_builds_route_timeline_jobs_metrics_and_conflicts() -> None:
    facts = build_facts(elevated=True)

    assert facts.jobs
    assert [job.job_id for job in facts.jobs] == sorted(job.job_id for job in facts.jobs)
    served = next(job for job in facts.jobs if job.served)
    assert served.crew_id == "crew-a"
    assert served.start is not None and served.end is not None

    states = [(segment.state.value, segment.start_slot, segment.end_slot) for segment in facts.timeline_segments]
    assert any(state == "travel" for state, _, _ in states)
    assert any(state == "work" for state, _, _ in states)
    assert facts.route_segments[0].from_location_id == "depot-central"
    assert facts.route_segments[-1].to_location_id == "depot-central"
    assert facts.route_segments[0].travel_minutes == 1
    assert facts.route_segments[-1].travel_minutes == 1
    assert facts.metrics.travel_minutes == sum(route.travel_minutes for route in facts.route_segments)
    assert facts.metrics.active_work_minutes == 45
    assert facts.metrics.eligible_recovery_minutes == 0
    assert facts.metrics.mandatory_policy_conflicts == facts.conflicts.count
    assert facts.conflicts.count > 0
    assert facts.conflicts.rule_ids
    assert facts.conflicts.job_ids


def test_policy_conflict_evaluator_counts_one_conflict_per_window() -> None:
    facts = build_facts(elevated=True)
    evidence = evaluate_policy_conflicts(
        facts.scenario,
        facts.policy,
        facts.timeline_segments,
    )
    assert evidence == facts.conflicts
    assert all(conflict.window_end_slot - conflict.window_start_slot == 4 for conflict in evidence.conflicts)
    assert len(evidence.conflicts) == evidence.count


def test_reconciliation_detects_metric_corruption() -> None:
    facts = build_facts()
    corrupted = replace(
        facts,
        metrics=facts.metrics.model_copy(
            update={"travel_minutes": facts.metrics.travel_minutes + 1}
        ),
    )
    with pytest.raises(ModelReconciliationError):
        reconcile_plan_facts(corrupted)


def test_reconciliation_detects_timeline_conflict_corruption() -> None:
    facts = build_facts()
    work_index = next(
        index for index, segment in enumerate(facts.timeline_segments) if segment.state.value == "work"
    )
    corrupted_segments = list(facts.timeline_segments)
    corrupted_segments[work_index] = corrupted_segments[work_index].model_copy(
        update={"state": "recovery"}
    )
    corrupted = replace(facts, timeline_segments=tuple(corrupted_segments))
    with pytest.raises(ModelReconciliationError):
        reconcile_plan_facts(corrupted)
