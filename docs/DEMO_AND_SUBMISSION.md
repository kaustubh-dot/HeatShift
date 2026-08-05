# Demo and submission plan

HeatShift should be judged as an operations-planning prototype, not as a weather dashboard. The demo needs to prove one idea: an approved heat policy changes a real service plan, and the optimizer makes the resulting trade-offs inspectable.

## Judge thesis

Heat alerts identify dangerous conditions. HeatShift answers the scheduling question that follows: what is the highest public service available under the policy, and what would it cost to add the work that had to be deferred?

## Story for a three to five minute demo

| Time | Presenter action | What the judge should take away |
|---|---|---|
| 0:00 to 0:25 | Open Tomorrow's Brief and state the scenario. | The problem is concrete: 41°C, three crews, twelve work orders. |
| 0:25 to 0:50 | Point out the synthetic-policy notice. | HeatShift applies supplied policy. It does not invent safety guidance. |
| 0:50 to 1:25 | Open the service-first view. | Serving all four critical jobs creates 11 policy conflicts. |
| 1:25 to 2:05 | Transform to the constrained plan and inspect its timeline and map. | The `OPTIMAL` plan has zero conflicts, three critical jobs, value 368, and no overtime. |
| 2:05 to 2:45 | Select the deferred bus-route repair. | A deferral is a question to test, not a conclusion. |
| 2:45 to 3:25 | Show the forced-inclusion diagnosis and intervention results. | The tool proves `INFEASIBLE` only under visible retained commitments. |
| 3:25 to 3:55 | Apply the synthetic +2°C heat shock. | The plan changes transparently and adds 60 eligible recovery minutes. |
| 3:55 to 4:25 | Close on the architecture and the boundary. | The prototype is technically reproducible and clear about its limits. |

For a three-minute cut, keep the opening scenario, constrained-plan transformation, one diagnosis, and the heat shock. Do not spend time editing inputs live.

## Demo rules

- Start at `http://127.0.0.1:8000/?fallback=true` for a deterministic recording.
- Use the bundled scenario. Do not alter figures while recording.
- Show the solver status beside each major claim.
- Say "synthetic policy" once and leave the boundary visible.
- Do not call an omitted job impossible until the diagnosis reports `INFEASIBLE`.
- Do not claim medical validation, legal compliance, real-world impact percentages, or turn-by-turn routing.
- If the recording fails, restart at the brief and record the full story again. Do not splice different scenarios together.

## What supports the demo

- Versioned scenario, policy, and saved solver outputs in the repository
- OR-Tools CP-SAT scheduling with staged objectives and proof states
- Complete timelines, route records, metrics, and plan differences from the solver response
- Forced-inclusion diagnosis for deferred work
- Synthetic +2°C re-plan
- Local fallback results that match the bundled scenario exactly
- Fresh-start setup instructions, tests, and an evidence audit

## Likely judge questions

### Is the policy medically validated?

No. The bundled policy is synthetic. HeatShift applies an organization-approved policy consistently; it does not create or certify one.

### Is the deferred work actually impossible?

Not because it is absent from one plan. HeatShift forces the selected job into a new solve and reports a feasible alternative, a visible displacement, or an `INFEASIBLE` proof under the listed commitments.

### Is this street routing?

No. The optimizer sequences crew travel using a directed travel-time matrix. The interface calls the visual a schematic service map and does not provide navigation.

### Why is this more than weather-aware scheduling?

The useful difference is counterfactual diagnosis. HeatShift shows the service, travel, overtime, and recovery consequences of including deferred work while keeping the policy constraints visible.

## Submission materials

Use [SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md) for the exact Devpost fields, copy, build tags, image plan, video upload steps, and final pre-submit checklist. Use [release/demo-rehearsal.md](release/demo-rehearsal.md) while recording.
