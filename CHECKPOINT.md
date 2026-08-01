# Checkpoint

**Last updated:** 2026-08-01
**Phase:** Planning frozen; B00 is next
**Overall status:** Product, contracts, design, and implementation sequence locked

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
- No application code, scenario fixture, solver output, tests, or frontend exists yet.
- A partially created `.venv` from the aborted implementation start was removed; the workspace remains documentation-only.
- The workspace was not a Git repository at the time of this checkpoint.

## Immediate next action

Execute **B00 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/BACKEND_IMPLEMENTATION_PLAN.md](docs/BACKEND_IMPLEMENTATION_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish until the solver release gates in [docs/TEST_PLAN.md](docs/TEST_PLAN.md) pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
