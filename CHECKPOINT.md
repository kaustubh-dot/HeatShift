# Checkpoint

**Last updated:** 2026-08-02
**Phase:** Planning frozen; backend implementation underway
**Overall status:** B08 complete; B09 active

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
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, and independent policy reconciliation now exist; service/API/frontend work has not started.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: B08
- Verification commands:
  - `.venv/bin/python -m pytest tests/unit/test_metrics_and_serialization.py -q`
  - `.venv/bin/python -m pytest tests/unit -q`
  - `.venv/bin/python -m compileall -q backend/heatshift`
  - `git diff --check`
- Results: `4 passed in 0.57s`; `65 passed in 0.65s`; compileall passed; `git diff --check` passed.
- Full-fixture extraction smoke: `27` timeline segments, `10` route segments, `12` stable job results, metrics `{critical_jobs_scheduled: 3, critical_jobs_total: 4, planned_service_value: 368, mandatory_policy_conflicts: 0, travel_minutes: 160, overtime_minutes: 0, active_work_minutes: 390, eligible_recovery_minutes: 0}`, independent conflict count `0`, elapsed `2.837s` from pattern generation through reconciliation.
- Files created/changed: `backend/heatshift/metrics.py`, `tests/unit/test_metrics_and_serialization.py`, `TODO.md`, `CHECKPOINT.md`
- Known limitation: Extracted facts are not yet wrapped in `Plan`/`SolveResponse` service orchestration; API routes and diagnosis remain later packets.
- Next task: B09 — Solve orchestration

## Immediate next action

Execute **B09 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/BACKEND_IMPLEMENTATION_PLAN.md](docs/BACKEND_IMPLEMENTATION_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish until the solver release gates in [docs/TEST_PLAN.md](docs/TEST_PLAN.md) pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
