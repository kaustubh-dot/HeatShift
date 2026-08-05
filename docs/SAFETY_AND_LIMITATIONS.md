# Safety and limitations

## What HeatShift does

HeatShift is an operations-planning prototype. It applies an organization's policy inputs to a synthetic or user-provided work scenario and produces a schedule subject to those inputs.

The bundled Demo City policy is synthetic. It exists to demonstrate the product and is not medical, legal, or workplace-safety guidance.

## What HeatShift does not do

HeatShift does not:

- determine whether work is medically safe;
- diagnose, predict, or prevent heat illness;
- create or validate a work and recovery policy;
- certify OSHA, NIOSH, legal, union, or contractual compliance;
- replace worksite measurements, emergency procedures, worker stop-work rights, or qualified professional judgment;
- evaluate individual fitness for work or use personal medical information.

## Claims the demo may make

- On the bundled synthetic scenario, HeatShift found a plan with zero conflicts against Demo City Policy HS-01.
- The counterfactual displays the service, travel, recovery, and overtime trade-offs produced by the stated inputs.
- HeatShift may call a result maximum only when the relevant solver stages return `OPTIMAL`.
- HeatShift may state that no feasible plan exists only when a forced-inclusion diagnosis returns `INFEASIBLE` under the visible retained commitments.

## Claims the demo must not make

- "HeatShift makes schedules safe."
- "HeatShift prevents heat illness."
- "HeatShift guarantees compliance."
- "HeatShift is the first heat-aware scheduler."
- "This job cannot be served" when it was only absent from one selected plan.
- "This is the smallest necessary change" when the tool tested only a bounded intervention catalogue.
- A generalized safety, productivity, compliance, or public-impact percentage based on the synthetic demo.

## Data and privacy

The launch prototype uses no personal medical data. Crews are represented as pre-formed operational resources. HeatShift does not infer or expose a person's health, medication, age, pregnancy, illness history, or heat tolerance.

An employer may assign a crew policy class as an approved input. HeatShift treats that class as opaque and does not justify the personnel decision behind it.

## Technical limits

- One planning day in 15-minute slots
- Three pre-formed crews and twelve synthetic work orders in the bundled demo
- Supplied travel-time matrix rather than street navigation
- Schematic map rather than geographic directions
- Simplified recovery conditions
- No forecast uncertainty model beyond the explicit +2°C scenario
- Bounded interventions rather than an exhaustive search for every possible operational change
- Solver proof that depends on model status and time limit

## What a production deployment would need

A real deployment would require an organization-approved policy, domain validation, worker participation, privacy review, current worksite measurements, emergency escalation, jurisdiction-specific review, and integration with existing safety-management processes. Those requirements are outside this hackathon prototype.
