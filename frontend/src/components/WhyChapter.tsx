import { useEffect, useRef } from "react";

import { MetricsBar, PlanDiffBadge, PlanDiffCard, PlanProof } from "./primitives";
import type { DiagnosisResponse, Job, Plan, PlanDiff, SolveResponse } from "../types";
import type { RequestStatus } from "../state/appState";

const CLASSIFICATION_COPY: Record<DiagnosisResponse["classification"], string> = {
  equivalent_alternative: "equivalent alternative",
  feasible_with_cost: "feasible with displayed cost",
  proven_infeasible: "proven infeasible under listed commitments",
  not_proven: "not proven within limit",
};

const INTERVENTION_LABELS: Record<DiagnosisResponse["tested_interventions"][number]["type"], string> = {
  deadline_extension: "Deadline extension",
  overtime_allowance: "Overtime allowance",
};

const OBJECTIVE_LABELS: Record<keyof DiagnosisResponse["objective_delta"], string> = {
  critical_service: "Critical service",
  planned_service_value: "Planned service value",
  travel_minutes: "Travel minutes",
  overtime_minutes: "Overtime minutes",
};

function signed(value: number): string {
  return value > 0 ? `+${value}` : `${value}`;
}

function ObjectiveDeltaList({ delta, label }: { delta: DiagnosisResponse["objective_delta"]; label: string }) {
  return (
    <dl className="diagnosis-objective-list" aria-label={label}>
      {(Object.keys(OBJECTIVE_LABELS) as Array<keyof DiagnosisResponse["objective_delta"]>).map((key) => (
        <div className="diagnosis-objective" key={key}>
          <dt>{OBJECTIVE_LABELS[key]}</dt>
          <dd className="data-value">{signed(delta[key])}</dd>
        </div>
      ))}
    </dl>
  );
}

function stateSummary(state: PlanDiff["before"]): string {
  if (state === null) return "Not scheduled";
  return `${state.crew_id ?? "Unassigned"} · ${state.start ?? "—"}–${state.end ?? "—"}`;
}

interface WhyChapterProps {
  job: Job | null;
  diagnosis: DiagnosisResponse | null;
  jobs?: Job[];
  policyPlan?: Plan | null;
  heatShockResult?: SolveResponse | null;
  heatShockStatus?: RequestStatus;
  heatShockError?: string | null;
  selectedJobId?: string | null;
  onJobClick?: (jobId: string) => void;
  onApplyHeatShock?: (request: { heat_adjustment_c: 2 }) => void;
  onResetHeatShock?: () => void;
  diagnosisRequestStatus?: RequestStatus;
  diagnosisRequestError?: string | null;
}

export function WhyChapter({
  job,
  diagnosis,
  jobs = [],
  policyPlan = null,
  heatShockResult = null,
  heatShockStatus = "idle",
  heatShockError = null,
  selectedJobId = null,
  onJobClick = () => undefined,
  onApplyHeatShock = () => undefined,
  onResetHeatShock = () => undefined,
  diagnosisRequestStatus = "idle",
  diagnosisRequestError = null,
}: WhyChapterProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (diagnosisRequestStatus === "success") headingRef.current?.focus();
  }, [diagnosisRequestStatus, diagnosis]);

  if (job === null || diagnosis === null) {
    return (
      <section className="fixture-error" role="alert" aria-labelledby="diagnosis-error-heading">
        <p className="label-caps">Diagnosis unavailable</p>
        <h1 id="diagnosis-error-heading">The designated diagnosis is missing.</h1>
        <p>{diagnosisRequestError ?? "The saved solver bundle did not include the designated diagnosis response."}</p>
      </section>
    );
  }

  const classification = CLASSIFICATION_COPY[diagnosis.classification];
  const shockPlan = heatShockStatus === "success" ? heatShockResult?.plans.heat_shock ?? null : null;
  const firstDecision = shockPlan === null ? null : heatShockResult?.plan_diff.find((diff) => diff.change !== "unchanged") ?? null;
  const jobNames = new Map(jobs.map((candidate) => [candidate.id, candidate.name]));

  return (
    <section className="why-chapter" aria-labelledby="diagnosis-heading">
      <header className="why-chapter__hero">
        <p className="label-caps">Forced-inclusion diagnosis</p>
        <h1 id="diagnosis-heading" ref={headingRef} tabIndex={-1}>
          {job.name}
        </h1>
        <p className="why-chapter__job-id data-value">{diagnosis.job_id}</p>
        <div className="diagnosis-result" aria-label="Diagnosis classification and proof status">
          <span className="diagnosis-result__classification">{classification}</span>
          <span className="solver-evidence__status" data-status={diagnosis.proof_status}>
            {diagnosis.proof_status}
          </span>
        </div>
        <p className="why-chapter__summary">This result preserves the listed commitments and reports the solver proof beside the classification.</p>
      </header>

      <section className="heat-shock-control" aria-labelledby="heat-shock-heading">
        <div>
          <p className="label-caps">Bounded what-if</p>
          <h2 id="heat-shock-heading">Test the day at +2°C.</h2>
          <p>Re-run the constrained plan with the returned heat adjustment and keep this diagnosis in view.</p>
        </div>
        <div className="heat-shock-control__actions">
          <button
            aria-label="Apply plus 2 degrees Celsius heat shock to re-optimize the plan"
            className="primary-action"
            disabled={heatShockStatus === "loading"}
            onClick={() => onApplyHeatShock({ heat_adjustment_c: 2 })}
            type="button"
          >
            <span>Apply +2°C Heat Shock</span>
            <span aria-hidden="true">↗</span>
          </button>
          {shockPlan !== null && (
            <button className="secondary-button" onClick={onResetHeatShock} type="button">
              Reset heat shock
            </button>
          )}
          {heatShockStatus === "loading" && (
            <p className="heat-shock-status" role="status" aria-live="polite">
              SOLVING…
            </p>
          )}
          {heatShockStatus === "error" && (
            <p className="heat-shock-status heat-shock-status--error" role="alert">
              {heatShockError ?? "The heat-shock response could not be loaded."}
            </p>
          )}
        </div>
      </section>

      {shockPlan !== null && policyPlan !== null && firstDecision !== null && (
        <section className="heat-shock-result" aria-labelledby="heat-shock-result-heading" aria-busy={heatShockStatus === "loading"}>
          <header className="section-heading-row">
            <div>
              <p className="label-caps">Returned heat-shock response</p>
              <h2 id="heat-shock-result-heading">The first decision changes before the supporting totals.</h2>
            </div>
            <span className="data-value">+{heatShockResult?.scenario.heat_adjustment_c}°C</span>
          </header>

          <section className="heat-shock-decision" aria-labelledby="heat-shock-decision-heading">
            <div>
              <p className="label-caps">First meaningful decision</p>
              <h3 id="heat-shock-decision-heading">{jobNames.get(firstDecision.job_id) ?? firstDecision.job_id}</h3>
              <p className="heat-shock-decision__job-id data-value">{firstDecision.job_id}</p>
            </div>
            <PlanDiffBadge change={firstDecision.change} />
            <div className="heat-shock-decision__states">
              <span>
                <small>Before</small>
                {stateSummary(firstDecision.before)}
              </span>
              <span aria-hidden="true">→</span>
              <span>
                <small>After</small>
                {stateSummary(firstDecision.after)}
              </span>
            </div>
          </section>

          <MetricsBar current={shockPlan.metrics} baseline={policyPlan.metrics} />
          <PlanProof plan={shockPlan} />

          <section className="heat-shock-diff-section" aria-labelledby="heat-shock-diff-heading">
            <div className="section-heading-row">
              <div>
                <p className="label-caps">Returned evidence</p>
                <h3 id="heat-shock-diff-heading">Every heat-shock difference</h3>
              </div>
              <span className="data-value">{heatShockResult?.plan_diff.length ?? 0} work-order records</span>
            </div>
            <div className="heat-shock-diff-list">
              {heatShockResult?.plan_diff.map((diff) => (
                <PlanDiffCard
                  diff={diff}
                  isSelected={diff.job_id === selectedJobId}
                  jobName={jobNames.get(diff.job_id) ?? diff.job_id}
                  key={diff.job_id}
                  onClick={() => onJobClick(diff.job_id)}
                />
              ))}
            </div>
          </section>
        </section>
      )}

      <div className="diagnosis-grid">
        <section className="diagnosis-panel" aria-labelledby="commitments-heading">
          <p className="label-caps">Held constant</p>
          <h2 id="commitments-heading">Retained commitments</h2>
          <ul className="diagnosis-list">
            {diagnosis.retained_commitments.map((commitment) => (
              <li className="data-value" key={commitment}>
                {commitment}
              </li>
            ))}
          </ul>
        </section>

        <section className="diagnosis-panel" aria-labelledby="displaced-heading">
          <p className="label-caps">Displacement evidence</p>
          <h2 id="displaced-heading">Displaced job IDs</h2>
          {diagnosis.displaced_job_ids.length === 0 ? (
            <p className="diagnosis-empty data-value">None returned</p>
          ) : (
            <ul className="diagnosis-list">
              {diagnosis.displaced_job_ids.map((jobId) => (
                <li className="data-value" key={jobId}>
                  {jobId}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="diagnosis-panel diagnosis-panel--wide" aria-labelledby="delta-heading">
          <div className="section-heading-row">
            <div>
              <p className="label-caps">Objective delta</p>
              <h2 id="delta-heading">Counterfactual cost</h2>
            </div>
            <span className="data-value">{diagnosis.proof_status}</span>
          </div>
          <ObjectiveDeltaList delta={diagnosis.objective_delta} label="Counterfactual objective delta" />
        </section>

        <section className="diagnosis-panel" aria-labelledby="rules-heading">
          <p className="label-caps">Policy evidence</p>
          <h2 id="rules-heading">Binding rule IDs</h2>
          <ul className="diagnosis-list">
            {diagnosis.binding_rule_ids.map((ruleId) => (
              <li className="data-value" key={ruleId}>
                {ruleId}
              </li>
            ))}
          </ul>
        </section>

        <section className="diagnosis-panel diagnosis-panel--wide" aria-labelledby="interventions-heading">
          <div className="section-heading-row">
            <div>
              <p className="label-caps">Bounded tests</p>
              <h2 id="interventions-heading">Tested interventions</h2>
            </div>
            <span className="data-value">{diagnosis.tested_interventions.length} tested</span>
          </div>
          <div className="intervention-table-wrap">
            <table className="intervention-table">
              <caption className="sr-only">Every tested intervention returned by the diagnosis solver</caption>
              <thead>
                <tr>
                  <th scope="col">Intervention</th>
                  <th scope="col">Value</th>
                  <th scope="col">Status</th>
                  <th scope="col">Objective delta</th>
                </tr>
              </thead>
              <tbody>
                {diagnosis.tested_interventions.map((intervention) => (
                  <tr key={`${intervention.type}-${intervention.value_minutes}`}>
                    <th scope="row">{INTERVENTION_LABELS[intervention.type]}</th>
                    <td className="data-value">{intervention.value_minutes} min</td>
                    <td>
                      <span className="solver-evidence__status" data-status={intervention.status}>
                        {intervention.status}
                      </span>
                    </td>
                    <td>
                      <ObjectiveDeltaList delta={intervention.objective_delta} label={`${INTERVENTION_LABELS[intervention.type]} objective delta`} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </section>
  );
}
