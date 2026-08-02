# B14 Fixture Tuning Record

## Single primary tuning pass

The pre-tuning source temperatures were 30°C at slots 2–4 (`07:30`–`08:00`).
This single cohesive morning-curve adjustment changes those three values to
29°C; the bands remain `normal` under the unchanged policy thresholds.

Reason: after the submitted +2°C adjustment, the fixed school-zone job's only
candidate pattern crossed an elevated rolling window without enough committed
recovery at its boundary, making the shock model infeasible. Keeping the
early-morning source curve at 29°C leaves those slots normal after +2°C and
lets the same locked job remain feasible while preserving the policy, solver,
objective order, crew eligibility, and job locks.

The adjustment is within the synthetic scenario's documented normal morning
conditions. No policy rule, threshold, objective, capability, equipment,
critical label, solver branch, or output value was changed.

## Post-tuning evidence

The tuned fixture produces a service-first plan with visible policy conflicts,
a zero-conflict policy-constrained plan, multiple plan changes, a deferred
critical job, nontrivial travel, a forced-inclusion diagnosis, and a feasible
meaningfully different +2°C plan. Exact measured results are recorded in the
B14 checkpoint entry and generated saved outputs in B15.

The measured quality-gate values from the single diagnostic command are:

- service-first: 4 critical jobs, service value 400, 11 policy conflicts, and
  82 travel minutes;
- policy-constrained: 3 critical jobs, service value 368, zero policy
  conflicts, and 160 travel minutes;
- base comparison: `moved_time`, `deferred`, and `served` changes are present;
- diagnosis: `job-bus-route` is `proven_infeasible` with proof status `INFEASIBLE`;
- +2°C: seven decision changes, including two `recovery_added` changes, with
  60 eligible recovery minutes and zero policy conflicts.

## Perturbed regression fixture

`perturbed-scenario.json` changes exactly one non-policy input from the tuned
primary fixture: `job-drain-inspection.active_minutes` increases from 30 to 45
minutes. It is a regression input, not a second tuning pass.
