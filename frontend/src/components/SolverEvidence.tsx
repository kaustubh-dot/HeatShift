import type { Plan, SolverStatus } from "../types";
import type { SavedManifest } from "../types";
import type { DataSource } from "../state/appState";

interface SolverEvidenceProps {
  plan: Plan | null;
  dataSource: DataSource;
  savedManifest?: SavedManifest | null;
}

function claimFor(plan: Plan | null): string {
  if (plan === null) return "Solver evidence will appear after the demo data loads.";
  switch (plan.status) {
    case "OPTIMAL":
      return plan.maximum_claim_allowed
        ? "Maximum-service claim permitted by the required proof stages."
        : "Optimal stages recorded; maximum-service wording is withheld.";
    case "FEASIBLE":
      return "Feasible incumbent returned; optimality was not proven.";
    case "INFEASIBLE":
      return "No feasible plan was proven under the retained commitments.";
    case "UNKNOWN":
      return "No conclusion was proven within the configured time limit.";
    case "MODEL_INVALID":
      return "The solver model was invalid; no operational claim is available.";
  }
}

export function SolverEvidence({ plan, dataSource, savedManifest = null }: SolverEvidenceProps) {
  const status: SolverStatus | "pending" = plan?.status ?? "pending";
  const sourceLabel = dataSource === "saved" ? "Saved solver run" : "Solver evidence";

  return (
    <div className="solver-evidence" role="status" aria-label={`${sourceLabel} status`}>
      <div className="solver-evidence__meta">
        <span className="solver-evidence__label">{sourceLabel}</span>
        <span className="solver-evidence__status" data-status={status}>
          {status === "pending" ? "WAITING" : status}
        </span>
      </div>
      <p className="solver-evidence__claim">{claimFor(plan)}</p>
      {dataSource === "saved" && (
        <p className="solver-evidence__saved-disclosure">
          SAVED SOLVER RUN · Live API unavailable · Results generated from the locked demo scenario
          {savedManifest === null ? "" : ` · ${savedManifest.fixture_version} · generated ${savedManifest.generated_at}`}
        </p>
      )}
      {plan !== null && (
        <ul className="solver-evidence__stages" aria-label="solver stages">
          {plan.stages.map((stage) => (
            <li className="solver-evidence__stage" key={stage.name}>
              <strong>{stage.name}</strong> {stage.status}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
