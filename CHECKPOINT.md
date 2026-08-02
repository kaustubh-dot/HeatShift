# Checkpoint

**Last updated:** 2026-08-02
**Phase:** Planning frozen; backend implementation underway
**Overall status:** B10 complete; B11 active

## Locked product

**HeatShift: Policy-Constrained Service Optimizer**

HeatShift computes the highest municipal maintenance service achievable under an employer-defined heat policy, then uses counterfactual optimization to show the operational cost of including each deferred work order.

## Decisions already made

- Sustainability & Climate Tech track
- Municipal planned-maintenance supervisor as the sole launch persona
- Pre-formed crews with attached capabilities and equipment
- One-day, 15-minute-slot planning horizon
- Recovery-interruptible, crew-committed jobs
- Synthetic employer policy for the deterministic demo
- Service-first counterfactual versus policy-constrained plan
- CP-SAT with staged lexicographic optimization
- Forced-inclusion counterfactuals for deferred work
- Schematic service map using input travel times, not street-level navigation
- React/TypeScript frontend and Python/FastAPI solver service
- One application with three click-driven chapters

## Important modelling correction

Per-job execution patterns do not by themselves prove rolling policy compliance across consecutive jobs. Selected patterns expose work and recovery slots, while the global solver must enforce rolling work/recovery constraints across the complete crew timeline, including gaps and transitions.

## Implementation-readiness corrections frozen

The final planning pass made previously implicit behavior explicit:

- policy-owned inclusive heat-band thresholds;
- policy-approved recovery-profile IDs;
- explicit directed travel-matrix row/column IDs;
- independent locked service, crew, and start fields;
- exact zero-adjustment versus heat-shock response semantics; and
- a fifth housekeeping objective that minimizes standalone recovery only after the four required objectives are fixed.

## Current evidence

- Product and engineering specifications exist under `docs/`.
- `docs/DESIGN.md` and `docs/FRONTEND_PLAN.md` have been reviewed for judge clarity, accessibility, contract fidelity, offline presentation, and deadline feasibility.
- `docs/IMPLEMENTATION_MASTER_PLAN.md` and `docs/BACKEND_IMPLEMENTATION_PLAN.md` define atomic, gated tasks for low-context implementation agents.
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, independent policy reconciliation, service orchestration, and evidence-backed plan differences now exist; API/frontend work has not started.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: B10
- Verification commands:
  - `.venv/bin/python -m pytest tests/unit/test_differences.py tests/integration/test_solve_service.py -q`
  - `.venv/bin/python -m pytest tests/unit tests/integration -q`
  - `.venv/bin/python -m compileall -q backend/heatshift`
  - `git diff --check`
-- Results: `6 passed in 0.35s`; `71 passed in 0.40s`; compileall passed; `git diff --check` passed.
- Full-fixture service smoke command:
  - `.venv/bin/python -c 'import json; from pathlib import Path; from backend.heatshift.models import Policy, Scenario; from backend.heatshift.service import solve_scenario; root=Path("backend/heatshift/fixtures"); scenario=Scenario.model_validate(json.loads((root/"scenario.json").read_text())); policy=Policy.model_validate(json.loads((root/"policy.json").read_text())); response=solve_scenario(scenario, policy, heat_adjustment_c=0, time_limit_seconds=5); print("status", response.plans.service_first.status.value, response.plans.policy_constrained.status.value); print("changes", [(item.job_id, item.change.value, item.binding_rule_ids) for item in response.plan_diff]); print("count", len(response.plan_diff), "jobs", len(scenario.jobs))'`
- Full-fixture result: `status FEASIBLE OPTIMAL`; 12 diff records for 12 jobs, including `moved_time`, `deferred`, `served`, `unchanged`, and evidence-backed rule IDs such as `hs01-heavy-elevated` and `hs01-moderate-normal`.
- Files created/changed: `backend/heatshift/differences.py`, `backend/heatshift/service.py`, `tests/unit/test_differences.py`, `tests/integration/test_solve_service.py`, `TODO.md`, `CHECKPOINT.md`
- Known limitation: forced-inclusion diagnosis, API routes, saved evidence, and frontend work remain later packets. The untuned full fixture can return a bounded `FEASIBLE` baseline rather than a proven optimum.
- Next task: B11 — Forced-inclusion diagnosis

## Immediate next action

Execute **B11 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/BACKEND_IMPLEMENTATION_PLAN.md](docs/BACKEND_IMPLEMENTATION_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish until the solver release gates in [docs/TEST_PLAN.md](docs/TEST_PLAN.md) pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
