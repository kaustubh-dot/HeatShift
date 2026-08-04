# Checkpoint

**Last updated:** 2026-08-04
**Phase:** Phase 3 release and submission
**Overall status:** Implementation audited and verified; R02 video/loaded captures and R04 submission remain manual

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
- Canonical models, pure time-grid/heat/matrix helpers, deterministic scenario/policy fixtures, solver-free validation, deterministic execution patterns, CP-SAT model construction, staged proof capture, timeline/route extraction, metrics, independent policy reconciliation, service orchestration, evidence-backed plan differences, forced-inclusion diagnosis, bounded interventions, +2°C heat shock, declared scenario-tuning evidence, deterministic saved solver evidence, the three FastAPI routes, the backend release report, the pinned React/Vite shell, canonical frontend contract types, genuine fallback loading, reducer-owned state, approved design tokens, local licensed fonts, semantic chapter navigation, the shared TrustBar, the scenario-derived Tomorrow's Brief, the complete-day accessible timeline, metrics/plan-difference evidence, the synchronized schematic service map, the replayable reduced-motion transformation, and the saved diagnosis chapter now exist.
- The root `.venv` uses Python 3.12.13 and contains the verified runtime and test dependencies.
- The implementation branch is `main`; teammate work is present through merge commit `30a00be`, with the 2026-08-04 audit fixes currently local and unpushed.

## Active implementation checkpoint

- Last completed task: R03; R02 is reopened because the required loaded captures and 3–5 minute video were not produced.
- Verification commands:
  - `python3.12 --version`
  - `python3.12 -m venv .venv`
  - `.venv/bin/python -m pip install -r backend/requirements-dev.txt`
  - `.venv/bin/python -m pip check`
  - `.venv/bin/python -m backend.heatshift.cli validate`
  - `.venv/bin/python -m backend.heatshift.cli generate-saved --output-dir <temporary-directory>`
  - `.venv/bin/python -m pytest -q`
  - `cd frontend && npm ci && npm run test:run && npm run build`
  - `.venv/bin/python -m uvicorn backend.heatshift.api:app --host 127.0.0.1 --port 8000`
  - `.venv/bin/python /private/tmp/heatshift-r01-rehearsal.py`
  - `cd frontend && npm run build`
  - `git diff --check`
- Results: Python `3.12.13` created a clean venv and installed all pinned requirements; imports reported `imports-ok`; `pip check` reported `No broken requirements found`; fixture validation returned `valid=true` with no issues; saved-output generation exited 0 and matched the checked-in canonical output hashes. After the production build, `.venv/bin/python -m pytest -q` reported `98 passed` with one existing Starlette/HTTPX deprecation warning; `npm ci` installed 129 packages with 0 vulnerabilities; `npm run test:run` reported `35 passed` across ten test files; `npm run build` emitted `backend/heatshift/static/index.html`, hashed assets, fallback JSON, and bundled fonts; the README evidence assertions reported `readme-evidence-ok`; and `git diff --check` exited 0.
- 2026-08-04 audit: fixed intermittent baseline timeouts while preserving `FEASIBLE`/`OPTIMAL` claim boundaries, traceback-safe service errors, condition-consistent heat-adjusted diagnosis, pre-solver validation of adjusted policy coverage, full structural saved-fallback matching, nested response validation, plan-loading/source copy, home navigation, and unchanged heat-shock rendering. Canonical generation now uses a manifest-recorded 30-second offline budget while live requests remain five seconds. Verification reports `102 passed` backend tests, `37 passed` frontend tests, a successful production build, `pip check` clean, static serving `2 passed`, and a live HTTP smoke with value 400 and zero constrained conflicts.
- R00 fresh-start evidence: a clean archive of candidate `f6eca22` initially exposed the missing venv setup in README; the README was corrected and the exact setup/install/build/start sequence passed from `/private/tmp/heatshift-r00-final.0IXb7U`. The one-process smoke returned `/healthz`, `/api/demo`, base `/api/solve`, designated `/api/diagnose`, +2°C `/api/solve`, `/`, `/why`, and `/fallback/demo.json` with the expected 200 responses and content types. Full details and canonical hashes are in [backend/RELEASE_EVIDENCE.md](backend/RELEASE_EVIDENCE.md).
- R01 evidence: one unchanged production process passed three live story runs in `13.94s`, `14.32s`, and `14.18s`; each showed 41°C, 3 crews, 12 work orders, 11 service-first conflicts, zero constrained conflicts, `OPTIMAL` policy status, `proven_infeasible` diagnosis, and 60 minutes of heat-shock recovery. Two saved-mode runs took `0.01s` and `0.00s`, matched all canonical hashes, retained the `SAVED SOLVER RUN / Live API unavailable` disclosure, and required only local runtime data. A malformed solve returned `422 INVALID_SCENARIO`, then `/api/demo` recovered with `200` without restart. Full details are in [backend/RELEASE_EVIDENCE.md](backend/RELEASE_EVIDENCE.md).
- R02 evidence: `docs/release/demo-rehearsal.md` contains the source-backed four-minute narration and exact values; the production-build capture set contains live and saved shell states at the browser’s actual `1280×720` resolution in `docs/release/screenshots/`. The requested `1440×900` override remained capped, and the browser transport left both JSON-backed journeys loading, so loaded chapter frames and an exported video remain explicitly unavailable rather than fabricated.
- R03 evidence: README now contains the problem/user boundary, exact feature list, architecture diagram, objective order, saved-result table, setup/development/production commands, determinism/fallback explanation, safety boundary, attribution link, and Orion scope statement. `docs/ARCHITECTURE.md` matches the implemented module tree and one-process static serving; [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) records direct dependency and bundled-font licenses; and [docs/EVIDENCE_AUDIT.md](docs/EVIDENCE_AUDIT.md) maps displayed values and superlatives to committed sources.
- R04 evidence: [docs/DEVPOST_SUBMISSION.md](docs/DEVPOST_SUBMISSION.md) contains the audited title, description, category, evidence table, judge-criteria mapping, installation block, asset links, attribution, limitations, and submission checklist. The configured GitHub repository is publicly visible and the official OrionHackathon page was checked for the current deadline and required fields. The local candidate is newer than the public candidate branch; the push was rejected by the workspace safety gate because publishing repository contents requires explicit authorization. A read-only local audit checked all relative links in `README.md`, `docs/DEVPOST_SUBMISSION.md`, and `docs/EVIDENCE_AUDIT.md`, then rechecked the canonical service-first, policy-constrained, diagnosis, and heat-shock values and printed `r04-local-audit-ok`. The demo video and owner-supplied team details are still missing, and the irreversible Devpost submit action has not been attempted.
- F00 shell: React 19.2.8, TypeScript 5.9.3, Vite 8.1.5, `lucide-react` 1.17.0, Vitest 3.2.7, React Testing Library 16.3.0, DOM matchers 6.8.0, and jsdom 26.1.0. No router, state library, HTTP library, animation package, or CSS framework was added.
- F01 evidence: `frontend/public/fallback/demo.json` is an exact copy of the B15 genuine bundle; `parseDemoBundle` rejects malformed required fields; `loadFallbackDemo` validates HTTP/JSON responses; the reducer stores canonical scenario, policy, solve, shock, and diagnosis responses once and selectors derive plan/diff views without copied metrics.
- F02 evidence: approved OKLCH tokens and type scales are in [frontend/src/styles/tokens.css](frontend/src/styles/tokens.css); local Space Grotesk, DM Sans, and JetBrains Mono WOFF2 files plus OFL texts are under [frontend/public/fonts](frontend/public/fonts); the shell has a first-focusable skip link, native `aria-current="step"` chapter buttons, disabled locked chapters, visible focus styling, and a normal-flow TrustBar that keeps policy disclaimer and solver proof visible.
- F03 evidence: [frontend/src/components/BriefChapter.tsx](frontend/src/components/BriefChapter.tsx) derives the maximum temperature, crew/job counts, heat-band strip, crew cards, and three fixed spotlight jobs from the saved scenario; `App` preloads the genuine fallback locally and the primary action dispatches navigation to Plan Transformation. Missing spotlight IDs and saved-load failures remain visible fixture errors.
- F04 evidence: [frontend/src/components/Timeline.tsx](frontend/src/components/Timeline.tsx) renders all 27 saved policy-plan segments in stable scenario crew order, uses 40 fractional slot columns with `start_slot + 1 / end_slot + 1` grid lines, exposes exact accessible segment labels, and provides native keyboard-selectable work controls with a live detail summary.
- F05 evidence: [frontend/src/components/PlanChapter.tsx](frontend/src/components/PlanChapter.tsx) renders the service-first and policy-constrained proof cards, the seven response-supplied metrics with subtraction-only deltas, and every saved `plan_diff` record; [frontend/src/components/primitives.tsx](frontend/src/components/primitives.tsx) exposes explicit change labels/icons, before/after crew-time, binding rule IDs, explanation codes, stage statuses, values, bounds, and claim gating; [frontend/tests/plan.test.tsx](frontend/tests/plan.test.tsx) covers 14 tests across base/heat-shock fixture statuses, diff vocabulary, exact deferred evidence, and shared timeline/diff selection.
- F06 evidence: [frontend/src/components/ServiceMap.tsx](frontend/src/components/ServiceMap.tsx) renders one responsive `800×600` SVG with submitted location coordinates, depot squares, neutral job circles, and backend-ordered route polylines using crew colors only for route identity; [frontend/tests/service-map.test.tsx](frontend/tests/service-map.test.tsx) verifies all 12 job nodes, the depot, all 10 route records/orderings, keyboard selection, and shared map/timeline/diff selection.
- F07 evidence: [frontend/src/hooks/usePlanTransformation.ts](frontend/src/hooks/usePlanTransformation.ts) keeps only animation phase in local state and schedules 300ms highlight, 500ms transform, and 250ms settle stages; [frontend/tests/transformation.test.tsx](frontend/tests/transformation.test.tsx) covers fake-timer phase boundaries, replay, final-plan equivalence, immediate reduced-motion output, and usable controls.
- F08 evidence: [frontend/src/components/WhyChapter.tsx](frontend/src/components/WhyChapter.tsx) defaults through `manifest.designated_diagnosis_job_id`, keeps classification beside proof status, and renders every saved diagnosis field plus intervention objective deltas; [frontend/tests/why.test.tsx](frontend/tests/why.test.tsx) covers the designated `proven_infeasible` response, all four exact classification phrases, and focus after a successful diagnosis request.
- F09 evidence: [frontend/src/components/WhyChapter.tsx](frontend/src/components/WhyChapter.tsx) sends the exact `{ heat_adjustment_c: 2 }` request, keeps the diagnosis and current plan visible while loading, and renders the returned `plans.heat_shock`, first non-unchanged decision, response metrics, solver proof, and every returned shock diff; [frontend/src/state/appState.tsx](frontend/src/state/appState.tsx) preserves the cached canonical response across reset; [frontend/tests/heat-shock.test.tsx](frontend/tests/heat-shock.test.tsx) covers exact request shape, loading behavior, returned evidence order/count, reset, and reducer preservation.
- F10 evidence: [frontend/src/api/client.ts](frontend/src/api/client.ts) uses only native fetch for `/api/demo`, `/api/solve`, and `/api/diagnose`, with one 15-second abort timeout and structured error preservation; [frontend/src/api/fallback.ts](frontend/src/api/fallback.ts) validates all UI-dereferenced response fields and selects saved solves/diagnoses only when the complete scenario and policy match structurally, with exact heat-adjustment and job matches; [frontend/src/App.tsx](frontend/src/App.tsx) runs live mode by default, activates saved mode only for explicit configuration or network/abort/server failure, preserves current results during requests, and keeps validation/malformed responses visible; [frontend/src/components/SolverEvidence.tsx](frontend/src/components/SolverEvidence.tsx) keeps the saved-run disclosure and provenance visible for the full saved session; [frontend/tests/client.test.tsx](frontend/tests/client.test.tsx) covers live success, demo parsing, exact fallback/rejection, structured 4xx errors, malformed nested 2xx data, abort, server failure, `FEASIBLE` warning, and saved disclosure.
- F11 evidence: [frontend/src/components/AppShell.tsx](frontend/src/components/AppShell.tsx) now moves focus to `#main-content` from the skip link; [frontend/tests/shell.test.tsx](frontend/tests/shell.test.tsx) verifies the focus handoff, enabled/disabled chapter navigation, trust landmarks, and visible main region. The in-app browser observed one skip link, semantic chapter navigation, `<main>`, trust-bar content, no horizontal overflow at its available `1280×720`, and reduced-motion CSS remains covered by the existing transformation tests. Manual full-chapter, 200% zoom, screen-reader, and `1440×900` checks were limited: the browser surface blocked `/fallback/demo.json` with `ERR_BLOCKED_BY_CLIENT`, page fetch remained unavailable, and the viewport override stayed capped at `1280×720`.
- F12 evidence: [frontend/vite.config.ts](frontend/vite.config.ts) emits to the generated-only `backend/heatshift/static/` directory and proxies `/api`/`/healthz` in development; [backend/heatshift/api.py](backend/heatshift/api.py) serves files with `FileResponse`, keeps exact API routes ahead of the SPA catch-all, rejects unknown `/api/*`, and returns `index.html` for direct app routes; [tests/integration/test_static.py](tests/integration/test_static.py) reports `2 passed` after the build. The elevated Uvicorn smoke run returned `/healthz` 200, `/` and `/why` 200 HTML, `/api/demo` 200 JSON, `/fallback/demo.json` 200 JSON, hashed JavaScript 200 `text/javascript`, and unknown API 404 JSON. `git ls-files backend/heatshift/static` is empty, and the built frontend contains no runtime CDN/font URL.
- Backend release evidence remains in [backend/RELEASE_EVIDENCE.md](backend/RELEASE_EVIDENCE.md); saved solver artifacts remain canonical under [backend/heatshift/fixtures/saved](backend/heatshift/fixtures/saved).
- Known limitations: the in-app browser loaded and refreshed the production HTML, and the server returned `/api/demo` and `/fallback/demo.json` 200, but the browser layer kept the JSON-backed journey in its loading state; direct JSON navigation reported `ERR_BLOCKED_BY_CLIENT`, and transient MIME, compression, and non-JSON-path proxies produced the same result, so manual completion of all three chapters was not observable there. The browser viewport also remains capped at `1280×720` for the `1440×900` check, and no exported video was produced. R04 must verify the final video/public-link assets if they are supplied. Backend limitations remain documented in [docs/SAFETY_AND_LIMITATIONS.md](docs/SAFETY_AND_LIMITATIONS.md).
- Next tasks: R02 — capture the loaded journey and record the video; then R04 — publish the audited fixes, supply owner/team fields, verify public links, and submit.

## Immediate next action

Complete the manual portion of **R02**, then **R04**, using [docs/RELEASE_IMPLEMENTATION_PLAN.md](docs/RELEASE_IMPLEMENTATION_PLAN.md): connect a usable browser, capture loaded chapter frames, record the 3–5 minute demo, provide team details, publish the audited local changes, verify every link incognito, and confirm before the irreversible Devpost submit action.

Do not begin frontend polish beyond the active frontend packet until its packet-specific acceptance commands pass.

## Restart instructions

1. Read `README.md` and this checkpoint.
2. Read `docs/SOLVER_SPEC.md` and `docs/DATA_AND_API_CONTRACTS.md` before implementing the backend.
3. Read the complete packet for the active task ID; use `TODO.md` as the ledger.
4. Update this file whenever a phase gate passes, a locked decision changes, or a blocker appears.
