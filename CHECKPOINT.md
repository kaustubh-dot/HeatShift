# Checkpoint

**Last updated:** 2026-08-02
**Phase:** Planning frozen; backend implementation underway
**Overall status:** B11 complete; B12 active

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
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, independent policy reconciliation, service orchestration, evidence-backed plan differences, and forced-inclusion diagnosis now exist; API/frontend work has not started.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: B11
- Verification commands:
  - `.venv/bin/python -m pytest tests/unit/test_diagnostics.py -q`
  - `.venv/bin/python -m pytest tests/unit tests/integration -q`
  - `.venv/bin/python -m compileall -q backend/heatshift`
  - `git diff --check`
- Results: `6 passed in 0.35s`; `77 passed in 0.43s`; compileall passed; `git diff --check` passed.
- Canonical deferred-job diagnosis command:
  - `.venv/bin/python -c 'import json; from pathlib import Path; from backend.heatshift.metrics import extract_plan_facts; from backend.heatshift.models import Policy, Scenario; from backend.heatshift.optimizer import build_optimizer_model, solve_staged; from backend.heatshift.patterns import generate_policy_constrained_patterns; from backend.heatshift.diagnostics import diagnose_job; root=Path("backend/heatshift/fixtures"); scenario=Scenario.model_validate(json.loads((root/"scenario.json").read_text())); policy=Policy.model_validate(json.loads((root/"policy.json").read_text())); model=build_optimizer_model(scenario, policy, generate_policy_constrained_patterns(scenario, policy), enforce_policy=True); result=solve_staged(model, 5); facts=extract_plan_facts(model, result); target=next(job.job_id for job in facts.jobs if not job.served); diagnosis=diagnose_job(scenario, policy, facts, result, target, time_limit_seconds=5); print("target", target, "classification", diagnosis.classification.value, "proof", diagnosis.proof_status.value, "binding", diagnosis.binding_rule_ids, "displaced", diagnosis.displaced_job_ids, "delta", diagnosis.objective_delta.model_dump())'`
- Canonical diagnosis result: target `job-bus-route`; classification `proven_infeasible`; proof `INFEASIBLE`; binding IDs `['hs01-heavy-elevated', 'hs01-heavy-normal', 'hs01-heavy-severe']`; displaced IDs `[]`; objective delta `{critical_service: 0, planned_service_value: 0, travel_minutes: 0, overtime_minutes: 0}`.
- Files created/changed: `backend/heatshift/diagnostics.py`, `tests/unit/test_diagnostics.py`, `TODO.md`, `CHECKPOINT.md`
- Known limitation: bounded interventions, API routes, saved evidence, and frontend work remain later packets. The untuned full fixture can prove a forced-inclusion infeasibility under retained critical service rather than produce a forced incumbent.
- Next task: B12 — Bounded interventions

## Immediate next action

Execute **B12 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/BACKEND_IMPLEMENTATION_PLAN.md](docs/BACKEND_IMPLEMENTATION_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish until the solver release gates in [docs/TEST_PLAN.md](docs/TEST_PLAN.md) pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
