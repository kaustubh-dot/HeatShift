# HeatShift Backend Release Evidence

**Gate:** B17 — Backend release gate  
**Measured:** 2026-08-03  
**Result:** PASS

## Runtime and dependency evidence

The release environment uses Python 3.12.13 and the exact pinned packages below:

| Package | Version |
| --- | ---: |
| Python | 3.12.13 |
| OR-Tools | 9.15.6755 |
| Pydantic | 2.13.4 |
| FastAPI | 0.141.1 |
| Uvicorn | 0.52.0 |
| Pytest | 9.1.1 |
| HTTPX | 0.28.1 |

Command:

```text
.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

Result: exit 0; all pinned requirements were satisfied.

Command:

```text
.venv/bin/python -m pip check
```

Result: `No broken requirements found.`

## Test and validation evidence

Command:

```text
.venv/bin/python -m pytest -q
```

Result: `96 passed in 41.42s`. One upstream Starlette deprecation warning is emitted by the pinned HTTPX/TestClient combination; it does not fail the suite.

Command:

```text
.venv/bin/python -m backend.heatshift.cli validate
```

Result:

```json
{"issues":[],"policy_id":"demo-city-hs-01","scenario_id":"demo-city-day-01","valid":true}
```

The P0 invariant suite passes through the unit and integration tests. It covers pattern completion and recovery, global occupancy and rolling policy constraints, capability and equipment matching, matrix-based routing, depot closure, locked assignments, staged objective ordering, status/proof wording, metric reconciliation, deterministic serialization, and API validation/error boundaries.

## Solver evidence

The bundled base solve uses a five-second request budget and one CP-SAT worker. The reported metrics are extracted from the serialized plans and independently reconciled.

| Evidence | Status and objective summary |
| --- | --- |
| Service-first counterfactual | `FEASIBLE`; 4/4 critical jobs, value 400, 11 mandatory policy conflicts, 82 travel minutes, 300 active-work minutes |
| Policy-constrained plan | `OPTIMAL` at all required stages; 3/4 critical jobs, value 368, 0 conflicts, 160 travel minutes, 0 overtime minutes |
| Forced inclusion: `job-bus-route` | `INFEASIBLE` under all mandatory rules, retained original critical-service count, and forced inclusion; classification `proven_infeasible` |
| +2°C heat-shock plan | `OPTIMAL` at all required stages; 3/4 critical jobs, value 368, 0 conflicts, 160 travel minutes, 60 eligible recovery minutes |

The +2°C saved response also records the retained unadjusted policy plan honestly: its final overtime stage can be `UNKNOWN` after an incumbent is found within the bounded per-plan budget. The heat-shock plan itself is fully `OPTIMAL`; no `UNKNOWN` result is presented as an infeasibility proof.

The scenario-quality gates pass:

- the compliant plan has zero mandatory conflicts;
- the service-first plan has visible policy conflicts;
- critical service is preserved when genuinely feasible;
- the base comparison contains moved-time and deferred/served changes;
- the forced-inclusion diagnosis is nontrivial and its four bounded interventions are `INFEASIBLE`;
- +2°C changes schedule decisions and adds recovery; and
- serialized route and metric reconciliation passes.

## Determinism evidence

Command:

```text
.venv/bin/python -m backend.heatshift.cli generate-saved
```

The command was run twice in separate temporary output directories. Both runs exited 0, input hashes matched, and canonical output hashes matched. The canonical hash excludes only runtime `wall_time_seconds`.

| Saved output | Canonical SHA-256 |
| --- | --- |
| `base-solve.json` | `f2fc17217539af49025a62aca91953eb5e8c87e7b3eff2cbd2af68f249c66cba` |
| `diagnosis-job-bus-route.json` | `de9526bf89fc5ec31d622db2b05db0b6fb3a893cbe2b643572bf017087859420` |
| `heat-shock.json` | `378baffd2ad1a76a1688268c4a89950dbb6a4d2127f8124bbe25f43942cb2615` |

## Wall-time evidence

Measured on the development laptop with the bundled five-second command budget:

| Operation | Wall time | Result |
| --- | ---: | --- |
| Base service-first plus constrained solve | 3.682s | response returned; constrained plan `OPTIMAL` |
| Designated diagnosis | 5.843s | bounded diagnosis returned; forced solve `INFEASIBLE` |
| +2°C heat-shock solve | 4.000s | heat-shock plan `OPTIMAL` |

The independent base branches run concurrently while each retains its own solver budget and deterministic one-worker configuration. Diagnosis remains bounded and reports solver status honestly.

## Safety and technical limitations

HeatShift is an operations-planning prototype using a synthetic scenario and organization-supplied policy inputs. It does not determine medical safety, diagnose or prevent heat illness, create an authoritative work/rest policy, certify regulatory or contractual compliance, or replace worksite measurements, emergency procedures, worker stop-work rights, or qualified professional judgment. The bundled policy is synthetic and is not medical, legal, or workplace-safety guidance.

The prototype is limited to a one-day, 15-minute horizon; a small set of pre-formed crews and jobs; input travel times and a schematic map; simplified recovery conditions; no forecast uncertainty beyond the explicit heat-shock scenario; bounded rather than exhaustive counterfactual interventions; and solver-status/time-limit-dependent optimality. It uses no personal medical information and must not infer individual health or heat tolerance.

## R00 — Fresh-start rehearsal

**Candidate source:** `f6eca22` (`F12: serve frontend through FastAPI`)

The first clean archive intentionally followed the pre-R00 README. The documented server command failed with exit `127` because `.venv/bin/python` did not exist. This exposed that the README assumed a pre-existing virtual environment. The README was corrected to document Python 3.12 venv creation, pinned dependency installation, `pip check`, fixture validation, saved-output generation into a temporary directory, and the backend test command. No source or product behavior was changed to address the documentation gap.

The corrected sequence was then run from a second clean archive with no `.venv`, `node_modules`, caches, or generated static output. The archive was created with:

```text
git archive f6eca22 | tar -x -C /private/tmp/heatshift-r00-final.0IXb7U
```

Commands and results:

```text
python3.12 --version
Python 3.12.13

python3.12 -m venv .venv
exit 0

.venv/bin/python -m pip install -r backend/requirements-dev.txt
exit 0; all pinned packages installed in the clean venv

.venv/bin/python -m pip check
No broken requirements found.

.venv/bin/python -c "import ortools, pydantic, fastapi, pytest; print('imports-ok')"
imports-ok

.venv/bin/python -m backend.heatshift.cli validate
valid=true; scenario_id=demo-city-day-01; policy_id=demo-city-hs-01; issues=[]

.venv/bin/python -m backend.heatshift.cli generate-saved --output-dir /private/tmp/heatshift-r00-final-saved.Iq1aIj
exit 0; fixture_version=demo-v1; Python=3.12.13; OR-Tools=9.15.6755
```

The generated saved-output hashes matched the checked-in manifest:

| Saved output | Canonical SHA-256 |
| --- | --- |
| `base-solve.json` | `f2fc17217539af49025a62aca91953eb5e8c87e7b3eff2cbd2af68f249c66cba` |
| `diagnosis-job-bus-route.json` | `de9526bf89fc5ec31d622db2b05db0b6fb3a893cbe2b643572bf017087859420` |
| `heat-shock.json` | `378baffd2ad1a76a1688268c4a89950dbb6a4d2127f8124bbe25f43942cb2615` |

The full backend suite before the frontend build reported `96 passed, 2 skipped` because the generated-only static directory did not yet exist. After the production build, the same full suite reported `98 passed` with the existing single Starlette/HTTPX deprecation warning.

```text
.venv/bin/python -m pytest -q
98 passed, 1 warning in 41.63s

cd frontend
npm ci
exit 0; 129 packages installed, 0 vulnerabilities

npm run test:run
10 files passed; 35 tests passed

npm run build
exit 0; emitted index.html, hashed JS/CSS, fallback JSON, and bundled fonts

.venv/bin/python -m uvicorn backend.heatshift.api:app --host 127.0.0.1 --port 8000
started successfully; one process served the API and compiled SPA
```

The production smoke checks against that one process returned:

- `/healthz` — `200`, `{"status":"ok"}`;
- `/api/demo` — `200`, `demo-city-day-01`, `demo-v1`;
- base `/api/solve` — `200`, zero policy conflicts, no heat-shock plan in the zero-adjustment response;
- `/api/diagnose` for `job-bus-route` — `200`, `proven_infeasible`;
- `+2°C` `/api/solve` — `200`, heat-shock plan present;
- `/` and `/why` — `200` HTML; and
- `/fallback/demo.json` — `200` JSON.

The in-app browser loaded and refreshed the production HTML and requested the fallback JSON with `200` responses from the server, but its browser layer kept the React app in the loading state for the JSON-backed journey. The three-chapter manual completion could therefore not be observed in that browser surface; the limitation is recorded rather than presented as a successful manual walkthrough. Frontend tests and the one-process endpoint smoke remain green. No global package installation or manual source edit was used in the clean runtime.

## R01 — Live and disconnected demo rehearsals

**Candidate:** `b476da1` (`R00: rehearse fresh release`)

The production build was regenerated with `npm run build`, then one documented Uvicorn process was started on `127.0.0.1:8000`. The rehearsal script used only localhost HTTP calls and did not edit files, restart the process, or change the scenario/policy between runs.

### Live runs

Each run followed the storyboard evidence order: `/api/demo` brief, service-first solve, policy-constrained solve, designated diagnosis, and +2°C solve.

| Run | Duration | Brief | Service-first conflicts | Policy conflicts | Policy status | Diagnosis | Heat-shock recovery |
| ---: | ---: | --- | ---: | ---: | --- | --- | ---: |
| 1 | 13.94s | 41°C / 3 crews / 12 work orders | 11 | 0 | `OPTIMAL` | `proven_infeasible` | 60 min |
| 2 | 14.32s | 41°C / 3 crews / 12 work orders | 11 | 0 | `OPTIMAL` | `proven_infeasible` | 60 min |
| 3 | 14.18s | 41°C / 3 crews / 12 work orders | 11 | 0 | `OPTIMAL` | `proven_infeasible` | 60 min |

The runs also asserted that the designated diagnosis returned `INFEASIBLE` with four tested interventions and that the heat-shock diff contained `recovery_added`. The live story therefore uses only displayed response values: it does not infer that omission alone proves impossibility, and it names the exact diagnosis classification.

### Failure drill

Without restarting the process, a malformed `/api/solve` request returned HTTP `422` with `INVALID_SCENARIO`. The next `/api/demo` request returned HTTP `200`, proving the presenter could explain the honest validation state and return to the deterministic demo without a machine restart.

### Disconnected runs

Two consecutive runs used `/?fallback=true` and `/fallback/demo.json` from the same production process. Each returned HTTP `200`, matched all three canonical saved output hashes, and verified the saved base, +2°C, and `job-bus-route` diagnosis records. The production bundle contained the exact `SAVED SOLVER RUN` and `Live API unavailable` disclosure strings and referenced only local fallback data. The server log showed local HTML, JavaScript, font, and fallback-JSON requests; no external font, map, analytics, image, or data request was needed.

| Run | Duration | Mode | Disclosure | Hashes | Runtime data |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 0.01s | explicit saved mode | `SAVED SOLVER RUN / Live API unavailable` | matched | local only |
| 2 | 0.00s | explicit saved mode | `SAVED SOLVER RUN / Live API unavailable` | matched | local only |

### Remaining presentation risk

The in-app browser was refreshed once in live mode and once in saved mode. The server returned HTTP `200` for `/api/demo` and `/fallback/demo.json`, but the browser integration layer did not expose the JSON response to the page, leaving the shell in its loading state with chapter buttons disabled. Consequently, these R01 timings prove the production API/story and saved-data path, while manual click completion of all three rendered chapters remains unobserved in this browser surface. The limitation is the test surface, not an API failure; the existing frontend test suite covers the chapter transitions and the exact saved disclosure.

## R02 — Release capture

**Candidate:** `81efa5b` (`R01: rehearse live and disconnected demo`)

The production build was regenerated and the in-app browser was given a temporary `1440×900` viewport request. The browser backend remained capped at `1280×720`, so the actual captures are:

- `docs/release/screenshots/00-production-saved-loading.jpg`
- `docs/release/screenshots/01-production-live-loading.jpg`

Both are genuine production-build captures. They show the shell, policy boundary, solver evidence trust bar, and the honest live/saved loading states. The browser transport requested the local JSON with HTTP `200`, but the page remained loading; a complete six-frame loaded journey and an exported video were not produced. The exact four-minute narration script and source-backed values are in [docs/release/demo-rehearsal.md](../docs/release/demo-rehearsal.md). No screenshot value was composited, hidden, or changed from the saved release JSON.
