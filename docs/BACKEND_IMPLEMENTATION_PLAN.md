# HeatShift Backend Implementation Plan

## 1. How to use this plan

Execute one numbered packet at a time, in order. The controlling sequence and gate rules are in [IMPLEMENTATION_MASTER_PLAN.md](IMPLEMENTATION_MASTER_PLAN.md). This plan contains implementation decisions; an agent following it must not choose a different solver formulation or add product scope.

All backend paths are relative to the repository root. Tests live in `tests/`. Production code lives in `backend/heatshift/`.

## 2. Locked mathematical interpretation

These rules remove ambiguity for implementation:

- Slot `0` begins at `scenario.day_start`; `end_slot` is exclusive.
- Job active durations and locked starts must align to `slot_minutes`.
- Travel minutes may be non-aligned. Feasibility reserves `ceil(travel_minutes / slot_minutes)` slots; route metrics retain the exact matrix minutes.
- Matrix row and column order comes only from `travel_matrix_location_ids`.
- Adjusted temperatures are source temperature plus `heat_adjustment_c`; bands are remapped from the policy thresholds after adjustment.
- Every **full** rolling window of `rolling_window_slots` inside the scenario horizon is checked.
- If a rolling window contains work that triggers several rules, every triggered rule is enforced; this is equivalent to applying the most restrictive maximum-work and minimum-recovery requirements.
- Only `recovery` slots with a policy-approved crew recovery profile receive credit. Travel and idle do not.
- A constrained job pattern works as early as permitted and inserts recovery only when the next work slot would violate a fully visible job-local window or the current band prohibits work. Global constraints still check windows crossing job boundaries.
- Standalone recovery is a solver decision and is minimized only after the four required objective stages are fixed.
- Route order is represented by one acyclic source-to-sink flow through selected fixed-time patterns for each crew.
- A selected route arc reserves just-in-time travel immediately before its destination. The final depot leg begins immediately after the last job.
- `locked: true` fixes service. Non-null `locked_crew_id` and `locked_start` independently fix those dimensions.
- Required objective order is: critical job count, planned-service value, exact matrix travel minutes, overtime minutes. A fifth housekeeping stage minimizes standalone recovery slots without changing the first four optima.
- `maximum_claim_allowed` depends only on all four required stages being `OPTIMAL`.

If any implementation step cannot preserve these rules, stop and amend the canonical solver specification before coding further.

## B00 — Python project and pinned environment

### Read first

- [ARCHITECTURE.md](ARCHITECTURE.md), sections 3–7
- [TEST_PLAN.md](TEST_PLAN.md), sections 1 and 9–10

### Create

- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/heatshift/__init__.py`
- `tests/conftest.py`
- `.gitignore`

### Exact steps

1. Confirm a Python 3.12 interpreter exists. Do not use Python 3.14 for OR-Tools unless official package support is verified.
2. Create `.venv` at the repository root.
3. Upgrade `pip` inside that environment.
4. Install only runtime packages: OR-Tools, Pydantic, FastAPI, and Uvicorn.
5. Install only test packages: Pytest and HTTPX.
6. Record the exact successfully installed runtime versions in `backend/requirements.txt` with `==` pins.
7. Record `-r requirements.txt`, Pytest, and HTTPX exact pins in `backend/requirements-dev.txt`.
8. Add `.venv/`, Python caches, Pytest caches, coverage output, frontend dependencies/build output, and generated backend static assets to `.gitignore`.
9. Keep `backend/heatshift/__init__.py` empty except for an optional package version constant.

### Verification

Run:

```powershell
.\.venv\Scripts\python.exe -c "import ortools, pydantic, fastapi, pytest; print('imports-ok')"
.\.venv\Scripts\python.exe -m pip check
```

### Acceptance

- Both commands exit zero.
- Every dependency is exactly pinned.
- No application logic, fixture, API route, or speculative configuration is added.

## B01 — Canonical Pydantic models

### Read first

- All of [DATA_AND_API_CONTRACTS.md](DATA_AND_API_CONTRACTS.md)
- [SAFETY_AND_LIMITATIONS.md](SAFETY_AND_LIMITATIONS.md), sections 2–4

### Create

- `backend/heatshift/models.py`
- `tests/unit/test_models.py`

### Models to define

Define strict models for:

- `Crew`, `Job`, `Location`, `HeatSlot`, `Scenario`
- `PolicyRule`, `Policy`
- `SolveRequest`, `DiagnoseRequest`
- `Stage`, `Metrics`, `TimelineSegment`, `RouteSegment`, `JobResult`, `Plan`, `PlanDiff`, `SolveResponse`
- `ObjectiveDelta`, `TestedIntervention`, `DiagnosisResponse`
- `ApiErrorDetail`, `ApiError`
- `SavedResultMetadata`, `DemoResponse`

Use enums or `Literal` values for every finite vocabulary in the contract. Reject unknown fields with `extra='forbid'`. Use snake_case JSON field names exactly as documented. Do not introduce ORM behavior, aliases, database IDs, datetime libraries, or frontend-only types.

### Field rules

- IDs and names are non-empty strings.
- `slot_minutes`, durations, service values, and travel values are non-negative integers where applicable.
- Coordinates are exactly two finite numbers.
- `objective_value` and `best_bound` are nullable numbers.
- `plans.heat_shock` is nullable.
- Lock detail fields are nullable.
- `diagnostics` remains a plain dictionary reserved by the contract.

Cross-reference checks do not belong in model validators; B04 owns them.

### Tests

- Parse every JSON example from the canonical contract after filling `{}` placeholders with minimal valid objects.
- Reject an unknown field.
- Reject an unknown enum/status/change/classification.
- Accept null stage objective/bound.
- Round-trip a model with `model_dump(mode='json')` and parse it again.

### Acceptance

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_models.py -q
```

All tests pass. No solver or fixture logic exists yet.

## B02 — Time grid, heat remapping, and matrix helpers

### Create

- `backend/heatshift/timegrid.py`
- `tests/unit/test_timegrid.py`

### Functions

Implement small pure functions:

- parse `HH:MM` to minutes after midnight;
- format minutes after midnight as `HH:MM`;
- convert aligned time to slot index relative to `day_start`;
- convert slot index to `HH:MM`;
- convert aligned active duration to slot count;
- convert travel minutes to reserved slots using ceiling division;
- build `{location_id: matrix_index}` from `travel_matrix_location_ids`;
- read directed travel minutes by two location IDs;
- remap a temperature using inclusive `band_thresholds_c`;
- produce an adjusted `HeatSlot` series without mutating the input.

### Exact heat rule

Sort thresholds by temperature ascending. A temperature below `elevated` is `normal`. Otherwise choose the band with the greatest threshold less than or equal to the value. Reject missing `elevated`, `severe`, or `extreme` keys in B04, not here.

### Tests

- `07:00` is slot 0 and `17:00` is slot 40 for the demo.
- `09:15` is slot 9.
- 14 travel minutes reserve one slot; 16 reserve two.
- Threshold values themselves enter the new band.
- `31.9`, `32`, `38`, and `42` map correctly for demo thresholds.
- Applying +2 does not mutate the original series.
- Directed matrix lookup distinguishes `i -> j` from `j -> i`.

### Acceptance

Run only `test_timegrid.py`; all cases pass.

## B03 — Deterministic scenario and policy fixtures

### Create

- `backend/heatshift/fixtures/scenario.json`
- `backend/heatshift/fixtures/policy.json`
- `tests/unit/test_fixture_shape.py`

### Scenario constants

- ID: `demo-city-day-01`
- Date: `2026-08-04`
- Horizon: `07:00`–`17:00`
- Slot size: 15 minutes
- Policy ID: `demo-city-hs-01`
- One depot: `depot-central`
- All crews start and end at that depot.
- Crew shifts: `07:00`–`16:00`, maximum overtime 30 minutes.
- Recovery profile for all crews: `cooled-vehicle-stationary`.

### Crews

| ID | Name | Capabilities | Equipment |
|---|---|---|---|
| `crew-asphalt` | Asphalt Crew | `asphalt-repair`, `traffic-control`, `debris-removal`, `minor-concrete` | `patch-truck`, `roller` |
| `crew-drainage` | Drainage Crew | `drain-cleaning`, `inlet-service`, `debris-removal`, `inspection` | `vac-truck`, `drainage-kit` |
| `crew-general` | General Crew | `sign-service`, `debris-removal`, `minor-concrete`, `inspection` | `flatbed`, `mini-excavator`, `sign-tools` |

### Work orders

Use the following values exactly before the one permitted B14 tuning pass:

| ID | Name | Location | Min | Exertion | Priority/value | Window | Capabilities | Equipment | Lock |
|---|---|---|---:|---|---|---|---|---|---|
| `job-school-potholes` | School-zone pothole cluster | `loc-school` | 90 | heavy | critical/100 | 07:00–10:30 | asphalt-repair, traffic-control | patch-truck | serve + asphalt + 07:15 |
| `job-bus-route` | Bus-route pavement failure | `loc-bus-route` | 120 | heavy | critical/100 | 07:00–16:30 | asphalt-repair | patch-truck | none |
| `job-residential` | Residential pothole batch | `loc-residential` | 75 | heavy | planned/8 | 07:00–16:00 | asphalt-repair | patch-truck | none |
| `job-utility-cut` | Utility-cut surface restoration | `loc-utility-cut` | 90 | heavy | high/30 | 08:00–15:00 | asphalt-repair | patch-truck, roller | none |
| `job-blocked-inlet` | Blocked storm inlet | `loc-blocked-inlet` | 45 | heavy | critical/100 | 07:00–14:00 | debris-removal | none | none |
| `job-catch-basin` | Catch-basin cleaning | `loc-catch-basin` | 60 | heavy | planned/10 | 07:00–16:00 | drain-cleaning | vac-truck | none |
| `job-culvert` | Culvert debris removal | `loc-culvert` | 90 | heavy | high/32 | 09:00–15:30 | debris-removal | none | none |
| `job-drain-inspection` | Drainage inspection | `loc-drain-inspection` | 30 | moderate | planned/6 | 07:00–16:00 | inspection | none | none |
| `job-stop-sign` | Damaged stop-sign replacement | `loc-stop-sign` | 45 | moderate | critical/100 | 07:00–14:00 | sign-service | sign-tools | none |
| `job-roadside-debris` | Roadside debris clearance | `loc-roadside-debris` | 45 | moderate | high/24 | 07:00–16:00 | debris-removal | none | none |
| `job-guardrail` | Guardrail inspection/temporary repair | `loc-guardrail` | 75 | moderate | high/28 | 09:00–16:00 | sign-service | flatbed | none |
| `job-sidewalk` | Sidewalk trip-hazard patch | `loc-sidewalk` | 120 | heavy | planned/12 | 08:00–16:00 | minor-concrete | none | none |

Priority is not inferred from service value. Store both fields.

### Locations and display coordinates

Use this exact matrix/display order:

```text
depot-central, loc-school, loc-bus-route, loc-residential,
loc-utility-cut, loc-blocked-inlet, loc-catch-basin, loc-culvert,
loc-drain-inspection, loc-stop-sign, loc-roadside-debris,
loc-guardrail, loc-sidewalk
```

Coordinates in the same order:

```text
[400,300], [260,160], [150,260], [180,420], [350,220],
[620,180], [700,310], [660,480], [520,410], [470,120],
[330,460], [100,120], [480,520]
```

Use this directed matrix exactly; each row follows the declared order:

```text
0,12,18,22,10,20,24,28,16,11,17,25,21
13,0,11,20,9,18,23,29,17,8,15,14,22
17,10,0,12,13,25,29,31,21,16,11,9,24
21,18,11,0,14,28,25,20,13,22,8,20,12
11,8,14,15,0,15,20,24,10,9,12,19,16
19,17,24,27,14,0,9,17,12,13,22,30,19
23,22,28,24,19,8,0,12,10,20,18,33,14
27,28,30,19,23,16,11,0,9,25,15,35,8
16,17,20,12,10,11,9,8,0,14,9,27,7
10,7,15,21,8,12,19,24,13,0,16,18,20
17,14,10,7,11,21,17,14,8,16,0,22,9
24,13,8,19,18,29,32,34,26,17,21,0,30
20,21,23,11,15,18,13,7,6,19,8,29,0
```

### Heat series

Create 40 entries, one per slot. Temperatures by hour are:

```text
07: 29,29,30,30
08: 30,31,31,31
09: 32,32,33,33
10: 34,34,35,35
11: 36,37,37,38
12: 38,39,39,40
13: 40,40,41,41
14: 41,41,40,40
15: 39,39,38,38
16: 37,36,35,34
```

Derive each stored band using the policy thresholds; do not type contradictory bands manually.

### Policy fixture

- Synthetic disclaimer: exact text from [SAFETY_AND_LIMITATIONS.md](SAFETY_AND_LIMITATIONS.md).
- Thresholds: elevated 32°C, severe 38°C, extreme 42°C.
- Rolling window: four slots.
- Eligible profile: `cooled-vehicle-stationary`.
- Travel does not count as recovery.

Rules:

| Band | Heavy max work/min recovery/stop | Moderate max work/min recovery/stop |
|---|---|---|
| normal | 4 / 0 / false | 4 / 0 / false |
| elevated | 3 / 1 / false | 4 / 0 / false |
| severe | 2 / 2 / false | 3 / 1 / false |
| extreme | 0 / 4 / true | 2 / 2 / false |

Give each rule ID the exact form `hs01-{exertion}-{band}`.

### Tests and acceptance

At B03, test only model parsing, counts, stable IDs, 40 heat slots, 13×13 matrix shape, and expected eligibility from tags. Full semantic validation belongs to B04.

## B04 — Cross-reference and semantic validation

### Create

- `backend/heatshift/validation.py`
- `tests/unit/test_validation.py`

### Public behavior

Return all discovered issues in stable path order. Each issue contains `path`, `code`, and `message`, matching `ApiErrorDetail`. Raise one domain validation exception holding that list only at the boundary.

### Required validations

1. Unique IDs within crews, jobs, locations, heat slots, and policy rules.
2. Scenario policy ID equals submitted policy ID.
3. `day_start < day_end`; horizon divides by slot size.
4. Crew shifts, job windows, durations, and locked starts are inside the horizon and aligned.
5. Start/end depots and every job location exist.
6. Lock crew exists, is eligible, and lock start lies in the job window.
7. Every required capability/equipment exists on at least one crew; every locked job has an eligible crew.
8. Heat slots cover every slot exactly once, in order, with aligned `start` and a band matching its temperature.
9. Threshold keys are exactly elevated, severe, extreme and strictly increase.
10. Policy has exactly one rule for every heat-band/exertion pair used by jobs.
11. Rule values are within `0..rolling_window_slots`; stop-work implies max active zero.
12. Matrix IDs equal the location-ID set exactly; matrix is square; diagonal is zero; other values are positive integers.
13. No duplicate matrix location ID.

Use precise paths such as `jobs[2].required_equipment[0]` and stable codes such as `DUPLICATE_ID`, `UNKNOWN_REFERENCE`, `NOT_SLOT_ALIGNED`, `INVALID_MATRIX`, and `INVALID_THRESHOLD`.

### Tests

One focused test per rule plus one test that multiple errors are returned in deterministic path order. Never invoke OR-Tools from validation tests.

## B05 — Execution-pattern generator

### Create

- `backend/heatshift/patterns.py`
- `tests/unit/test_patterns.py`

### Internal immutable record

`ExecutionPattern` contains:

- stable ID;
- job ID and crew ID;
- start/end slots, end exclusive;
- ordered work slots;
- ordered committed-recovery slots;
- location and exertion;
- applicable rule IDs by work slot; and
- a normalized segment list.

### Eligibility

A crew is eligible only when it contains every required capability and equipment tag. Apply lock crew/start filters before generation.

### Baseline patterns

For every eligible start slot, produce a continuous-work pattern of exactly `active_minutes / slot_minutes` work slots. Reject it if it exceeds job window, crew shift plus allowed overtime, day horizon, depot-reachability bounds, or lock fields. Baseline ignores heat rules only; it does not ignore operations.

### Policy-constrained patterns

For every eligible start slot:

1. The start slot is the first work slot; do not generate leading recovery.
2. Walk forward until all active slots are placed.
3. At each slot, first remap/read its heat band and find the job's policy rule.
4. If work is prohibited, append committed recovery when the crew profile is eligible; otherwise reject.
5. Otherwise tentatively append work.
6. Evaluate every full rolling window wholly visible in the tentative pattern. Determine rules triggered by work slots in that window.
7. If the tentative work violates any triggered maximum or minimum-recovery rule, append eligible recovery instead and retry work at the next slot.
8. Reject when no progress is possible, required recovery is ineligible, or the commitment would exceed the job/crew/day bound.
9. Stop immediately after the final active slot; no trailing recovery belongs to the job pattern.
10. Merge adjacent same-state slots into normalized segments.

Sort patterns by `(job_id, crew_id, start_slot, end_slot, pattern_id)`.

### Mandatory tests

Implement the seven pattern cases in [TEST_PLAN.md](TEST_PLAN.md), plus:

- exact active slot count;
- no work in heavy/extreme slots;
- locked start produces no alternate start;
- baseline contains no recovery;
- generator output order is stable; and
- input models are not mutated.

The consecutive-pattern global case belongs to B06. At B05, create only the small reusable fixture/helper for it; do not add a skipped or expected-failure test.

## B06 — CP-SAT selection, route flow, and global policy

### Create

- `backend/heatshift/optimizer.py`
- `tests/unit/test_optimizer_constraints.py`

### Model inputs

The optimizer receives validated scenario/policy objects and a sorted list of patterns. It never reads files or emits API models.

### Decision variables

- `x[p]`: pattern selected.
- `serve[j]`: job served; equal to the sum of its pattern variables.
- `crew_used[c]`: at least one pattern selected for the crew.
- `start_arc[p]`: depot is the predecessor of pattern `p`.
- `route_arc[p,q]`: pattern `q` immediately follows `p` on the same crew.
- `end_arc[p]`: pattern `p` is followed by the depot.
- `standalone_recovery[c,t]`: an eligible recovery slot outside job commitment and travel.

Create route arcs only when patterns belong to different jobs on the same crew and `p.end_slot + ceil(travel(p,q)/slot_minutes) <= q.start_slot`. Time-ordered arcs make cycles impossible.

### Selection and lock constraints

- `serve[j] == sum(x[p] for job j)` and at most one pattern per job.
- `serve[j] == 1` when `locked` is true.
- Pattern generation already filters locked crew/start; assert this invariant in tests.

### Route-flow constraints

For each pattern:

- incoming start/route arcs sum to `x[p]`;
- outgoing route/end arcs sum to `x[p]`.

For each crew:

- start arcs sum to `crew_used[c]`;
- end arcs sum to `crew_used[c]`;
- selected patterns imply `crew_used[c]`;
- a start arc exists only if depot travel fits before the pattern;
- an end arc exists only if the depot return fits within shift plus overtime.

Because arcs always move forward in time and there is one source/sink, every selected pattern belongs to one depot-connected path; no disconnected subtour is possible.

### Slot occupancy

For each crew/slot, form linear expressions for selected pattern work and committed recovery. Constrain work + committed recovery + standalone recovery to at most one.

Standalone recovery is forced to zero:

- outside the crew shift/overtime horizon;
- when its recovery profile is not policy-approved;
- during any selected start, route, or end arc's reserved travel slots; and
- during selected job commitment slots through the occupancy constraint.

For middle/start travel, reserve the ceiling-rounded slots immediately before destination start. For the final depot leg, reserve slots immediately after the last pattern.

### Global rolling constraints

For every crew and every full rolling window:

1. Sum all selected work slots, regardless of job.
2. Sum committed plus standalone eligible recovery.
3. For every pattern whose selected work inside the window triggers rule `r`, add conditional constraints:
   - total work `<= r.max_active_slots` when `x[p]`;
   - total eligible recovery `>= r.min_recovery_slots` when `x[p]`.

Applying every triggered conditional rule implements the most restrictive rule and prevents consecutive jobs from bypassing recovery.

### Objective expressions exposed to B07

- critical served count;
- total planned-service value across all served jobs;
- exact directed travel minutes across selected start/middle/end arcs;
- overtime minutes from selected end arcs relative to regular shift end;
- standalone recovery slot count.

### Required tests

- no job double-selection;
- no crew double occupancy;
- capability/equipment filters survive into selected output;
- route begins/ends at depot;
- no disconnected route;
- directed travel feasibility uses ceiling slots;
- consecutive locally valid jobs require global recovery;
- travel and idle receive no recovery credit;
- stop-work slots have no prohibited work;
- all lock dimensions remain fixed.

Use tiny purpose-built scenarios, not the full demo, for each invariant.

## B07 — Staged lexicographic solving and proof capture

### Modify/create

- modify `backend/heatshift/optimizer.py`
- `tests/unit/test_objectives_and_status.py`

### Solver configuration

- fixed random seed stored as one module constant;
- one search worker for deterministic behavior;
- no search logging by default;
- request `time_limit_seconds` is the total budget;
- allocate the remaining budget across unfinished required stages so total wall time does not intentionally exceed the request budget.

### Stage procedure

For each required stage in order:

1. Set the objective.
2. Solve.
3. Capture normalized status, incumbent objective or null, best bound or null, and measured wall time.
4. If `OPTIMAL`, fix the exact objective value and continue.
5. If `FEASIBLE`, keep the incumbent, stop required-stage optimization, and do not claim later objectives were optimized.
6. If `INFEASIBLE`, `UNKNOWN`, or `MODEL_INVALID`, stop and return that proof state to the service layer.

After all four required stages are proven optimal, minimize standalone recovery slots as a housekeeping stage. It may affect which tied plan is displayed but never the maximum-service claim.

### Status mapping

Map OR-Tools statuses only through one tested function. Unknown OR-Tools values are `MODEL_INVALID`, not guessed.

### Tests

- lower stages cannot sacrifice fixed higher-stage values;
- `maximum_claim_allowed` is true only when all four required stages are optimal;
- feasible-only never uses maximum wording;
- null values serialize for stages without incumbent/bound;
- same input/seed produces the same selected pattern and arc IDs.

## B08 — Timeline, routes, metrics, and conflict reconciliation

### Create

- `backend/heatshift/metrics.py`
- `tests/unit/test_metrics_and_serialization.py`

### Extraction order

1. Read selected pattern, arc, and standalone-recovery variables from the solver result.
2. For each crew, follow the unique start arc and successor arcs to build route order. Assert every selected pattern is visited once.
3. Build route segments using exact matrix minutes and schematic coordinates.
4. Reserve ceiling-rounded travel slots for timeline display exactly as the model did.
5. Paint work, committed recovery, standalone recovery, travel, idle, and unavailable slots into a 40-slot crew state array. Raise an internal model error on any collision.
6. Merge adjacent slots only when state, job, location, exertion, and rule IDs all match.
7. Build one `JobResult` per scenario job in stable job-ID order.
8. Compute metrics only from extracted job/timeline/route facts.

### Metric definitions

- critical counts from served `JobResult` records;
- planned-service value from served jobs' stored service values;
- policy conflicts from the independent evaluator below;
- exact travel minutes from route segments, not reserved timeline slots;
- overtime from route completion beyond regular shift end;
- active and recovery minutes from timeline slots.

### Independent policy-conflict evaluator

For every crew/full window, inspect serialized slot states. Collect rules triggered by work slot band/exertion. Count one conflict for the window when any triggered max-work, min-recovery, or stop-work rule fails. Return both count and involved rule IDs/job IDs. Do not reuse CP-SAT constraint expressions.

### Tests

Hand-build one small selected solution and assert every timeline segment, route segment, metric, and conflict. Add a corruption test proving reconciliation detects a mismatch.

## B09 — Solve orchestration

### Create

- `backend/heatshift/service.py`
- `tests/integration/test_solve_service.py`

### `solve_scenario` sequence

1. Validate inputs.
2. Generate baseline patterns with policy disabled.
3. Solve and serialize the service-first plan.
4. Independently evaluate that plan against the submitted policy.
5. Generate unadjusted constrained patterns.
6. Solve and serialize the policy-constrained plan.
7. Assert/reconcile zero conflicts or raise `MODEL_INVALID`.
8. When adjustment is zero, set `heat_shock` null and compare baseline to constrained.
9. When adjustment is nonzero, also execute B13's adjusted constrained solve; retain the unadjusted constrained plan in its canonical field.
10. Return a canonical `SolveResponse` with the exact policy ID/disclaimer.

Do not cache until deterministic saved output is implemented in B15.

### Acceptance

The untuned demo may fail scenario-quality gates here, but it must either return a schema-valid response or a precise solver status/error. No hardcoded metrics or plan differences are allowed.

## B10 — Plan differences

### Create

- `backend/heatshift/differences.py`
- `tests/unit/test_differences.py`

### Classification precedence

For each job in stable ID order:

1. before served, after not served → `deferred`;
2. before not served, after served → `served`;
3. both served, different crew → `moved_crew`;
4. both served, same crew/start but after adds committed recovery → `recovery_added`;
5. both served, start or end differs → `moved_time`;
6. otherwise → `unchanged`.

Populate before/after from `JobResult`. Binding rule IDs come from solver/evaluator evidence: after-pattern rules for moved/recovery cases and baseline conflict evidence for a policy-deferred job. Never derive an explanation from color or name.

Tests cover all six types and precedence when more than one field changes.

## B11 — Forced-inclusion diagnosis

### Create

- `backend/heatshift/diagnostics.py`
- `tests/unit/test_diagnostics.py`

### Inputs

- validated scenario/policy;
- original proven/best constrained plan;
- deferred job ID;
- heat adjustment and time budget.

Reject unknown or already-served job IDs with structured validation details.

### Retained commitments

Always retain mandatory policy rules. Also require the forced solve to preserve the original number of served critical jobs. Record:

```text
all-mandatory-rules
original-critical-service-count
forced-job:{job_id}
```

### Procedure and classification

1. Build a fresh constrained model; do not mutate/reuse the original model.
2. Add `serve[target] == 1`.
3. Add critical served count `>=` the original count.
4. Run the same objective stages.
5. If proven infeasible, classify `proven_infeasible`.
6. If no incumbent and no proof, classify `not_proven`.
7. If feasible, compare critical count, service value, travel, overtime, and served set.
8. Classify `equivalent_alternative` only when the objective vector is proven equal.
9. Otherwise classify `feasible_with_cost`, even when the cost is only an incumbent estimate; preserve the proof status.

Displaced IDs are original served jobs absent from the forced plan. Objective delta is forced minus original. Binding IDs come from the target pattern and policy-conflict evidence, never from a canned table.

Tests use purpose-built scenarios for all four classifications.

## B12 — Bounded interventions

### Modify

- `backend/heatshift/diagnostics.py`
- `tests/unit/test_interventions.py`

### Catalogue and order

Test each candidate independently from the original input:

1. `deadline_extension`, 15 minutes;
2. `deadline_extension`, 30 minutes;
3. `overtime_allowance`, 15 minutes for eligible crews;
4. `overtime_allowance`, 30 minutes for eligible crews.

For every intervention, deep-copy the submitted models, modify only the declared field, validate again, force the target job, and solve with the same retained commitments. Record status and objective delta. Do not stop after the first success; the UI needs the bounded comparison.

Do not claim smallest, minimal, safest, or recommended intervention. The ordered list is a tested catalogue only.

## B13 — +2°C heat shock

### Modify/create

- modify `backend/heatshift/service.py`
- `tests/integration/test_heat_shock.py`

### Procedure

1. Preserve the original scenario object.
2. Add the submitted adjustment to every source temperature.
3. Remap every band through policy thresholds.
4. Regenerate constrained patterns and solve from scratch.
5. Keep `service_first` and unadjusted `policy_constrained` in their fields.
6. Put the adjusted plan in `plans.heat_shock`.
7. Compare unadjusted constrained to adjusted constrained in `plan_diff`.

Test exact threshold crossings, immutability, unchanged jobs/crews/priorities/policy, and response semantics for both zero and +2 adjustments.

## B14 — Single declared scenario-tuning pass

### Inputs

Use one diagnostic command that prints, without UI:

- each plan's objective vector/status;
- served/deferred IDs;
- conflict count/rules;
- route order/travel;
- recovery minutes;
- base diff types;
- one diagnosis summary; and
- +2°C decision changes.

### Allowed changes

If a gate fails, make one cohesive fixture-only adjustment to plausible:

- noncritical service values;
- nonlocked job windows;
- directed travel values;
- initial temperatures within the documented narrative; or
- noncritical job durations within the catalogue's plausible scale.

### Forbidden changes

- policy thresholds/rules;
- objective ordering;
- critical labels merely to force a result;
- capabilities/equipment merely to add eligibility;
- solver code conditional on demo IDs;
- output JSON edits; or
- more than one undocumented tuning cycle.

Record before/after input changes and reasons in `backend/heatshift/fixtures/TUNING.md`. Pass every scenario-quality gate before B15.

After the primary fixture passes, create `perturbed-scenario.json` by changing exactly one non-policy input (prefer a 15-minute extension to one noncritical active duration). Add a regression test proving it validates, solves without invariant failure, and does not rely on hardcoded demo output. Document the single perturbation in `TUNING.md`; it is not a second tuning pass.

## B15 — Deterministic saved evidence

### Create

- `backend/heatshift/cli.py`
- saved JSON files under `backend/heatshift/fixtures/saved/`
- `tests/integration/test_determinism.py`

### CLI commands

Provide commands for:

- validate fixtures;
- solve base scenario;
- diagnose the designated deferred job;
- solve +2°C;
- generate all saved artifacts and manifest.

The manifest records fixture version, UTC generation time, Python version, OR-Tools version, solver seed/workers, input hashes, and output hashes. Runtime measurements may vary; either normalize them out of byte-determinism comparison or compare a canonical projection excluding only documented runtime fields.

The future frontend fallback bundle has this exact wrapper shape:

```text
fixture_version
generated_at
scenario
policy
base_solve
heat_shock_solve
diagnoses              # object keyed by diagnosed job ID
manifest               # solver/input/output provenance
```

Copy that self-contained bundle to `frontend/public/fallback/demo.json` only when frontend F01 creates the directory. Until then the backend saved files are canonical.

## B16 — FastAPI endpoints and error mapping

### Create

- `backend/heatshift/api.py`
- `tests/integration/test_api.py`

### Routes

- `GET /api/demo`
- `POST /api/solve`
- `POST /api/diagnose`
- optional `GET /healthz` returning only process readiness

Use the exact request/response models. Load bundled inputs through one service function. Map Pydantic/cross-reference errors, model invalidity, no-result timeout, and no feasible plan to the canonical error envelope. Do not expose tracebacks or raw OR-Tools text.

HTTP behavior:

- invalid input: 422;
- feasible/optimal solve: 200;
- no reportable incumbent before timeout: 504;
- proven no feasible plan for a solve request: 409;
- internal/model error: 500.

Do not add authentication, CORS configuration for arbitrary origins, database setup, background queues, or telemetry.

## B17 — Backend release gate

### Required commands

Run from a clean environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m backend.heatshift.cli validate
.\.venv\Scripts\python.exe -m backend.heatshift.cli generate-saved
```

Then run the saved-generation command twice and compare canonical hashes. Measure total base solve and diagnosis time on the development laptop.

### Gate report

Write `backend/RELEASE_EVIDENCE.md` containing:

- dependency/runtime versions;
- test count and command;
- P0 invariant results;
- base, constrained, diagnosis, and shock objective/status summaries;
- scenario-quality gate results;
- deterministic hash comparison;
- measured wall times; and
- known limitations copied without inflation from the safety document.

Only after this report passes may `CHECKPOINT.md` mark Phase 1 complete and name F00 as next.
