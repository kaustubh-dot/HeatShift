# HeatShift Release and Submission Implementation Plan

Execute these packets only after backend B17 and frontend F12 pass. The release must use the same commit/build for local verification, screenshots, video, repository instructions, and Devpost.

## R00 — Fresh-start rehearsal

### Goal

Prove that a reviewer can install, test, build, and run HeatShift without hidden local state.

### Procedure

1. Record the candidate commit ID or, before Git exists, a SHA-256 inventory of source files.
2. Use a clean temporary checkout/copy that excludes `.venv`, `node_modules`, caches, and generated static output.
3. Follow only the README commands. Do not repair missing steps silently.
4. Create Python 3.12 environment and install `backend/requirements-dev.txt`.
5. Run the full backend test suite and saved-output generation.
6. Run `npm ci`, frontend tests, and the production build.
7. Start the documented FastAPI command.
8. Verify `/healthz`, `/api/demo`, base solve, designated diagnosis, and +2°C solve.
9. Load the production UI directly, refresh it, and complete all three chapters.
10. Record commands, durations, failures, and fixes in `backend/RELEASE_EVIDENCE.md` and `CHECKPOINT.md`.

### Acceptance

- No undeclared environment variable, global package, local file, or manual data edit is needed.
- The production process serves both API and compiled UI.
- Generated outputs match the canonical hashes except documented runtime metadata.
- README instructions exactly match the successful commands.

## R01 — Live and disconnected demo rehearsals

### Live rehearsal

Use the storyboard in [DEMO_AND_SUBMISSION.md](DEMO_AND_SUBMISSION.md):

1. Open the preloaded brief.
2. State the user/problem and synthetic-policy boundary.
3. Transform service-first into the policy-constrained plan.
4. Point to critical service, zero policy conflicts, and proof status.
5. Select the designated deferred job and show its forced-inclusion result.
6. Apply +2°C and state the meaningful decision change.
7. Finish with architecture, reproducibility, and limitations.

Time the rehearsal. Target 3:30–4:30, leaving margin for pauses.

### Disconnected rehearsal

1. Force saved mode using the documented switch or make the API unavailable.
2. Confirm the disclosure remains visible.
3. Repeat the same story using only exact-match saved outputs.
4. Confirm no external font, map, analytics, image, or data request is required.

### Failure drill

Rehearse one deliberate validation error or unavailable API state. The presenter must be able to explain the honest status and return to the deterministic demo without restarting the machine.

### Acceptance

Complete three consecutive live runs and two disconnected runs without editing files, refreshing to repair state, or making an unsupported claim. Record the durations and any remaining risk.

## R02 — Release screenshots and demo recording

### Screenshot list

Capture from the production build at 1440×900 or the recording resolution:

1. Tomorrow's Brief with 41°C, crew count, work-order count, heat strip, and disclaimer.
2. Service-first plan immediately before transformation.
3. Final policy-constrained timeline/map with metrics and solver proof.
4. Selected deferred-job difference with binding rule.
5. Diagnosis result with retained commitments and intervention table.
6. +2°C result with the changed decision.
7. Optional architecture/test evidence frame.

Do not composite values, hide fallback disclosure, or use a build different from the candidate release.

### Recording checklist

- 3–5 minutes.
- Cursor and text readable at normal playback.
- No notifications, credentials, local private paths, or unrelated tabs visible.
- Synthetic-policy disclaimer appears visually and is stated once.
- “Maximum” is spoken only when the displayed proof permits it.
- The map is called schematic.
- The deferred-job result is described using its exact classification.
- The final limitation statement is included.

After recording, watch the entire exported file once with audio and once muted. The muted pass must still communicate the core before/after story.

## R03 — Repository and evidence documentation

### README sections required

1. One-sentence value proposition.
2. Problem, user, and why existing alerts are insufficient.
3. Exact feature list.
4. Architecture diagram.
5. Optimization formulation summary and objective order.
6. Screenshot/GIF from the release build.
7. Python 3.12 and Node prerequisites.
8. Fresh install, test, saved generation, development, and production commands.
9. Demo scenario/result table populated from saved output.
10. Determinism/fallback explanation.
11. Safety boundary and known limitations.
12. Technology and third-party attribution.
13. “Built during Orion” scope statement.

### Evidence audit

For every number or superlative in README, slides, narration, and Devpost, record its source:

- solver output path;
- measured test/runtime command;
- canonical product limitation; or
- external source with a direct citation.

Delete claims that have no traceable source. Never generalize percentages from the synthetic scenario.

### License audit

Record licenses/attribution for OR-Tools, FastAPI, React, Vite, Lucide, and every bundled font. Do not bundle a font file until its redistribution license is stored or linked appropriately.

## R04 — Devpost audit and submission

The [OrionHackathon page](https://orionhackathon.devpost.com/) lists the deadline as 5 August 2026 at 17:00 EDT and evaluates innovation, technical excellence, real-world impact, UX/design, and presentation/demo.

### Required submission fields/assets

- title and one-line value proposition;
- Sustainability & Climate Tech category;
- project description;
- public repository at the candidate release;
- working demo link if available;
- 3–5 minute video;
- presentation if used;
- installation instructions;
- team details;
- technology list;
- synthetic scenario/policy disclosure; and
- limitations and attribution.

### Judge-criteria audit

| Criterion | Evidence to place in submission |
|---|---|
| Innovation | Counterfactual forced-inclusion diagnosis, not generic heat alerts |
| Technical excellence | CP-SAT formulation, route continuity, global rolling constraints, staged proofs, deterministic tests |
| Real-world impact | Municipal supervisor workflow and exact synthetic scenario trade-off; no generalized impact percentage |
| UX/design | Three-chapter story, full-day timeline, synchronized evidence, accessibility, honest states |
| Presentation | Short before/after demo, diagnosis, +2°C re-plan, limitations |

### Final checks

1. Open every public link in a private/incognito window.
2. Confirm repository visibility and installation commands.
3. Confirm video permissions, audio, duration, and final URL.
4. Compare every displayed metric in screenshots/video/description with the saved release JSON.
5. Confirm the disclaimer and limitations are present.
6. Preserve a submission buffer; do not use the final minutes for optional polish.
7. Request explicit user confirmation before the irreversible final Devpost submission.

R04 is complete only after the submitted page is reopened and all assets/links are verified.
