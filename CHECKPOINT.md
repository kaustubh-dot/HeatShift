# Checkpoint

**Last updated:** 2026-08-01
**Phase:** Planning frozen; backend implementation underway
**Overall status:** B00 complete; B01 active

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
- No application logic, scenario fixture, solver output, tests, or frontend exists yet; B00 environment files are present.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: B00
- Verification commands and results:
  - `/opt/homebrew/bin/python3.12 --version` → `Python 3.12.13`
  - `/opt/homebrew/bin/python3.12 -m venv .venv` → exit 0
  - `.venv/bin/python -m ensurepip --upgrade` → pip 26.1.2 available
  - `.venv/bin/python -m pip install ortools pydantic fastapi uvicorn` → installed OR-Tools 9.15.6755, Pydantic 2.13.4, FastAPI 0.141.1, Uvicorn 0.52.0
  - `.venv/bin/python -m pip install pytest httpx` → installed Pytest 9.1.1 and HTTPX 0.28.1
  - `.venv/bin/python -c "import ortools, pydantic, fastapi, pytest; print('imports-ok')"` → `imports-ok`
  - `.venv/bin/python -m pip check` → `No broken requirements found.`
- Files created/changed: `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/heatshift/__init__.py`, `TODO.md`, `CHECKPOINT.md`
- Known limitation: None
- Next task: B01 — Canonical Pydantic models

## Immediate next action

Execute **B01 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/BACKEND_IMPLEMENTATION_PLAN.md](docs/BACKEND_IMPLEMENTATION_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish until the solver release gates in [docs/TEST_PLAN.md](docs/TEST_PLAN.md) pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
