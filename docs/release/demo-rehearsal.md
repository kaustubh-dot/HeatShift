# R02 release capture and demo rehearsal

**Candidate:** `81efa5b` (`R01: rehearse live and disconnected demo`)

## Production capture

The production build was regenerated with:

```text
cd frontend
npm run build
```

The in-app browser was asked for `1440×900`, but the available surface remained `1280×720`. The two captures below are therefore labeled with their actual dimensions:

- [saved-mode loading state, 1280×720](screenshots/00-production-saved-loading.jpg)
- [live-mode loading state, 1280×720](screenshots/01-production-live-loading.jpg)

The captures are honest production states: the shell, policy boundary, and solver evidence trust bar render, while the browser integration layer prevents the local JSON response from reaching the React state. The requested six loaded journey frames were not fabricated or composited.

## Four-minute narration script

This script uses the canonical saved outputs and the three successful R01 live runs. Values are sourced from `backend/heatshift/fixtures/saved/*.json`.

| Time | Presenter action and exact language | Visible evidence |
| ---: | --- | --- |
| 0:00–0:20 | “Tomorrow is 41°C. This synthetic Demo City has three crews and twelve work orders.” | Scenario brief: `41°C`, `3`, `12` |
| 0:20–0:45 | “The user is a municipal planned-maintenance supervisor. The policy is synthetic and organization-supplied; this tool executes it and does not medically or legally validate it.” | Policy boundary / TrustBar |
| 0:45–1:15 | “First, I show the service-first counterfactual. It schedules all four critical jobs and value 400, but it is only `FEASIBLE` and carries 11 mandatory policy conflicts.” | Service-first proof card and conflict count |
| 1:15–1:55 | “Now the policy-constrained solve is `OPTIMAL`: three of four critical jobs, value 368, zero mandatory conflicts, 160 travel minutes, and no overtime. The saved proof permits the highest-service claim within this locked scenario.” | Final timeline, schematic map, metrics, proof status |
| 1:55–2:25 | “The cost of compliance is visible as moved, served, and deferred decisions. I select `job-bus-route`; omission alone is not called impossible.” | Plan difference with binding rule `hs01-heavy-elevated` |
| 2:25–3:10 | “The forced-inclusion diagnosis retains the original commitments, reports `proven_infeasible` with `INFEASIBLE` proof, and shows four bounded interventions, each also `INFEASIBLE`.” | Diagnosis result and intervention table |
| 3:10–3:45 | “With a synthetic +2°C shock, the re-plan is `OPTIMAL`, keeps zero mandatory conflicts, and adds 60 eligible recovery minutes. The changed decision is shown rather than hidden.” | Heat-shock metrics, recovery-added diff |
| 3:45–4:20 | “The stack is a React/Vite client served by FastAPI, with OR-Tools CP-SAT, deterministic seed 7, one worker, saved canonical hashes, and a local fallback. The map is schematic and the horizon is one day.” | Architecture/test evidence and provenance |
| 4:20–4:40 | “This is a synthetic planning prototype, not a medical, legal, safety, routing, or compliance certification system. It does not replace measurements, emergency procedures, stop-work rights, or qualified judgment.” | TrustBar and limitations |

## Capture status and risk

- The narration is ready and uses exact saved evidence; no unsupported percentage or medical claim is included.
- A loaded six-frame screenshot set and an exported 3–5 minute recording could not be produced in the available browser surface because both live and explicit saved mode remained in their honest loading states after the server returned HTTP `200` for the requested JSON.
- R01 still verified three live API story runs and two saved-mode runs without edits or restart. The remaining risk is visual capture, not solver/API determinism.
