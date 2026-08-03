import type { Crew, HeatSlot, Job, Metrics, Plan, PlanChange, PlanDiff } from "../types";

const HEAT_BANDS = ["normal", "elevated", "severe", "extreme"] as const;

export function TemperatureBadge({ temperatureC, band }: { temperatureC: number; band: HeatSlot["band"] }) {
  return (
    <div className="temperature-badge" data-band={band} aria-label={`Temperature: ${temperatureC} degrees Celsius, ${band} heat band`}>
      <span className="temperature-badge__value data-value">{temperatureC}°C</span>
      <span className="temperature-badge__band label-caps">{band}</span>
    </div>
  );
}

function heatProgression(heatSeries: HeatSlot[]): string {
  const transitions: string[] = [];
  for (const slot of heatSeries) {
    const previous = heatSeries[slot.slot - 1];
    if (previous?.band === slot.band) continue;
    transitions.push(`${slot.band} from ${slot.start}`);
  }
  return transitions.join(", ");
}

export function HeatBandStrip({ heatSeries }: { heatSeries: HeatSlot[] }) {
  return (
    <div
      className="heat-band-strip"
      role="img"
      aria-label={`Heat progression: ${heatProgression(heatSeries)}`}
    >
      {heatSeries.map((slot) => (
        <span
          className="heat-band-strip__slot"
          data-band={slot.band}
          data-slot={slot.slot}
          key={slot.slot}
          style={{ backgroundColor: `var(--heat-${slot.band})` }}
        />
      ))}
    </div>
  );
}

export function CrewCard({ crew }: { crew: Crew }) {
  return (
    <article className="crew-card" data-crew-id={crew.id} aria-label={`${crew.name}, ${crew.shift_start} to ${crew.shift_end}`}>
      <h3>{crew.name}</h3>
      <p className="crew-card__shift data-value">
        {crew.shift_start}–{crew.shift_end}
      </p>
      <div className="crew-card__tags" aria-label="Crew capabilities">
        {crew.capabilities.slice(0, 2).map((capability) => (
          <span className="data-tag" key={capability}>
            {capability}
          </span>
        ))}
      </div>
    </article>
  );
}

export function JobCard({ job }: { job: Job }) {
  return (
    <article className="job-card" data-job-id={job.id} aria-label={`${job.name}, ${job.priority} priority, ${job.exertion} exertion`}>
      <div className="job-card__header">
        <span className={`priority-badge priority-badge--${job.priority}`}>{job.priority}</span>
        <span className="job-card__exertion">{job.exertion}</span>
      </div>
      <h3>{job.name}</h3>
      <p className="job-card__meta data-value">
        {job.window_start}–{job.window_end} · {job.service_value} service value
      </p>
      <p className="job-card__id">{job.id}</p>
    </article>
  );
}

interface MetricDefinition {
  key: keyof Metrics;
  label: string;
  unit: string;
}

const METRIC_DEFINITIONS: MetricDefinition[] = [
  { key: "critical_jobs_scheduled", label: "Critical jobs", unit: "scheduled" },
  { key: "planned_service_value", label: "Planned service", unit: "value" },
  { key: "mandatory_policy_conflicts", label: "Policy conflicts", unit: "conflicts" },
  { key: "travel_minutes", label: "Travel", unit: "min" },
  { key: "overtime_minutes", label: "Overtime", unit: "min" },
  { key: "active_work_minutes", label: "Active work", unit: "min" },
  { key: "eligible_recovery_minutes", label: "Eligible recovery", unit: "min" },
];

function signed(value: number): string {
  return value > 0 ? `+${value}` : `${value}`;
}

export function MetricTile({
  label,
  value,
  unit,
  delta,
}: {
  label: string;
  value: string;
  unit: string;
  delta: number | null;
}) {
  return (
    <article className="metric-tile" aria-label={`${label}: ${value} ${unit}${delta === null ? "" : `, delta ${signed(delta)}`}`}>
      <p className="label-caps">{label}</p>
      <p className="metric-tile__value metric-value">{value}</p>
      <p className="metric-tile__unit">{unit}</p>
      {delta !== null && <p className="metric-tile__delta metric-value">Δ {signed(delta)}</p>}
    </article>
  );
}

export function MetricsBar({ current, baseline }: { current: Metrics; baseline: Metrics }) {
  return (
    <section className="metrics-bar" aria-label="Plan metrics comparison" role="region">
      {METRIC_DEFINITIONS.map(({ key, label, unit }) => {
        const value = key === "critical_jobs_scheduled" ? `${current[key]} / ${current.critical_jobs_total}` : `${current[key]}`;
        const delta = current[key] - baseline[key];
        return <MetricTile delta={delta} key={key} label={label} unit={unit} value={value} />;
      })}
    </section>
  );
}

const DIFF_PRESENTATION: Record<PlanChange, { icon: string; label: string }> = {
  unchanged: { icon: "—", label: "Unchanged" },
  moved_time: { icon: "↔", label: "Moved time" },
  moved_crew: { icon: "⇄", label: "Moved crew" },
  recovery_added: { icon: "+", label: "Recovery added" },
  served: { icon: "✓", label: "Served" },
  deferred: { icon: "✕", label: "Deferred" },
};

export function PlanDiffBadge({ change }: { change: PlanChange }) {
  const presentation = DIFF_PRESENTATION[change];
  return (
    <span className="plan-diff-badge" data-change={change}>
      <span aria-hidden="true">{presentation.icon}</span> {presentation.label}
    </span>
  );
}

function stateSummary(state: PlanDiff["before"]): string {
  if (state === null) return "Not scheduled";
  return `${state.crew_id ?? "Unassigned"} · ${state.start ?? "—"}–${state.end ?? "—"}`;
}

export function PlanDiffCard({
  diff,
  jobName,
  isSelected,
  onClick,
}: {
  diff: PlanDiff;
  jobName: string;
  isSelected: boolean;
  onClick: () => void;
}) {
  const presentation = DIFF_PRESENTATION[diff.change];
  const rules = diff.binding_rule_ids.length === 0 ? "No binding rule IDs" : diff.binding_rule_ids.join(", ");
  return (
    <button
      className={`plan-diff-card${isSelected ? " is-selected" : ""}`}
      data-change={diff.change}
      data-job-id={diff.job_id}
      aria-expanded={isSelected}
      aria-label={`${jobName} (${diff.job_id}): ${presentation.label}. Before ${stateSummary(diff.before)}. After ${stateSummary(diff.after)}. ${rules}. Explanation ${diff.explanation_code}.`}
      onClick={onClick}
      type="button"
    >
      <span className="plan-diff-card__title">
        <strong>{jobName}</strong>
        <span className="plan-diff-card__id">{diff.job_id}</span>
      </span>
      <PlanDiffBadge change={diff.change} />
      <span className="plan-diff-card__states">
        <span>
          <small>Before</small>
          {stateSummary(diff.before)}
        </span>
        <span aria-hidden="true">→</span>
        <span>
          <small>After</small>
          {stateSummary(diff.after)}
        </span>
      </span>
      <span className="plan-diff-card__evidence">
        <span>{rules}</span>
        <code>{diff.explanation_code}</code>
      </span>
    </button>
  );
}

function stageNumber(value: number | null): string {
  return value === null ? "—" : `${value}`;
}

export function PlanProof({ plan }: { plan: Plan }) {
  return (
    <section className="plan-proof" aria-label={`Solver proof for ${plan.label}`}>
      <header className="plan-proof__header">
        <div>
          <p className="label-caps">Solver result</p>
          <h2>{plan.label}</h2>
        </div>
        <span className="solver-evidence__status" data-status={plan.status}>
          {plan.status}
        </span>
      </header>
      <p className="plan-proof__claim">
        {plan.maximum_claim_allowed
          ? "Maximum-service claim permitted by all required objective stages."
          : plan.status === "FEASIBLE"
            ? "Feasible incumbent; optimality was not proven."
            : "Maximum-service wording withheld until the required stages prove optimality."}
      </p>
      <ol className="stage-list" aria-label="Solver objective stages">
        {plan.stages.map((stage) => (
          <li key={stage.name} aria-label={`${stage.name}: ${stage.status}, value ${stageNumber(stage.objective_value)}, bound ${stageNumber(stage.best_bound)}`}>
            <span>{stage.name}</span>
            <strong>{stage.status}</strong>
            <span className="data-value">
              {stageNumber(stage.objective_value)} / {stageNumber(stage.best_bound)}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function isHeatBand(value: string): value is HeatSlot["band"] {
  return HEAT_BANDS.includes(value as HeatSlot["band"]);
}
