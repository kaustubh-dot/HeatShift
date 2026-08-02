# Checkpoint

**Last updated:** 2026-08-03
**Phase:** Planning frozen; backend implementation underway
**Overall status:** B16 complete; B17 active

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
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, independent policy reconciliation, service orchestration, evidence-backed plan differences, forced-inclusion diagnosis, bounded interventions, +2°C heat shock, declared scenario-tuning evidence, deterministic saved solver evidence, and the three FastAPI routes now exist; frontend work has not started.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: B16
- Verification commands:
  - `.venv/bin/python -m pytest tests/integration/test_api.py -q`
  - `.venv/bin/python -m pytest tests/unit tests/integration -q`
  - `.venv/bin/python -m compileall -q backend/heatshift tests`
  - `git diff --check`
  - `TestClient` smoke checks for `/healthz` and `/api/demo`
- Results: `13 passed in 11.95s`; the full suite reported `96 passed in 51.27s`; compileall passed; `git diff --check` passed; `/healthz` and `/api/demo` returned HTTP `200`.
- B16 routes: `GET /api/demo` returns the bundled scenario, policy, schematic coordinates, and saved-result metadata; `POST /api/solve` returns the canonical `SolveResponse`; `POST /api/diagnose` returns the canonical `DiagnosisResponse`; `GET /healthz` returns only process readiness.
- B16 error evidence: request/Pydantic and cross-reference failures return the common envelope with HTTP `422`; `SOLVER_TIMEOUT` maps to `504`; `NO_FEASIBLE_PLAN` maps to `409`; `MODEL_INVALID` and `INTERNAL_ERROR` map to `500`. Unknown diagnosis IDs are rejected before solver construction.
- B15 saved evidence remains canonical under [backend/heatshift/fixtures/saved](backend/heatshift/fixtures/saved), and `/api/demo` exposes its base-result metadata without treating metadata as a solve response.
- Known limitation: the pinned FastAPI/HTTPX test stack emits one upstream Starlette deprecation warning for `TestClient`; the endpoint tests and runtime behavior pass. Frontend work remains later packets.
- Next task: B17 — Backend release gate

## Immediate next action

Execute **B17 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/BACKEND_IMPLEMENTATION_PLAN.md](docs/BACKEND_IMPLEMENTATION_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish until the solver release gates in [docs/TEST_PLAN.md](docs/TEST_PLAN.md) pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
