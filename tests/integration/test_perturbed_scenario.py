from __future__ import annotations

import json
from pathlib import Path

from backend.heatshift.models import Policy, Scenario, SolverStatus
from backend.heatshift.service import solve_scenario
from backend.heatshift.validation import validate_scenario


FIXTURE_DIR = Path(__file__).parents[2] / "backend" / "heatshift" / "fixtures"


def test_perturbed_fixture_validates_and_solves_without_hardcoded_output() -> None:
    scenario = Scenario.model_validate(
        json.loads((FIXTURE_DIR / "perturbed-scenario.json").read_text(encoding="utf-8"))
    )
    policy = Policy.model_validate(
        json.loads((FIXTURE_DIR / "policy.json").read_text(encoding="utf-8"))
    )

    assert validate_scenario(scenario, policy) == []

    response = solve_scenario(
        scenario,
        policy,
        heat_adjustment_c=0,
        time_limit_seconds=5,
    )
    plan = response.plans.policy_constrained

    assert plan.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert plan.metrics.mandatory_policy_conflicts == 0
    assert {job.job_id for job in plan.jobs} == {job.id for job in scenario.jobs}
    assert any(job.served for job in plan.jobs)
