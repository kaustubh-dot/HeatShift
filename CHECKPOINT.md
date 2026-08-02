# Checkpoint

**Last updated:** 2026-08-03
**Phase:** Phase 2 frontend implementation underway
**Overall status:** F04 complete; F05 active

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
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, independent policy reconciliation, service orchestration, evidence-backed plan differences, forced-inclusion diagnosis, bounded interventions, +2°C heat shock, declared scenario-tuning evidence, deterministic saved solver evidence, the three FastAPI routes, the backend release report, the pinned React/Vite shell, canonical frontend contract types, genuine fallback loading, reducer-owned state, approved design tokens, local licensed fonts, semantic chapter navigation, the shared TrustBar, the scenario-derived Tomorrow's Brief, and the complete-day accessible timeline now exist.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `agent/lock-planning-docs`.

## Active implementation checkpoint

- Last completed task: F04
- Verification commands:
  - `cd frontend && npm ci`
  - `cd frontend && npm run test:run`
  - `cd frontend && npm run build`
  - `cmp backend/heatshift/fixtures/saved/demo-bundle.json frontend/public/fallback/demo.json`
- Results: `npm ci` exited 0 and audited 130 packages with 0 vulnerabilities; `npm run test:run` reported `11 passed`; `npm run build` exited 0 and produced the Vite production bundle; `cmp` remains passed; no font CDN references were found. Exact dependency pins are recorded in `frontend/package.json` and the lockfile. npm reports only its install-script review notices and one transitive deprecation warning.
- F00 shell: React 19.2.8, TypeScript 5.9.3, Vite 8.1.5, `lucide-react` 1.17.0, Vitest 3.2.7, React Testing Library 16.3.0, DOM matchers 6.8.0, and jsdom 26.1.0. No router, state library, HTTP library, animation package, or CSS framework was added.
- F01 evidence: `frontend/public/fallback/demo.json` is an exact copy of the B15 genuine bundle; `parseDemoBundle` rejects malformed required fields; `loadFallbackDemo` validates HTTP/JSON responses; the reducer stores canonical scenario, policy, solve, shock, and diagnosis responses once and selectors derive plan/diff views without copied metrics.
- F02 evidence: approved OKLCH tokens and type scales are in [frontend/src/styles/tokens.css](frontend/src/styles/tokens.css); local Space Grotesk, DM Sans, and JetBrains Mono WOFF2 files plus OFL texts are under [frontend/public/fonts](frontend/public/fonts); the shell has a first-focusable skip link, native `aria-current="step"` chapter buttons, disabled locked chapters, visible focus styling, and a normal-flow TrustBar that keeps policy disclaimer and solver proof visible.
- F03 evidence: [frontend/src/components/BriefChapter.tsx](frontend/src/components/BriefChapter.tsx) derives the maximum temperature, crew/job counts, heat-band strip, crew cards, and three fixed spotlight jobs from the saved scenario; `App` preloads the genuine fallback locally and the primary action dispatches navigation to Plan Transformation. Missing spotlight IDs and saved-load failures remain visible fixture errors.
- F04 evidence: [frontend/src/components/Timeline.tsx](frontend/src/components/Timeline.tsx) renders all 27 saved policy-plan segments in stable scenario crew order, uses 40 fractional slot columns with `start_slot + 1 / end_slot + 1` grid lines, exposes exact accessible segment labels, and provides native keyboard-selectable work controls with a live detail summary.
- Backend release evidence remains in [backend/RELEASE_EVIDENCE.md](backend/RELEASE_EVIDENCE.md); saved solver artifacts remain canonical under [backend/heatshift/fixtures/saved](backend/heatshift/fixtures/saved).
- Known limitations: metrics/diff evidence, map synchronization, live API client, and responsive screenshot review remain later packets. Why chapter currently shows a packet handoff placeholder. Backend limitations remain documented in [docs/SAFETY_AND_LIMITATIONS.md](docs/SAFETY_AND_LIMITATIONS.md).
- Next task: F05 — metrics and plan-difference evidence

## Immediate next action

Execute **F05 only** from [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md) and [docs/FRONTEND_PLAN.md](docs/FRONTEND_PLAN.md). Stop after its verification and checkpoint handoff.

Do not begin frontend polish beyond the active frontend packet until its packet-specific acceptance commands pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
