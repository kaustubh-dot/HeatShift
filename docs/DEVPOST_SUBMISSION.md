# HeatShift Devpost submission packet

**Audit date:** 2026-08-04
**Repository:** https://github.com/kaustubh-dot/HeatShift
**Hackathon:** [OrionHackathon](https://orionhackathon.devpost.com/)
**Category:** Sustainability & Climate Tech
**Submission status:** Prepared for review; final external submission requires the owner's confirmation.

The configured GitHub repository is publicly visible. Teammate work is merged on public `main` through `30a00be`; the 2026-08-04 audit fixes are newer and remain local until the owner explicitly asks to publish them.

## Title

HeatShift: Policy-Constrained Service Optimizer

## One-line value proposition

HeatShift shows a municipal maintenance supervisor the highest proven service available under an approved heat policy, then proves what it costs to bring deferred work back into the plan.

## Project description

Heat alerts tell a supervisor that conditions are dangerous; they do not show which work orders, crews, routes, recovery periods, or policy rules must change. HeatShift turns that operational question into a transparent optimization workflow for a municipal planned-maintenance supervisor.

The application loads a deterministic synthetic Demo City scenario with three pre-formed crews and twelve work orders. It first exposes a service-first counterfactual and its policy conflicts, then solves the policy-constrained plan with OR-Tools CP-SAT. The UI makes critical service, weighted service, travel, recovery, overtime, route order, timeline changes, and solver proof visible. A selected deferred job is forced back into the plan and classified under retained commitments. A synthetic `+2°C` shock produces a new plan and an explicit diff.

The contribution is counterfactual diagnosis, not a generic heat alert. The bundled policy is synthetic and organization-supplied. HeatShift does not create or certify a safety policy, diagnose heat illness, certify legal compliance, or replace worksite measurements, emergency procedures, worker stop-work rights, or qualified judgment.

## Evidence-backed demo claims

| Claim | Exact evidence |
|---|---|
| Opening scenario | 41°C, 3 crews, 12 work orders from `backend/heatshift/fixtures/scenario.json` |
| Service-first view | `FEASIBLE`, 4/4 critical jobs, value 400, 11 mandatory conflicts, 82 travel minutes |
| Constrained view | `OPTIMAL`, 3/4 critical jobs, value 368, zero conflicts, 160 travel minutes, zero overtime |
| Deferred job | `job-bus-route` classified `proven_infeasible` with `INFEASIBLE` proof and four bounded interventions |
| Heat shock | `OPTIMAL`, zero conflicts, 60 eligible recovery minutes, and a `recovery_added` diff |

All result values above are copied from `backend/heatshift/fixtures/saved/*.json`; the full mapping is in [docs/EVIDENCE_AUDIT.md](EVIDENCE_AUDIT.md).

## Demo and repository assets

- Four-minute source-backed narration: [docs/release/demo-rehearsal.md](release/demo-rehearsal.md)
- Production capture: [saved-mode shell](release/screenshots/00-production-saved-loading.jpg), [live-mode shell](release/screenshots/01-production-live-loading.jpg)
- Installation and production run: [README](../README.md)
- Architecture: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Safety boundary: [docs/SAFETY_AND_LIMITATIONS.md](SAFETY_AND_LIMITATIONS.md)
- Attribution: [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)

The available capture environment could not render the JSON-backed journey beyond its honest loading states, so no loaded journey video is claimed here. A real 3–5 minute recording remains a submission asset to produce in a browser that can render the local JSON response.

## Technology

Python 3.12, OR-Tools CP-SAT, Pydantic, FastAPI, Uvicorn, React 19, TypeScript, Vite, Lucide React, Vitest, React Testing Library, and bundled DM Sans, JetBrains Mono, and Space Grotesk fonts. The production shape is one FastAPI process serving the API and compiled SPA; no database or external runtime data service is required.

## Judge-criteria mapping

| Criterion | Submission evidence | Claim boundary |
|---|---|---|
| Innovation & Creativity | Forced-inclusion diagnosis distinguishes omission from proven infeasibility; this is the core differentiator beyond a heat alert. | No “first” or market-superiority claim. |
| Technical Excellence | CP-SAT pattern/route model, global rolling constraints, staged proof capture, independent metric reconciliation, deterministic saved hashes, and 98 backend tests. | One-day synthetic prototype; no production-scale claim. |
| Real-world Impact | Municipal supervisor workflow and an exact synthetic service/policy trade-off. | No generalized percentage or real-world outcome claim. |
| User Experience & Design | Three chapters, complete-day timeline, synchronized schematic map/diffs, keyboard/reduced-motion coverage, and visible trust boundary. | Browser capture limitation is disclosed. |
| Presentation & Demo | Four-minute narration, before/after plan, diagnosis, +2°C re-plan, architecture, and limitations. | Exported video still must be recorded and checked. |

## Reproduction

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/python -m backend.heatshift.cli validate
.venv/bin/python -m backend.heatshift.cli generate-saved --output-dir "$(mktemp -d)"
.venv/bin/python -m pytest -q
cd frontend
npm ci
npm run test:run
npm run build
cd ..
.venv/bin/python -m uvicorn backend.heatshift.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. Add `?fallback=true` to explicitly use the disclosed exact-match saved result presentation.

## Submission audit

| Devpost requirement | Status | Evidence or remaining action |
|---|---|---|
| Title and value proposition | Ready | This packet |
| Sustainability & Climate Tech category | Ready | This packet |
| Project description | Ready | This packet; no unsupported generalized impact percentage |
| GitHub repository | Public visibility verified; candidate URL recorded | Publish the current candidate branch, then confirm its final SHA in Devpost |
| Demo video | Missing | Record and watch once with audio and once muted; do not claim the current shell captures are the video |
| Presentation | Optional / missing | Create only if useful; do not block on it unless required by the organizer |
| Installation instructions | Ready | README and reproduction block above |
| Team details | Requires owner input | Enter names, roles, and contact details in Devpost; do not infer them from Git metadata |
| Technology list | Ready | Technology section and `THIRD_PARTY_NOTICES.md` |
| Synthetic policy/data disclosure | Ready | README, TrustBar, narration, and description |
| Limitations and attribution | Ready | Safety doc, evidence audit, and third-party notices |
| Private/incognito link audit | Pending | Check the public repository and any video/demo URL after publishing |
| Final submission | Pending confirmation | Ask the owner before clicking the irreversible submit action |

The official hackathon page currently lists the deadline as 5 August 2026 at 17:00 EDT and requests a project description, GitHub repository, demo video, recommended presentation, installation instructions, and team details. Confirm the page and account state immediately before submission.
