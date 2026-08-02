# Checkpoint

**Last updated:** 2026-08-03
**Phase:** Planning frozen; backend implementation underway
**Overall status:** B14 complete; B15 active

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
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, independent policy reconciliation, service orchestration, evidence-backed plan differences, forced-inclusion diagnosis, bounded interventions, +2°C heat shock, and the declared scenario-tuning evidence now exist; API/frontend work has not started.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: B14
- Verification commands:
  - `.venv/bin/python -m pytest tests/integration/test_perturbed_scenario.py -q`
  - `.venv/bin/python -m pytest tests/unit tests/integration -q`
  - `.venv/bin/python -m compileall -q backend/heatshift tests`
  - `git diff --check`
- `.venv/bin/python` exact structural comparison of `scenario.json` and `perturbed-scenario.json`
- one `.venv/bin/python` diagnostic command printing objective/status vectors, served/deferred IDs, conflicts/rules, route order/travel, recovery minutes, base diff types, diagnosis, and +2°C changes
- Results: `1 passed in 5.74s`; `82 passed in 5.90s`; compileall passed; `git diff --check` passed; the perturbation comparison reported exactly `jobs.7.active_minutes: 30->45` and `change_count=1`.
- B14 fixture tuning: one cohesive permitted input adjustment changed source heat slots 2–4 (`07:30`–`08:00`) from 30°C to 29°C. No policy, solver, objective, eligibility, lock, or output semantics changed. The reason and the before/after record are in [backend/heatshift/fixtures/TUNING.md](backend/heatshift/fixtures/TUNING.md).
- B14 primary diagnostic result: service-first `FEASIBLE`, 4 critical jobs, service value `400`, 11 conflicts, 82 travel minutes; policy-constrained `OPTIMAL`, 3 critical jobs, service value `368`, zero conflicts, 160 travel minutes; base diff includes `moved_time`, `deferred`, and `served`; `job-bus-route` diagnosis is `proven_infeasible` / `INFEASIBLE`.
- B14 heat-shock result: +2°C `heat_shock` is `OPTIMAL`, zero conflicts, 60 eligible recovery minutes, and seven decision changes including `recovery_added` for `job-catch-basin` and `job-school-potholes`.
- Perturbation result: `perturbed-scenario.json` validates with zero issues and solves with a reportable zero-conflict policy-constrained plan; `tests/integration/test_perturbed_scenario.py` checks this from computed model output rather than canned demo values.
- B13 integration evidence: exact source temperatures `[30, 36, 40]` became `[32, 38, 42]` with bands `[elevated, severe, extreme]`; the original heat series remained unchanged. A +2°C solve preserved the unadjusted policy plan fields and compared that plan to `heat_shock` in `plan_diff`.
- Files created/changed: `backend/heatshift/fixtures/scenario.json`, `backend/heatshift/fixtures/perturbed-scenario.json`, `backend/heatshift/fixtures/TUNING.md`, `tests/integration/test_perturbed_scenario.py`, `TODO.md`, `CHECKPOINT.md`
- Known limitation: solver wall times and incumbent-vs-optimal status can vary with the configured time budget; B15 will normalize documented runtime fields for deterministic saved-output comparison. API routes and frontend work remain later packets.
- Next task: B15 — Deterministic saved evidence

## Immediate next action

Execute **B15 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/BACKEND_IMPLEMENTATION_PLAN.md](docs/BACKEND_IMPLEMENTATION_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish until the solver release gates in [docs/TEST_PLAN.md](docs/TEST_PLAN.md) pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
