# HeatShift evidence audit

This audit maps externally visible numbers, superlatives, product claims, and release claims to the repository evidence that supports them. Synthetic scenario values must not be generalized beyond this product demo.

| Claim or displayed value | Evidence source | Verification |
|---|---|---|
| 41°C, 3 crews, 12 work orders | `backend/heatshift/fixtures/scenario.json` (`heat_series`, `crews`, `jobs`) | `max(heat_series.temperature_c) == 41`; lengths are 3 and 12. |
| Service-first: 4/4 critical, value 400, 11 conflicts, 82 travel minutes | `backend/heatshift/fixtures/saved/base-solve.json` → `plans.service_first` | Saved JSON plus `tests/integration/test_solve_service.py`. |
| Constrained: 3/4 critical, value 368, zero conflicts, 160 travel minutes | `backend/heatshift/fixtures/saved/base-solve.json` → `plans.policy_constrained` | Saved JSON plus backend reconciliation tests; status is `OPTIMAL`. |
| “Maximum” wording | `maximum_claim_allowed` and stage statuses in the response contract | Frontend claim gating in `SolverEvidence`/plan components and optimizer proof tests. |
| `job-bus-route` is `proven_infeasible` | `backend/heatshift/fixtures/saved/diagnosis-job-bus-route.json` | `proof_status == INFEASIBLE`; four bounded interventions are retained in the response. |
| +2°C adds 60 eligible recovery minutes | `backend/heatshift/fixtures/saved/heat-shock.json` | `plans.heat_shock.metrics.eligible_recovery_minutes == 60`; `plan_diff` contains `recovery_added`. |
| Canonical hashes and determinism | `backend/heatshift/fixtures/saved/manifest.json`, `tests/integration/test_determinism.py` | R00 generated-output hashes matched the manifest; only `wall_time_seconds` is excluded. |
| Three live rehearsal durations and two saved-mode durations | `backend/RELEASE_EVIDENCE.md` R01 section | Measured R01 localhost rehearsal output. |
| Python/Node and dependency versions | `backend/requirements*.txt`, `frontend/package.json`, `frontend/package-lock.json` | R00 clean-install evidence and `THIRD_PARTY_NOTICES.md`. |
| One-process API/UI serving and local assets | `backend/heatshift/api.py`, `frontend/vite.config.ts`, `tests/integration/test_static.py` | R00 Uvicorn smoke; `/`, `/why`, API, fallback, fonts, and hashed assets returned from one process. |
| No external runtime asset/data dependency | compiled static output, `frontend/src/api/client.ts`, local font directory, R01 request log | R00/R01 production smoke and static inspection; no CDN/map/analytics/image/data request is part of the app path. |
| Synthetic-policy and safety boundary | `docs/SAFETY_AND_LIMITATIONS.md`, `docs/DEMO_SCENARIO.md`, TrustBar component | The disclaimer is rendered in the shell and repeated in the demo script; no medical/legal certification claim is permitted. |
| “Built during Orion” | `docs/PRD.md` and README scope statement | Project scope statement, not an impact or performance claim. |

## Claims deliberately excluded

- No generalized percentage, productivity, safety, compliance, or public-impact claim is made from the synthetic scenario.
- No claim says that a deferred job is impossible merely because it is absent from one optimum; the diagnosis classification is named exactly.
- No claim says that bounded interventions are globally minimal.
- No claim presents the schematic map as street-level routing.
- No loaded-UI screenshot or video is presented as captured when the available browser surface could not consume the local JSON response.
