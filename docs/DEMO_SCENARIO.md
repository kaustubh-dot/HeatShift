# Demo Scenario

## 1. Purpose and honesty

The bundled scenario exists to exercise the complete product deterministically. It is evidence-informed but synthetic. It is not a validated representation of every municipality and must not be described as real operational data.

Scenario values may be tuned once during the solver spike to expose a nontrivial trade-off. Solver rules, objective ordering, and policy semantics must not be changed merely to manufacture favorable metrics.

## 2. Narrative

Demo City expects a hot afternoon. A public-works supervisor must schedule planned street and drainage maintenance using three pre-formed crews. Critical work should be retained where feasible, but heavy work and recovery must follow the city's synthetic policy.

Opening line:

> 41 C. Three crews. Twelve work orders. How much public service survives the heat?

## 3. Crews

| Crew | Capabilities | Attached equipment | Recovery condition |
|---|---|---|---|
| Asphalt Crew | Asphalt repair, traffic control | Patch truck, roller | Stationary cooled vehicle |
| Drainage Crew | Drain cleaning, inlet inspection, debris removal | Vac truck, drainage kit | Stationary cooled vehicle |
| General Crew | Signs, debris, minor concrete, inspection | Flatbed, mini-excavator, sign tools | Stationary cooled vehicle |

Crews are indivisible. Individual health or medical data is not represented.

## 4. Work-order catalogue

Initial values are scenario assumptions and must be encoded explicitly in the fixture.

| Work order | Active duration | Exertion | Priority | Eligible crews | Window/movability |
|---|---:|---|---|---|---|
| School-zone pothole cluster | 90 min | Heavy | Critical | Asphalt | Fixed morning window |
| Bus-route pavement failure | 120 min | Heavy | Critical | Asphalt | Same day |
| Residential pothole batch | 75 min | Heavy | Planned | Asphalt | Flexible |
| Utility-cut surface restoration | 90 min | Heavy | High | Asphalt | Before 15:00 |
| Blocked storm inlet | 45 min | Heavy | Critical | Drainage, General | Same day |
| Catch-basin cleaning | 60 min | Heavy | Planned | Drainage | Flexible |
| Culvert debris removal | 90 min | Heavy | High | Drainage, General | Before forecast rain |
| Drainage inspection | 30 min | Moderate | Planned | Drainage, General | Flexible |
| Damaged stop-sign replacement | 45 min | Moderate | Critical | General | Same day |
| Roadside debris clearance | 45 min | Moderate | High | General, Asphalt | Flexible |
| Guardrail inspection/temporary repair | 75 min | Moderate | High | General | Before 16:00 |
| Sidewalk trip-hazard patch | 120 min | Heavy | Planned | General, Asphalt | Deferrable |

The implemented fixture must define exact IDs, locations, service values, required equipment, and time windows. Shared eligibility must be real; a crew may not become eligible merely to improve the demo.

## 5. Heat series and policy

The initial heat series rises from normal morning conditions through elevated and severe afternoon bands. The policy fixture explicitly defines the inclusive band thresholds. The +2 C interaction remaps the same series without modifying those thresholds.

`Demo City Policy HS-01` is wholly synthetic and must display:

> Synthetic demonstration policy. Not medical, legal, or workplace-safety guidance. Organizations must supply and approve their own policy.

The policy uses 15-minute slots and a rolling four-slot window. Travel does not count as recovery. Stationary time in the crew's cooled vehicle may count when explicitly scheduled as recovery.

## 6. Travel

- Use a directed location matrix containing both depots and job locations, with an explicit location-ID row/column order.
- Keep travel values plausible and stable.
- Use schematic display coordinates independent of travel duration.
- Do not derive duration from straight-line SVG distance.
- Include depot-to-first and last-to-depot legs.

## 7. Scenario-quality gates

Proceed only when the scenario produces all of the following without hardcoded output:

- service-first plan with visible policy conflicts;
- policy-constrained plan with zero mandatory conflicts;
- at least two meaningful schedule changes;
- critical service preserved where the scenario is genuinely feasible;
- at least one deferred or substituted planned job;
- nontrivial travel/service trade-off;
- a counterfactual that yields an equivalent alternative, explicit cost, or proven infeasibility;
- a +2 C re-plan that changes a meaningful decision.

## 8. Anti-cherry-picking safeguards

- Store inputs and outputs in the repository.
- Never hardcode claimed metrics in frontend source.
- Show policy, travel matrix, and solver stage status.
- Add at least one perturbed regression fixture after the primary scenario works.
- Document the single tuning pass and preserve the pre-tuning fixture if practical.
- If all jobs trivially fit or every heavy job is forced into the morning, revise job windows/travel using plausible assumptions rather than weakening policy.
