import { useEffect, useRef } from "react";

import type { DiagnosisResponse, Job } from "../types";
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

interface WhyChapterProps {
  job: Job | null;
  diagnosis: DiagnosisResponse | null;
  diagnosisRequestStatus?: RequestStatus;
  diagnosisRequestError?: string | null;
}

export function WhyChapter({ job, diagnosis, diagnosisRequestStatus = "idle", diagnosisRequestError = null }: WhyChapterProps) {
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
