# HeatShift evidence audit

This page maps public claims and displayed numbers to their repository evidence. The bundled scenario is synthetic. Do not generalize its values to real municipalities.

| Public claim or value | Source of record | How it is checked |
|---|---|---|
| 41°C, 3 crews, 12 work orders | `backend/heatshift/fixtures/scenario.json` | The heat-series maximum is 41; the crew and job collections contain 3 and 12 entries. |
| Service-first result: 4 of 4 critical jobs, value 400, 11 conflicts, 82 travel minutes | `backend/heatshift/fixtures/saved/base-solve.json`, `plans.service_first` | Saved output and integration tests. |
| Constrained result: 3 of 4 critical jobs, value 368, 0 conflicts, 160 travel minutes, 0 overtime | `backend/heatshift/fixtures/saved/base-solve.json`, `plans.policy_constrained` | Saved output, independent reconciliation tests, and `OPTIMAL` status. |
| Maximum-service wording | `maximum_claim_allowed` and stage statuses in the result contract | Frontend claim gating and optimizer proof tests. |
| Bus-route repair is `proven_infeasible` | `backend/heatshift/fixtures/saved/diagnosis-job-bus-route.json` | The saved diagnosis has `proof_status == INFEASIBLE` and records four bounded interventions. |
| +2°C adds 60 eligible recovery minutes | `backend/heatshift/fixtures/saved/heat-shock.json` | The heat-shock metrics record 60 minutes; the plan differences include `recovery_added`. |
| Deterministic saved results | `backend/heatshift/fixtures/saved/manifest.json` and `tests/integration/test_determinism.py` | Canonical output hashes are checked; only wall-clock duration is excluded from hashing. |
| One service serves the app and API | `backend/heatshift/api.py`, `frontend/vite.config.ts`, and static integration tests | Production smoke tests cover the app, direct routes, APIs, fallback JSON, fonts, and hashed assets. |
| No external runtime data service | Compiled frontend, API client, local font directory, and release evidence | The app does not require a CDN, map service, analytics service, database, or API key for the demo. |
| Safety boundary | `docs/SAFETY_AND_LIMITATIONS.md`, `docs/DEMO_SCENARIO.md`, and the Trust Bar component | The UI and docs state that the policy and scenario are synthetic and that the tool does not certify safety or compliance. |

## Claims deliberately excluded

- No generalized percentage for safety, productivity, compliance, or public impact
- No claim that a deferred job is impossible because it is absent from one plan
- No claim that the bounded interventions are globally minimal
- No claim that the schematic map provides street-level navigation
- No medical, legal, or safety certification claim
