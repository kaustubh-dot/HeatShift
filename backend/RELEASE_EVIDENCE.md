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
