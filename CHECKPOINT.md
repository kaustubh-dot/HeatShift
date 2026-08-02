# Checkpoint

**Last updated:** 2026-08-03
**Phase:** Phase 1 complete; frontend implementation next
**Overall status:** B17 complete; F00 active

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
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, independent policy reconciliation, service orchestration, evidence-backed plan differences, forced-inclusion diagnosis, bounded interventions, +2°C heat shock, declared scenario-tuning evidence, deterministic saved solver evidence, the three FastAPI routes, and the backend release report now exist; frontend work has not started.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: B17
- Verification commands:
  - `.venv/bin/python -m pip install -r backend/requirements-dev.txt`
  - `.venv/bin/python -m pytest -q`
  - `.venv/bin/python -m backend.heatshift.cli validate`
  - `.venv/bin/python -m backend.heatshift.cli generate-saved` (run twice in separate temporary directories)
  - `.venv/bin/python -m pip check`
  - `.venv/bin/python -m compileall -q backend/heatshift tests`
  - `git diff --check`
  - `/healthz` and `/api/demo` smoke checks remain covered by the full suite
- Results: dependency installation exited 0; `96 passed in 41.42s`; fixture validation returned `valid: true` with no issues; `generate-saved` exited 0 twice with equal input and canonical output hashes; `pip check` returned `No broken requirements found.`; compileall and `git diff --check` passed. The pinned FastAPI/HTTPX test stack emits one upstream Starlette deprecation warning.
- B17 solver evidence: service-first `FEASIBLE` with 4/4 critical jobs, value 400, 11 conflicts, and 82 travel minutes; policy-constrained `OPTIMAL` with 3/4 critical jobs, value 368, zero conflicts, and 160 travel minutes; designated `job-bus-route` diagnosis `proven_infeasible` / `INFEASIBLE`; +2°C heat-shock `OPTIMAL` with zero conflicts, 60 eligible recovery minutes, and meaningful schedule changes.
- B17 wall times: base 3.682s, diagnosis 5.843s, and heat shock 4.000s. Independent base branches run concurrently with separate budgets and deterministic one-worker solver configuration.
- B17 canonical output hashes: base `f2fc17217539af49025a62aca91953eb5e8c87e7b3eff2cbd2af68f249c66cba`; diagnosis `de9526bf89fc5ec31d622db2b05db0b6fb3a893cbe2b643572bf017087859420`; heat shock `378baffd2ad1a76a1688268c4a89950dbb6a4d2127f8124bbe25f43942cb2615`.
- B16 routes and error mappings remain covered: `GET /healthz`, `GET /api/demo`, `POST /api/solve`, and `POST /api/diagnose`; invalid input returns `422`, timeout `504`, no feasible plan `409`, and model/internal failures `500`.
- B15 saved evidence remains canonical under [backend/heatshift/fixtures/saved](backend/heatshift/fixtures/saved), and the release report is [backend/RELEASE_EVIDENCE.md](backend/RELEASE_EVIDENCE.md).
- Known limitations: synthetic policy and scenario; no medical, legal, workplace-safety, or regulatory certification; one-day 15-minute horizon; small pre-formed crews/jobs; matrix travel and schematic map; simplified recovery; no uncertainty beyond +2°C; bounded interventions; and solver-status/time-limit-dependent optimality. Frontend work remains.
- Next task: F00 — React/Vite shell and pinned environment

## Immediate next action

Execute **F00 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/FRONTEND_PLAN.md](docs/FRONTEND_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish beyond the active frontend packet until its packet-specific acceptance commands pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
