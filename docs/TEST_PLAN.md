# Test and Validation Plan

## 1. Test strategy

The solver is the highest-risk component and receives the deepest testing. Tests should verify observable contracts and invariants, not implementation details.

## 2. P0 solver invariants

- Every served work order selects exactly one execution pattern and crew.
- No crew occupies more than one state in a slot.
- Selected patterns complete exactly the required active-work slots.
- Recovery inside a committed job blocks unrelated work and travel.
- Standalone recovery receives credit only under an eligible condition.
- Travel and ordinary idle receive no recovery credit in the bundled policy.
- Global rolling policy rules hold across individual patterns and consecutive jobs.
- Stop-work slots contain no prohibited active work.
- Crew capabilities and attached-equipment requirements are never violated.
- Every route transition uses the matrix duration.
- No job starts before its crew can arrive.
- Every scheduled route begins and ends at the configured depot.
- No disconnected subtour exists.
- Locked assignments/times remain unchanged.
- Critical service is optimized before planned-service value.
- Identical input and configuration produce identical serialized output.

## 3. Pattern-generator cases

1. Continuous work allowed: pattern has only required work slots.
2. 45/15 rule: a 90-minute job contains valid recovery and a longer elapsed duration.
3. Severe-band transition: work/recovery sequence changes at the correct slot.
4. Stop-work transition: candidate work slot is rejected.
5. Ineligible recovery location: pattern is rejected or requires standalone eligible recovery.
6. Window overflow: pattern ending after the deadline is rejected.
7. Consecutive patterns: global constraints insert/require recovery when each job alone appears valid.

## 4. Objective and status tests

- A lower objective stage never sacrifices a proven higher-stage optimum.
- `OPTIMAL` permits the configured maximum wording.
- `FEASIBLE` never produces `maximum_claim_allowed: true`.
- `INFEASIBLE` language states the commitments under which proof was obtained.
- `UNKNOWN` and timeout language explicitly avoids an infeasibility claim.
- Stage objective values and best bounds serialize correctly.

## 5. Counterfactual tests

- Deferred job with an equal alternative is classified `equivalent_alternative`.
- Forced inclusion that displaces work reports the exact displaced IDs and objective delta.
- Forced inclusion with a proof is classified `proven_infeasible` only on `INFEASIBLE`.
- Time-limited analysis is classified `not_proven`.
- Tested interventions are independently solved and never labelled globally minimal.
- Reported binding rule IDs exist in the submitted policy.

## 6. Metric reconciliation

Recompute from serialized timeline/route data and compare with backend metrics:

- served critical jobs;
- planned-service value;
- policy conflicts;
- work and recovery minutes;
- travel minutes;
- overtime;
- per-crew totals.

## 7. Validation and API tests

- Unknown IDs return precise reference paths.
- Misaligned durations/times are rejected.
- Invalid windows and travel matrices are rejected before solver construction.
- Travel-matrix location IDs contain every scenario location exactly once and define matrix row/column order.
- Heat-band thresholds are strictly increasing and remap +2 C values at exact boundaries.
- Recovery receives credit only for policy-approved recovery-profile IDs.
- Locked service, crew, and start fields are enforced independently when present.
- `/api/demo`, `/api/solve`, and `/api/diagnose` conform to the documented schemas.
- Error responses conform to the common error envelope.
- Saved presentation fallback uses the same contract as live responses.

## 8. Frontend critical-journey tests

- Demo loads in one click.
- Baseline and compliant plans display the correct labels and metrics.
- Timeline segments and route lines match backend IDs and order.
- A moved/deferred job opens the correct diagnosis.
- Heat shock replaces plan data rather than animating canned values.
- `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, and API failure states remain usable.
- Reduced-motion mode displays the same information without transition dependence.
- Keyboard users can reach primary actions and diagnosis content.

## 9. Performance gates

- Bundled solve targets less than five seconds on the development laptop.
- Diagnosis is bounded and reports timeout honestly.
- Initial saved-result render is interactive quickly enough for a live presentation.
- Animations do not block controls or conceal final values.

## 10. Release gate

Release requires:

- all P0 invariants passing;
- complete deterministic demo journey;
- zero unexplained metric mismatches;
- no unsupported optimality, safety, compliance, or impact wording;
- fresh-start local run succeeding from documented commands;
- recorded fallback available.
