# Roadmap

The roadmap is gate-driven. Planning is frozen; implementation follows the task IDs in [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md).

## Phase 0 — Locked specifications

**Status:** Complete

Deliverables:

- Product requirements
- Architecture and solver specification
- Data/API contracts
- Demo scenario definition
- Test, safety, demo, detailed design, and deadline-scoped frontend plan
- Master and backend execution plans with atomic task packets

Exit gate: all documents use the same user, scope, terminology, solver claims, and safety boundary.

## Phase 1 — Headless solver spike

**Status:** Next — begin B00

Deliverables:

- `scenario.json` and `policy.json`
- Schema validation
- Valid execution-pattern generator
- Global rolling work/recovery constraints
- Crew/equipment eligibility
- Travel/order model with depot legs
- Staged lexicographic optimization
- Service-first and policy-constrained results
- Deferred-job counterfactual
- +2 C heat-shock result
- Deterministic JSON output and focused tests

Exit gate:

- Recommended plan has zero mandatory conflicts.
- At least one critical job is retained through a meaningful reschedule.
- At least two visible schedule changes occur.
- At least one deferred job has a solver-derived counterfactual.
- Heat shock changes at least one meaningful decision.
- Travel is matrix-derived and route-continuous.
- Solver status and proof claims are honest.
- Runtime is suitable for a live demo on the development laptop.

If this gate fails, tune the evidence-informed scenario once without changing solver rules. Pivot only when no credible nontrivial scenario can pass.

## Phase 2 — Static visual foundation

**Status:** Blocked by Gate G2/B15

Build the three frontend chapters using saved solver JSON:

1. Tomorrow's Brief
2. Plan Transformation
3. Why / What-if

Deliverables:

- Typography, palette, layout, and motion tokens
- Schematic SVG service map
- Crew timelines and heat bands
- Baseline-to-plan diff animation
- Counterfactual diagnosis panel
- Reduced-motion behavior

Exit gate: a judge understands the problem and before/after result in under thirty seconds without narration.

## Phase 3 — API integration

**Status:** Blocked by Gate G4/F09 for UI integration and Gate G3/B16 for live endpoints

Deliverables:

- `GET /api/demo`
- `POST /api/solve`
- `POST /api/diagnose`
- Loading, validation, timeout, feasible-only, and infeasible states
- Live +2 C heat-shock rerun
- One-process production build

Exit gate: the full critical journey works from a fresh start without manually editing files or restarting services.

## Phase 4 — Judge polish and release

**Status:** Blocked by Gate G4/F12

Deliverables:

- Performance and accessibility pass
- Deterministic deployment/fallback path
- Architecture diagram and README evidence
- Three-to-five-minute demo video
- Devpost description, screenshots, repository, and installation guide

Exit gate: the recorded and live demo both complete without network-dependent data or fabricated metrics.
