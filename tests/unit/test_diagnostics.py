from __future__ import annotations

import pytest

from backend.heatshift.diagnostics import DiagnosisValidationError, diagnose_job
from backend.heatshift.metrics import extract_plan_facts
from backend.heatshift.models import DiagnosisClassification, SolverStatus
from backend.heatshift.optimizer import build_optimizer_model, solve_staged
from backend.heatshift.patterns import generate_policy_constrained_patterns
from tests.unit.test_patterns import make_case


def _solve_original(scenario, policy, *, time_limit_seconds: float = 5):
    model = build_optimizer_model(
        scenario,
        policy,
        generate_policy_constrained_patterns(scenario, policy),
        enforce_policy=True,
    )
    result = solve_staged(model, time_limit_seconds)
    facts = extract_plan_facts(model, result)
    return facts, result


def _two_job_case(*, target_value: int = 8):
    scenario, policy = make_case(
        ["normal"] * 8,
        active_minutes=45,
        window_start_slot=1,
        window_end_slot=4,
    )
    scenario.jobs.append(
        scenario.jobs[0].model_copy(
            deep=True,
            update={
                "id": "job-b",
                "name": "Job B",
                "service_value": target_value,
            },
        )
    )
    return scenario, policy


def test_equivalent_alternative_preserves_proven_objective_vector() -> None:
    scenario, policy = _two_job_case()
    original_facts, original_result = _solve_original(scenario, policy)

    served_job_id = next(job.job_id for job in original_facts.jobs if job.served)
    deferred_job_id = next(job.job_id for job in original_facts.jobs if not job.served)
    diagnosis = diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        deferred_job_id,
        time_limit_seconds=5,
    )

    assert diagnosis.classification is DiagnosisClassification.EQUIVALENT_ALTERNATIVE
    assert diagnosis.proof_status is SolverStatus.OPTIMAL
    assert diagnosis.displaced_job_ids == [served_job_id]
    assert diagnosis.objective_delta.planned_service_value == 0
    assert diagnosis.binding_rule_ids == ["rule-heavy-normal"]
    assert diagnosis.retained_commitments == [
        "all-mandatory-rules",
        "original-critical-service-count",
        f"forced-job:{deferred_job_id}",
    ]


def test_forced_inclusion_with_lower_service_value_reports_cost_and_displacement() -> None:
    scenario, policy = _two_job_case(target_value=3)
    scenario.jobs[0].service_value = 10
    original_facts, original_result = _solve_original(scenario, policy)

    diagnosis = diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        "job-b",
        time_limit_seconds=5,
    )

    assert diagnosis.classification is DiagnosisClassification.FEASIBLE_WITH_COST
    assert diagnosis.displaced_job_ids == ["job-a"]
    assert diagnosis.objective_delta.planned_service_value == -7


def test_infeasible_forced_inclusion_is_proven_only_by_infeasible_status() -> None:
    scenario, policy = make_case(
        ["normal"] * 8,
        active_minutes=45,
        window_start_slot=1,
        window_end_slot=2,
    )
    original_facts, original_result = _solve_original(scenario, policy)

    diagnosis = diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        "job-a",
        time_limit_seconds=5,
    )

    assert diagnosis.classification is DiagnosisClassification.PROVEN_INFEASIBLE
    assert diagnosis.proof_status is SolverStatus.INFEASIBLE
    assert diagnosis.displaced_job_ids == []


def test_time_limited_forced_inclusion_is_not_proven_without_an_incumbent() -> None:
    scenario, policy = _two_job_case()
    original_facts, original_result = _solve_original(scenario, policy)
    deferred_job_id = next(job.job_id for job in original_facts.jobs if not job.served)

    diagnosis = diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        deferred_job_id,
        time_limit_seconds=0,
    )

    assert diagnosis.classification is DiagnosisClassification.NOT_PROVEN
    assert diagnosis.proof_status is SolverStatus.UNKNOWN
    assert diagnosis.objective_delta.planned_service_value == 0


def test_unknown_and_already_served_job_ids_return_structured_details() -> None:
    scenario, policy = _two_job_case()
    original_facts, original_result = _solve_original(scenario, policy)
    served_job_id = next(job.job_id for job in original_facts.jobs if job.served)

    with pytest.raises(DiagnosisValidationError) as unknown:
        diagnose_job(scenario, policy, original_facts, original_result, "job-missing")
    assert unknown.value.details[0].path == "job_id"
    assert unknown.value.details[0].code == "UNKNOWN_REFERENCE"

    with pytest.raises(DiagnosisValidationError) as served:
        diagnose_job(scenario, policy, original_facts, original_result, served_job_id)
    assert served.value.details[0].path == "job_id"
    assert served.value.details[0].code == "ALREADY_SERVED"


def test_heat_adjustment_does_not_mutate_original_scenario() -> None:
    scenario, policy = _two_job_case()
    original_heat = scenario.model_dump(mode="json")["heat_series"]
    original_facts, original_result = _solve_original(scenario, policy)
    deferred_job_id = next(job.job_id for job in original_facts.jobs if not job.served)

    diagnose_job(
        scenario,
        policy,
        original_facts,
        original_result,
        deferred_job_id,
        heat_adjustment_c=2,
        time_limit_seconds=5,
    )

    assert scenario.model_dump(mode="json")["heat_series"] == original_heat
