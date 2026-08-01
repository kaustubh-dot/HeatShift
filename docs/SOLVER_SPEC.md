# Solver Specification

## 1. Purpose

The solver determines which municipal work orders can be completed by pre-formed crews during one day while satisfying operational and employer-defined heat-policy constraints. It also evaluates the consequences of forcing deferred work into the plan.

## 2. Time and scope

- One planning day
- Fifteen-minute slots
- Three pre-formed crews in the bundled scenario
- Approximately twelve work orders
- One start/end depot per crew
- Directed matrix travel times
- Deterministic inputs and solver configuration

## 3. Domain entities

### Crew

A crew is indivisible during the planning day and contains:

- shift start/end;
- start/end depot;
- capability tags;
- attached equipment tags;
- overtime allowance;
- recovery-condition profile.

The model does not assess individual medical vulnerability. If the employer assigns a policy class to a mixed crew, that employer-supplied classification controls.

### Work order

A work order contains:

- location;
- required active-work slots;
- exertion class;
- priority class and planned-service value;
- allowed time window;
- required capability/equipment tags;
- mandatory/locked flag;
- permitted crews derived from eligibility.

### Policy

The policy is employer-defined and versioned. It maps heat band and exertion to:

- maximum active slots in a rolling window;
- minimum eligible recovery slots;
- stop-work conditions;
- inclusive temperature thresholds that map adjusted temperatures to heat bands;
- eligible recovery-profile IDs;
- optional overtime and lock rules.

The bundled policy is synthetic and prominently labelled as such.

## 4. Job execution

Jobs are **recovery-interruptible and crew-committed**:

- active work may pause for eligible recovery;
- the job cannot change crews or location;
- its equipment remains occupied;
- the crew cannot travel, idle, or work elsewhere during the commitment interval;
- completion occurs only after all required active slots are executed.

A 90-minute job under a 45/15 policy may therefore occupy 105 elapsed minutes: 45 work, 15 recovery, 45 work.

## 5. Candidate execution patterns

For each eligible `(job, crew, start slot)`, generate possible commitment patterns containing:

- start/end slot;
- crew/job assignment;
- ordered `work` and `recovery` slots;
- location and exertion;
- policy rule IDs active in each slot;
- required active-slot total.

Reject a pattern when it:

- falls outside the work-order window or crew shift;
- performs work in a stop-work slot;
- uses ineligible recovery conditions;
- does not complete the required active slots;
- violates job-local commitment or recovery rules.

Pattern generation reduces model complexity and directly provides timeline segments. It does **not** replace global rolling constraints across the full crew schedule.

## 6. Global crew timeline

For each crew and slot, exactly one state applies:

- active work on a selected pattern;
- committed recovery inside a pattern;
- standalone eligible recovery between jobs;
- travel;
- ordinary idle;
- unavailable/outside shift.

Travel receives no recovery credit in the bundled policy. Ordinary idle receives recovery credit only when it is explicitly selected as recovery and the crew's configured condition is eligible.

Aggregate work and recovery expressions are derived from selected patterns and gap-state variables. Rolling policy constraints are applied to every relevant window across the entire crew day, preventing two individually valid jobs from bypassing recovery when scheduled consecutively.

Every full rolling window inside the scenario horizon is checked. When a window spans multiple heat bands or exertion classes, every rule triggered by active work in that window is enforced; this is equivalent to applying the lowest active-work maximum and highest recovery minimum among triggered rules.

For deterministic candidate generation, a constrained job works as early as permitted from its candidate start and inserts recovery only when the next work slot would violate a fully visible job-local window or that slot prohibits work. Windows crossing job boundaries are enforced globally. Standalone eligible recovery remains an explicit solver decision.

## 7. Selection and routing

Decision concepts:

- `select_pattern[p]`: candidate pattern is used;
- `serve[j]`: work order is scheduled;
- `assign[c,j]`: work order is assigned to crew;
- `transition[c,i,j]`: `j` immediately follows `i` on crew `c`;
- depot start/end transitions;
- optional standalone recovery states.

Constraints:

1. At most one pattern is selected per work order.
2. A selected pattern implies one eligible crew assignment.
3. Selected commitment intervals for a crew do not overlap.
4. Every selected job has one route predecessor and successor.
5. Depot flow and ordering/circuit constraints prevent subtours.
6. Successor start respects predecessor completion plus matrix travel.
7. Travel, work, recovery, idle, and unavailable states do not overlap.
8. Locked jobs/assignments remain fixed when supplied.

The directed travel matrix uses the explicit `travel_matrix_location_ids` order. Never assume that display-coordinate order or alphabetical location order matches the matrix.

## 8. Baseline

The primary baseline is a **service-first counterfactual**:

- same crews, jobs, equipment, travel, time windows, priorities, and shifts;
- same lexicographic service objectives;
- mandatory heat-policy constraints disabled;
- resulting plan evaluated against the policy to count conflicts.

It is an ablation, not a claim about current municipal practice.

## 9. Lexicographic objectives

Solve sequentially:

1. Maximize critical jobs served.
2. Fix stage 1 optimum; maximize weighted planned-service value.
3. Fix stages 1–2; minimize matrix travel minutes.
4. Fix stages 1–3; minimize overtime.
5. After the four required stages are fixed, minimize explicitly scheduled standalone recovery as a housekeeping tie-breaker. This stage does not affect maximum-service wording.

Capture status, objective value, best bound, and runtime for every stage. Do not fix a stage as optimal unless CP-SAT proves it. If a stage is only feasible, stop or continue under a clearly documented incumbent policy; never call the final plan globally optimal.

## 10. Counterfactual service diagnosis

For each selected deferred job:

1. Add `serve[j] = 1`.
2. Preserve mandatory constraints and the declared retained commitments.
3. Rerun the objective hierarchy.
4. Compare the objective vector and scheduled set with the original plan.

Classify:

| Classification | Meaning |
|---|---|
| `equivalent_alternative` | Same proven objective vector; a different plan may serve the job |
| `feasible_with_cost` | Job can be served with explicit displacement, service, travel, or overtime cost |
| `proven_infeasible` | CP-SAT proved no plan under the stated retained commitments |
| `not_proven` | Time/limits prevented a proof |

The system never equates omission from one optimum with infeasibility.

## 11. Bounded interventions

Test only declared alternatives, such as:

- equal-priority substitution;
- deadline extension by 15 or 30 minutes;
- overtime allowance by 15 or 30 minutes;
- availability of an appropriately equipped alternate crew;
- next-day deferral.

Report Pareto-like outcomes or the lowest-ranked successful tested intervention. Never claim the globally smallest repair. An assumption core, if used, is a sufficient non-minimal conflict diagnostic only.

## 12. Heat shock

The synthetic +2 C control adds two degrees to each source temperature, remaps values using the policy's inclusive `band_thresholds_c`, regenerates affected patterns, and reruns the same optimization. It must not modify jobs, crews, priorities, or policy values.

## 13. Determinism and runtime

- Sort IDs and candidate patterns before model creation.
- Set a documented solver seed and worker configuration.
- Serialize arrays in stable order.
- Target a live-demo solve below five seconds for the bundled scenario.
- Label `FEASIBLE`, `INFEASIBLE`, and `UNKNOWN` exactly as specified in the PRD.
