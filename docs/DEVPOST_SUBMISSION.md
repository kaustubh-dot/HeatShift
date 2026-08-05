# HeatShift project copy

This page contains the public project claims and short copy used for the OrionHackathon Devpost entry. The detailed field-by-field upload instructions are in [SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md).

## Title

HeatShift: Policy-Constrained Service Optimizer

## Elevator pitch

HeatShift helps municipal teams plan essential maintenance during extreme heat. It finds the highest service level that meets an approved heat policy, then explains each trade-off.

## Project description

### Inspiration

Extreme heat does not pause public maintenance. Roads still need repairs, drainage still needs clearing, and crews still need a schedule that respects the limits their organization has approved. A weather alert tells a supervisor that the day will be difficult. It does not tell them which work order should move, where recovery belongs, or whether a deferred repair can still fit without breaking the policy.

We built HeatShift around that operational gap.

### What it does

HeatShift plans one day of municipal maintenance for a synthetic Demo City. It starts with a service-first counterfactual, then produces a policy-constrained plan using the same crews, jobs, travel times, and heat conditions. The interface makes the trade-off visible through timelines, a schematic service map, route order, recovery, travel, overtime, service value, and solver proof.

The most important interaction starts after a job has been deferred. Selecting that job launches a forced-inclusion counterfactual. HeatShift either finds a feasible alternative, shows the work that would need to move, or proves that no feasible plan exists under the retained commitments. A synthetic +2°C heat shock then re-plans the same day and shows the exact changes.

### How we built it

The frontend is React and TypeScript. FastAPI serves the API and the compiled single-page app. The scheduling engine uses OR-Tools CP-SAT with deterministic inputs, a fixed seed, one search worker, and versioned saved results for repeatable demos.

The model schedules crews, equipment, travel, work, and recovery in 15-minute slots. It first maximizes critical jobs served, then service value, then minimizes travel and overtime. The final tie-breaker minimizes standalone recovery. The frontend receives solver-derived metrics, route sequences, timelines, differences, and proof states instead of recreating planning logic in the browser.

### Challenges we ran into

The hard part was avoiding a polished but misleading planner. A job omitted from one schedule is not necessarily impossible, so we built a separate forced-inclusion solve instead of labelling every deferral as infeasible. We also had to enforce rolling work and recovery rules across a crew's full day, not just inside individual jobs.

We kept the demo reproducible by committing the scenario, policy, and saved solver outputs. That makes the result inspectable and gives judges a reliable fallback if live solving is unavailable.

### Accomplishments we are proud of

HeatShift turns an abstract safety constraint into a concrete operational decision. In the bundled scenario, the service-first plan handles all four critical jobs but creates 11 policy conflicts. The policy-constrained plan is `OPTIMAL`, has zero conflicts, serves three of four critical jobs, and shows exactly what changed.

The deferred bus-route repair is classified as `proven_infeasible` only after a forced-inclusion solve returns `INFEASIBLE` under stated commitments. The +2°C scenario keeps the plan policy-constrained while adding 60 eligible recovery minutes. These are synthetic-demo results, not estimates of real municipal performance.

### What we learned

The useful output is not a black-box schedule. A supervisor needs to understand why work moved and what a change would cost. Showing proof status, constraints, and plan differences made the optimization easier to inspect without pretending the model can replace human judgment.

### What is next

A production version would need an organization-approved policy, local operational data, worker participation, privacy review, worksite measurements, emergency escalation, and jurisdiction-specific validation. Those are deliberately outside this prototype.

## Evidence used in the demo

| Moment | Bundled result |
|---|---|
| Opening brief | 41°C, 3 crews, 12 work orders |
| Service-first counterfactual | 4 of 4 critical jobs, value 400, 11 conflicts, 82 travel minutes |
| Policy-constrained plan | `OPTIMAL`, 3 of 4 critical jobs, value 368, 0 conflicts, 160 travel minutes, 0 overtime |
| Deferred bus-route repair | `proven_infeasible` with `INFEASIBLE` proof under retained commitments |
| +2°C heat shock | `OPTIMAL`, 0 conflicts, 60 eligible recovery minutes added |

The source map for these values is in [EVIDENCE_AUDIT.md](EVIDENCE_AUDIT.md).

## Technology

Python 3.12, OR-Tools CP-SAT, Pydantic, FastAPI, Uvicorn, React, TypeScript, Vite, Vitest, React Testing Library, and local bundled fonts.

## Claim boundary

HeatShift uses a synthetic scenario and a synthetic demonstration policy. It does not provide medical, legal, or workplace-safety guidance; certify compliance; diagnose heat illness; replace worksite measurements; or determine individual fitness for work. The map is schematic and the travel model uses a supplied directed matrix rather than street navigation.
