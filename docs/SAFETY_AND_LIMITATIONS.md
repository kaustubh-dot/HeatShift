# Safety, Responsible Use, and Limitations

## 1. Product boundary

HeatShift is an operations-planning prototype. It applies policy inputs supplied by an organization to a synthetic or user-provided work scenario.

It does not:

- determine whether work is medically safe;
- diagnose, predict, or prevent heat illness;
- create an authoritative work/rest policy;
- certify OSHA, NIOSH, local-law, union, or contractual compliance;
- replace worksite measurements, emergency procedures, worker stop-work rights, or qualified professional judgment.

## 2. Bundled-policy disclaimer

The demo must display near the policy and result:

> Synthetic demonstration policy. Not medical, legal, or workplace-safety guidance. Organizations must supply and approve their own policy.

Do not describe the bundled numeric thresholds as OSHA-, NIOSH-, or medically approved.

## 3. Permitted claims

Examples:

- “On the bundled synthetic scenario, HeatShift produced a plan with zero conflicts against Demo City Policy HS-01.”
- “The counterfactual retained all critical jobs and changed the planned-service/travel trade-off by the displayed amounts.”
- “The optimizer proved the stated result optimal” only when the relevant stages return `OPTIMAL`.
- “No feasible plan exists under these retained commitments” only after an `INFEASIBLE` proof.

## 4. Prohibited claims

- “HeatShift makes schedules safe.”
- “HeatShift prevents heat illness.”
- “HeatShift guarantees compliance.”
- “HeatShift is the first heat-aware scheduler.”
- “This job cannot be served” when it was merely absent from one selected optimum.
- “This is the smallest necessary change” when only a bounded catalogue was tested.
- Generalized impact percentages derived from the synthetic scenario.

## 5. Data and privacy

The launch prototype uses no personal medical information. Crews are pre-formed resources. The system must not infer or expose individual fitness, medication, age, pregnancy, illness history, or heat tolerance.

If an employer assigns a crew policy class, HeatShift treats it as an opaque approved input and does not explain or validate the personnel decision behind it.

## 6. Technical limitations

- Synthetic scenario and policy
- One-day horizon and 15-minute discretization
- Small number of pre-formed crews and work orders
- Input travel-time matrix rather than street routing
- Schematic map rather than geographic navigation
- Simplified recovery conditions
- No forecast uncertainty model beyond the explicit heat-shock scenario
- Counterfactual interventions are bounded, not exhaustive
- Optimality depends on solver status and time limit

## 7. Worker and organizational safeguards

A production system would require domain validation, organizational governance, worker participation, privacy review, real worksite measurements, emergency escalation, jurisdiction-specific review, and integration with existing safety-management processes. These are future requirements, not implied capabilities of the hackathon prototype.
