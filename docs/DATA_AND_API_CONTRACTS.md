# Data and API Contracts

This document defines the frontend/backend boundary. The backend supplies operational meaning explicitly; the frontend does not infer compliance or explanations from timestamps.

## 1. Conventions

- Times use local `HH:MM` plus integer `slot` indices.
- Durations are integer minutes aligned to `slot_minutes`.
- Temperatures use Celsius only in machine fields.
- Coordinates are schematic `[x, y]` values, not geographic claims.
- IDs are stable lowercase kebab-case strings.
- Solver statuses are `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, or `MODEL_INVALID`.
- Every result includes the policy ID and disclaimer used for the solve.

## 2. Scenario input

```json
{
  "id": "demo-city-day-01",
  "date": "2026-08-04",
  "slot_minutes": 15,
  "day_start": "07:00",
  "day_end": "17:00",
  "policy_id": "demo-city-hs-01",
  "crews": [],
  "jobs": [],
  "locations": [],
  "heat_series": [],
  "travel_matrix_location_ids": [],
  "travel_matrix_minutes": []
}
```

`travel_matrix_location_ids` defines the row and column order of `travel_matrix_minutes`. It must contain every location ID exactly once. Matrix entry `[i][j]` is the directed travel time from `travel_matrix_location_ids[i]` to `travel_matrix_location_ids[j]`.

### Crew

```json
{
  "id": "crew-asphalt",
  "name": "Asphalt Crew",
  "shift_start": "07:00",
  "shift_end": "16:00",
  "start_depot_id": "depot-central",
  "end_depot_id": "depot-central",
  "capabilities": ["asphalt", "traffic-control"],
  "equipment": ["patch-truck", "roller"],
  "max_overtime_minutes": 30,
  "recovery_profile": "cooled-vehicle-stationary"
}
```

### Work order

```json
{
  "id": "job-d107",
  "name": "Residential pothole batch",
  "location_id": "loc-d107",
  "active_minutes": 75,
  "exertion": "heavy",
  "priority": "planned",
  "service_value": 8,
  "window_start": "07:00",
  "window_end": "16:00",
  "required_capabilities": ["asphalt"],
  "required_equipment": ["patch-truck"],
  "locked": false,
  "locked_crew_id": null,
  "locked_start": null
}
```

When `locked` is `true`, the job must be served. A non-null `locked_crew_id` fixes its crew, and a non-null `locked_start` fixes its slot-aligned start. Null lock details leave that dimension to the solver.

### Heat slot

```json
{
  "slot": 20,
  "start": "12:00",
  "temperature_c": 39,
  "band": "severe"
}
```

## 3. Policy input

```json
{
  "id": "demo-city-hs-01",
  "name": "Demo City Policy HS-01",
  "synthetic": true,
  "disclaimer": "Synthetic demonstration policy only. Not medical, legal, or workplace-safety guidance.",
  "band_thresholds_c": {
    "elevated": 32,
    "severe": 38,
    "extreme": 42
  },
  "rolling_window_slots": 4,
  "eligible_recovery_profiles": ["cooled-vehicle-stationary"],
  "travel_counts_as_recovery": false,
  "rules": [
    {
      "id": "hs01-heavy-elevated",
      "band": "elevated",
      "exertion": "heavy",
      "max_active_slots": 3,
      "min_recovery_slots": 1,
      "stop_work": false
    }
  ]
}
```

Heat-band lower bounds are inclusive. Temperatures below `elevated` are `normal`; the greatest configured threshold not exceeding the adjusted temperature determines the other band. Thresholds must be strictly increasing. Only an explicitly scheduled recovery slot using a profile in `eligible_recovery_profiles` receives recovery credit. The bundled policy does not count travel or ordinary idle as recovery.

## 4. Solve response

```json
{
  "scenario": {
    "id": "demo-city-day-01",
    "policy_id": "demo-city-hs-01",
    "policy_disclaimer": "Synthetic demonstration policy only.",
    "slot_minutes": 15,
    "heat_adjustment_c": 0
  },
  "plans": {
    "service_first": {},
    "policy_constrained": {},
    "heat_shock": null
  },
  "plan_diff": [],
  "diagnostics": {}
}
```

### Plan

```json
{
  "label": "maximum_service_compliant_plan",
  "status": "OPTIMAL",
  "maximum_claim_allowed": true,
  "wall_time_seconds": 1.84,
  "stages": [
    {
      "name": "critical_service",
      "status": "OPTIMAL",
      "objective_value": 4,
      "best_bound": 4,
      "wall_time_seconds": 0.31
    }
  ],
  "metrics": {
    "critical_jobs_scheduled": 4,
    "critical_jobs_total": 4,
    "planned_service_value": 71,
    "mandatory_policy_conflicts": 0,
    "travel_minutes": 126,
    "overtime_minutes": 0,
    "active_work_minutes": 525,
    "eligible_recovery_minutes": 105
  },
  "timeline_segments": [],
  "route_segments": [],
  "jobs": []
}
```

`objective_value` and `best_bound` are numbers when the stage has an incumbent/bound and `null` when no such value exists. `maximum_claim_allowed` is `true` only when every required objective stage is `OPTIMAL`.

### Timeline segment

```json
{
  "crew_id": "crew-asphalt",
  "state": "work",
  "job_id": "job-d107",
  "start_slot": 9,
  "end_slot": 12,
  "start": "09:15",
  "end": "10:00",
  "exertion": "heavy",
  "location_id": "loc-d107",
  "policy_rule_ids": ["hs01-heavy-elevated"]
}
```

Valid states: `work`, `recovery`, `travel`, `idle`, `unavailable`.

### Route segment

```json
{
  "crew_id": "crew-asphalt",
  "from_location_id": "loc-d101",
  "to_location_id": "loc-d107",
  "departure": "09:01",
  "arrival": "09:15",
  "travel_minutes": 14,
  "from_coordinates": [180, 210],
  "to_coordinates": [470, 330]
}
```

### Job result

```json
{
  "job_id": "job-d107",
  "served": false,
  "crew_id": null,
  "start": null,
  "end": null,
  "status_reason_code": "POLICY_CAPACITY_CONFLICT"
}
```

### Plan difference

```json
{
  "job_id": "job-d107",
  "change": "deferred",
  "before": {
    "crew_id": "crew-asphalt",
    "start": "13:00",
    "end": "14:15"
  },
  "after": null,
  "binding_rule_ids": ["hs01-heavy-severe"],
  "explanation_code": "POLICY_CAPACITY_CONFLICT"
}
```

Allowed changes: `unchanged`, `moved_time`, `moved_crew`, `recovery_added`, `served`, `deferred`.

## 5. Diagnosis response

```json
{
  "job_id": "job-d107",
  "classification": "feasible_with_cost",
  "proof_status": "OPTIMAL",
  "retained_commitments": ["all-mandatory-rules", "all-critical-jobs"],
  "displaced_job_ids": ["job-d104"],
  "objective_delta": {
    "critical_service": 0,
    "planned_service_value": -4,
    "travel_minutes": 18,
    "overtime_minutes": 0
  },
  "binding_rule_ids": ["hs01-heavy-severe"],
  "tested_interventions": [
    {
      "type": "deadline_extension",
      "value_minutes": 30,
      "status": "OPTIMAL",
      "objective_delta": {
        "critical_service": 0,
        "planned_service_value": 0,
        "travel_minutes": 4,
        "overtime_minutes": 0
      }
    }
  ]
}
```

Classifications: `equivalent_alternative`, `feasible_with_cost`, `proven_infeasible`, `not_proven`.

## 6. API

### `GET /api/demo`

Returns the bundled scenario, policy, display coordinates, and optional saved genuine result metadata. Metadata is not a solve response:

```json
{
  "scenario": {},
  "policy": {},
  "display_coordinates": {},
  "saved_result_metadata": {
    "fixture_version": "demo-v1",
    "generated_at": "2026-08-01T12:00:00Z",
    "solver_version": "implementation-defined",
    "sha256": "implementation-defined"
  }
}
```

### `POST /api/solve`

Request:

```json
{
  "scenario": {},
  "policy": {},
  "heat_adjustment_c": 0,
  "time_limit_seconds": 5
}
```

Response semantics are fixed:

- `service_first` always uses the submitted operational inputs with heat-policy constraints disabled.
- `policy_constrained` always uses the unadjusted heat series and the submitted policy.
- `heat_shock` is `null` when `heat_adjustment_c` is zero. Otherwise it is the policy-constrained plan after applying the adjustment and remapping temperatures through `band_thresholds_c`.
- `plan_diff` compares `service_first` to `policy_constrained` when the adjustment is zero, and compares `policy_constrained` to `heat_shock` when the adjustment is nonzero.

If a solve finds an incumbent but does not prove optimality, return HTTP 200 with `FEASIBLE` and `maximum_claim_allowed: false`. Return `SOLVER_TIMEOUT` only when no reportable plan exists before the request budget expires.

### `POST /api/diagnose`

Request:

```json
{
  "scenario": {},
  "policy": {},
  "job_id": "job-d107",
  "heat_adjustment_c": 0,
  "time_limit_seconds": 5
}
```

Returns the forced-inclusion classification, objective delta, displaced jobs, proof status, binding rule IDs, and tested interventions.

## 7. Error contract

```json
{
  "error": {
    "code": "INVALID_SCENARIO",
    "message": "Scenario validation failed.",
    "details": [
      {
        "path": "jobs[2].required_equipment[0]",
        "code": "UNKNOWN_REFERENCE",
        "message": "Equipment 'vac-truck' is not present on any crew."
      }
    ]
  }
}
```

Required codes: `INVALID_SCENARIO`, `INVALID_POLICY`, `MODEL_INVALID`, `SOLVER_TIMEOUT`, `NO_FEASIBLE_PLAN`, and `INTERNAL_ERROR`.
