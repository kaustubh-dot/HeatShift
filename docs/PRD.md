# Product Requirements Document

## 1. Product summary

**Product:** HeatShift: Policy-Constrained Service Optimizer
**Track:** Sustainability & Climate Tech
**Release:** Orion hackathon prototype

HeatShift helps a municipal planned-maintenance supervisor determine how much public service can be completed during a hot-weather day while satisfying an employer-defined heat policy. It compares a service-first counterfactual with a policy-constrained plan, explains operational changes, and quantifies the cost of forcing deferred work back into the plan.

## 2. Problem

A supervisor must reconcile work orders, crew capabilities, equipment, travel, time windows, urgency, exertion, recovery requirements, and changing heat conditions. Conventional dispatch tools may optimize service and travel or issue weather alerts, but the operational cost of applying a heat policy is often difficult to inspect.

HeatShift must answer:

> What is the highest-service feasible plan under the organization's mandatory policy, and what must change to include work that was deferred?

## 3. User and job to be done

### Primary user

A municipal planned-maintenance supervisor preparing the next day's schedule for pre-formed street, drainage, and general-maintenance crews.

### Job to be done

When a hot-weather day threatens the planned workload, help me produce and defend a feasible crew plan that preserves critical service, applies our approved policy consistently, and makes every trade-off inspectable.

## 4. Product principles

1. **Policy execution, not policy invention.** The organization owns every safety rule.
2. **Proof before prose.** Explanations originate from solver results, not an LLM.
3. **Service and safety are ordered priorities.** Mandatory rules are never weakened by a presentation mode.
4. **No fabricated optimality.** The UI distinguishes optimal, feasible, infeasible, unknown, and invalid states.
5. **Visuals reveal the model.** Routes, timeline changes, recovery, and metrics are driven by result data.
6. **Deterministic demonstration.** The core journey does not depend on network services.

## 5. Goals

- Produce a valid service-first counterfactual and policy-constrained plan from identical operational inputs.
- Retain the maximum proven critical and weighted planned service under mandatory rules.
- Model crews, attached equipment, job capabilities, travel, work, and eligible recovery.
- Explain deferred work using forced-inclusion counterfactual optimization.
- Re-plan after a synthetic +2 C heat shock.
- Communicate the transformation within a three-to-five-minute judge demo.

## 6. Non-goals

- Creating or certifying heat-safety policy
- Assessing individual medical vulnerability
- Replacing worksite measurement or professional judgment
- Street-level routing or navigation
- Production municipal integration
- Real-time or multi-day dispatch
- Employee tracking, payroll, notifications, or a worker application
- Natural-language policy ingestion

## 7. Functional requirements

### FR-1: Guided scenario

The application shall load a complete synthetic scenario without account creation, uploads, or API keys.

### FR-2: Scenario inspection

The user shall be able to inspect crews, attached capabilities/equipment, work orders, locations, travel times, time windows, exertion, heat bands, and policy rules.

### FR-3: Service-first counterfactual

The system shall optimize the scenario using all operational constraints while disabling mandatory heat-policy rules. It shall evaluate and display the conflicts that plan would create under the policy.

### FR-4: Policy-constrained plan

The system shall generate a plan with zero mandatory policy conflicts or report that no compliant plan was proven.

### FR-5: Plan comparison

The UI shall compare critical jobs, weighted planned service, policy conflicts, travel, overtime, work, and recovery using synchronized timelines and a schematic map.

### FR-6: Honest proof state

Each lexicographic stage shall expose its status, objective value, best bound, and runtime. The word “maximum” may appear only when every required stage is proven optimal.

### FR-7: Deferred-job diagnosis

For a selected deferred job, the system shall force its inclusion and classify the result as:

- equivalent optimum;
- feasible with substitution or objective cost;
- proven infeasible under the stated retained commitments; or
- not proven within the analysis limit.

### FR-8: Bounded interventions

The system shall test a small declared intervention catalogue and report successful alternatives without claiming global minimality.

### FR-9: Heat shock

The user shall apply a synthetic +2 C adjustment and receive a new plan, plan difference, metrics, and diagnostics.

### FR-10: Presentation fallback

The frontend shall be able to render saved, genuine solver results if the live solver cannot be reached during presentation.

## 8. Non-functional requirements

- Identical inputs and configured seed produce identical output.
- Bundled solves target less than five seconds on the development laptop; every timeout is handled honestly.
- No core journey requires internet access.
- The first useful state is visible in one click.
- Keyboard navigation and reduced-motion behavior cover the critical journey.
- All displayed operational numbers reconcile with serialized solver output.
- The frontend shall not infer policy meaning from colors or timestamps alone; explicit codes and state fields are required.

## 9. Success measures

### Engineering success

- Zero mandatory conflicts in the recommended plan.
- Matrix-derived travel continuity.
- At least one meaningful reschedule and one solver-derived deferred-job diagnosis.
- Heat shock changes at least one meaningful decision.
- Invariants and contract tests pass.

### Judge success

- Problem understood within ten seconds.
- Before/after operational change understood within thirty seconds.
- Judge can inspect the exact policy rule and solver proof behind a change.
- Demo completes in three to five minutes without unsupported safety claims.

## 10. Release acceptance

The hackathon prototype is release-ready only when the complete journey—brief, counterfactual, compliant plan, diagnosis, and heat shock—runs from a fresh start and every claim shown by the UI is present in the backend result contract.
