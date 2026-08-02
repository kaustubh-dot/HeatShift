"""Evidence-backed differences between two reconciled plan fact sets."""

from __future__ import annotations

from collections.abc import Iterable

from .metrics import PlanFacts
from .models import JobResult, PlanChange, PlanDiff, PlanJobState, TimelineState


def derive_plan_diff(before: PlanFacts, after: PlanFacts) -> list[PlanDiff]:
    """Classify every job's change from ``before`` to ``after``.

    The input fact sets are deliberately kept separate from serialized plans so
    that rule evidence comes from extracted solver/evaluator facts rather than
    from labels, colors, or job names.
    """

    before_jobs = _index_jobs(before.jobs)
    after_jobs = _index_jobs(after.jobs)
    job_ids = sorted(set(before_jobs) | set(after_jobs))
    differences: list[PlanDiff] = []

    for job_id in job_ids:
        before_job = before_jobs.get(job_id)
        after_job = after_jobs.get(job_id)
        change = _classify_change(
            before_job,
            after_job,
            before_recovery_slots=_recovery_slots(before, job_id),
            after_recovery_slots=_recovery_slots(after, job_id),
        )
        differences.append(
            PlanDiff(
                job_id=job_id,
                change=change,
                before=_job_state(before_job),
                after=_job_state(after_job),
                binding_rule_ids=_binding_rule_ids(
                    change,
                    job_id,
                    before=before,
                    after=after,
                ),
                explanation_code=_explanation_code(change, before, job_id),
            )
        )

    return differences


def derive_plan_differences(before: PlanFacts, after: PlanFacts) -> list[PlanDiff]:
    """Descriptive alias for callers that prefer the plural operation name."""

    return derive_plan_diff(before, after)


def _index_jobs(jobs: Iterable[JobResult]) -> dict[str, JobResult]:
    indexed: dict[str, JobResult] = {}
    for job in jobs:
        if job.job_id in indexed:
            raise ValueError(f"duplicate job result {job.job_id!r}")
        indexed[job.job_id] = job
    return indexed


def _classify_change(
    before: JobResult | None,
    after: JobResult | None,
    *,
    before_recovery_slots: frozenset[int],
    after_recovery_slots: frozenset[int],
) -> PlanChange:
    before_served = before is not None and before.served
    after_served = after is not None and after.served

    if before_served and not after_served:
        return PlanChange.DEFERRED
    if not before_served and after_served:
        return PlanChange.SERVED

    if not before_served or not after_served:
        return PlanChange.UNCHANGED

    if before.crew_id != after.crew_id:
        return PlanChange.MOVED_CREW

    same_start = before.start == after.start
    if same_start and len(after_recovery_slots) > len(before_recovery_slots):
        return PlanChange.RECOVERY_ADDED

    if before.start != after.start or before.end != after.end:
        return PlanChange.MOVED_TIME

    return PlanChange.UNCHANGED


def _job_state(job: JobResult | None) -> PlanJobState | None:
    if job is None or not job.served:
        return None
    return PlanJobState(crew_id=job.crew_id, start=job.start, end=job.end)


def _recovery_slots(facts: PlanFacts, job_id: str) -> frozenset[int]:
    return frozenset(
        slot
        for segment in facts.timeline_segments
        if segment.job_id == job_id and segment.state is TimelineState.RECOVERY
        for slot in range(segment.start_slot, segment.end_slot)
    )


def _binding_rule_ids(
    change: PlanChange,
    job_id: str,
    *,
    before: PlanFacts,
    after: PlanFacts,
) -> list[str]:
    if change in {
        PlanChange.MOVED_CREW,
        PlanChange.MOVED_TIME,
        PlanChange.RECOVERY_ADDED,
    }:
        return _after_pattern_rule_ids(after, job_id)
    if change is PlanChange.DEFERRED:
        return _baseline_conflict_rule_ids(before, job_id)
    return []


def _after_pattern_rule_ids(facts: PlanFacts, job_id: str) -> list[str]:
    rule_ids = {
        rule_id
        for segment in facts.timeline_segments
        if segment.job_id == job_id and segment.state is TimelineState.WORK
        for rule_id in segment.policy_rule_ids
    }
    return sorted(rule_ids)


def _baseline_conflict_rule_ids(facts: PlanFacts, job_id: str) -> list[str]:
    rule_ids = {
        rule_id
        for conflict in facts.conflicts.conflicts
        if job_id in conflict.job_ids
        for rule_id in conflict.rule_ids
    }
    return sorted(rule_ids)


def _explanation_code(change: PlanChange, facts: PlanFacts, job_id: str) -> str:
    if change is PlanChange.DEFERRED and _baseline_conflict_rule_ids(facts, job_id):
        return "POLICY_CAPACITY_CONFLICT"
    return change.value.upper()
