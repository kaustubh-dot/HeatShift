from __future__ import annotations

from dataclasses import replace

from backend.heatshift.differences import derive_plan_diff
from backend.heatshift.metrics import ConflictEvidence, PlanFacts, PolicyConflict
from backend.heatshift.models import JobResult, TimelineSegment, TimelineState
from tests.unit.test_metrics_and_serialization import build_facts


def _job(
    job_id: str,
    *,
    served: bool,
    crew_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> JobResult:
    return JobResult(
        job_id=job_id,
        served=served,
        crew_id=crew_id,
        start=start,
        end=end,
    )


def _work(job_id: str, *, crew_id: str = "crew-a", rule_ids: list[str] | None = None) -> TimelineSegment:
    return TimelineSegment(
        crew_id=crew_id,
        state=TimelineState.WORK,
        job_id=job_id,
        start_slot=1,
        end_slot=2,
        start="07:15",
        end="07:30",
        exertion="heavy",
        location_id="loc-job",
        policy_rule_ids=rule_ids or [],
    )


def _recovery(job_id: str, *, crew_id: str = "crew-a") -> TimelineSegment:
    return TimelineSegment(
        crew_id=crew_id,
        state=TimelineState.RECOVERY,
        job_id=job_id,
        start_slot=2,
        end_slot=3,
        start="07:30",
        end="07:45",
        location_id="loc-job",
    )


def _with_facts(
    facts: PlanFacts,
    *,
    jobs: tuple[JobResult, ...],
    timeline_segments: tuple[TimelineSegment, ...] = (),
    conflicts: ConflictEvidence | None = None,
) -> PlanFacts:
    return replace(
        facts,
        jobs=jobs,
        timeline_segments=timeline_segments,
        conflicts=conflicts or facts.conflicts,
    )


def test_derives_all_six_changes_in_stable_id_order() -> None:
    facts = build_facts(elevated=True)
    before = _with_facts(
        facts,
        jobs=(
            _job("job-a", served=True, crew_id="crew-a", start="07:15", end="08:00"),
            _job("job-b", served=True, crew_id="crew-a", start="07:15", end="08:00"),
            _job("job-c", served=False),
            _job("job-d", served=True, crew_id="crew-a", start="07:15", end="08:00"),
            _job("job-e", served=True, crew_id="crew-a", start="07:15", end="08:00"),
            _job("job-f", served=True, crew_id="crew-a", start="07:15", end="08:00"),
        ),
        timeline_segments=(_work("job-e"),),
        conflicts=ConflictEvidence(
            count=1,
            rule_ids=("rule-heavy-elevated",),
            job_ids=("job-b",),
            conflicts=(
                PolicyConflict(
                    crew_id="crew-a",
                    window_start_slot=1,
                    window_end_slot=5,
                    rule_ids=("rule-heavy-elevated",),
                    job_ids=("job-b",),
                ),
            ),
        ),
    )
    after = _with_facts(
        facts,
        jobs=(
            _job("job-a", served=True, crew_id="crew-a", start="07:15", end="08:00"),
            _job("job-b", served=False),
            _job("job-c", served=True, crew_id="crew-a", start="07:15", end="08:00"),
            _job("job-d", served=True, crew_id="crew-b", start="07:30", end="08:15"),
            _job("job-e", served=True, crew_id="crew-a", start="07:15", end="08:15"),
            _job("job-f", served=True, crew_id="crew-a", start="07:30", end="08:15"),
        ),
        timeline_segments=(
            _work("job-c", rule_ids=["rule-heavy-elevated"]),
            _work("job-d", crew_id="crew-b", rule_ids=["rule-heavy-elevated"]),
            _work("job-e", rule_ids=["rule-heavy-elevated"]),
            _recovery("job-e"),
            _work("job-f", rule_ids=["rule-heavy-elevated"]),
        ),
    )

    differences = derive_plan_diff(before, after)

    assert [difference.job_id for difference in differences] == [
        "job-a",
        "job-b",
        "job-c",
        "job-d",
        "job-e",
        "job-f",
    ]
    assert [difference.change.value for difference in differences] == [
        "unchanged",
        "deferred",
        "served",
        "moved_crew",
        "recovery_added",
        "moved_time",
    ]
    assert differences[1].before is not None and differences[1].after is None
    assert differences[1].binding_rule_ids == ["rule-heavy-elevated"]
    assert differences[1].explanation_code == "POLICY_CAPACITY_CONFLICT"
    assert differences[3].before is not None and differences[3].after is not None
    assert differences[3].binding_rule_ids == ["rule-heavy-elevated"]
    assert differences[4].change.value == "recovery_added"
    assert differences[4].binding_rule_ids == ["rule-heavy-elevated"]


def test_precedence_prefers_crew_change_over_recovery_and_time() -> None:
    facts = build_facts()
    before = _with_facts(
        facts,
        jobs=(_job("job-a", served=True, crew_id="crew-a", start="07:15", end="07:30"),),
        timeline_segments=(_work("job-a"),),
    )
    after = _with_facts(
        facts,
        jobs=(_job("job-a", served=True, crew_id="crew-b", start="07:30", end="08:00"),),
        timeline_segments=(_work("job-a", crew_id="crew-b"), _recovery("job-a", crew_id="crew-b")),
    )

    difference = derive_plan_diff(before, after)[0]

    assert difference.change.value == "moved_crew"
