import { Timeline } from "./Timeline";
import { ServiceMap } from "./ServiceMap";
import { MetricsBar, PlanDiffCard, PlanProof } from "./primitives";
import { usePlanTransformation } from "../hooks/usePlanTransformation";
import type { Plan, PlanDiff, Scenario } from "../types";

interface PlanChapterProps {
  scenario: Scenario;
  serviceFirstPlan: Plan;
  policyPlan: Plan;
  planDiff: PlanDiff[];
  selectedJobId: string | null;
  onJobClick: (jobId: string) => void;
}

export function PlanChapter({ scenario, serviceFirstPlan, policyPlan, planDiff, selectedJobId, onJobClick }: PlanChapterProps) {
  const jobNames = new Map(scenario.jobs.map((job) => [job.id, job.name]));
  const { phase, replay } = usePlanTransformation();
  const activePlan = phase === "baseline" || phase === "highlight" ? serviceFirstPlan : policyPlan;
  const changedJobIds = new Set(planDiff.filter((diff) => diff.change !== "unchanged").map((diff) => diff.job_id));
  const phaseLabel =
    phase === "baseline"
      ? "Service-first plan"
      : phase === "highlight"
        ? "Policy changes highlighted"
        : phase === "transforming"
          ? "Policy-constrained plan settling"
          : "Policy-constrained plan ready";
  return (
    <section className="plan-chapter" aria-labelledby="plan-heading" data-transform-phase={phase}>
      <header className="plan-chapter__intro">
        <p className="label-caps">Plan transformation · policy-constrained view</p>
        <h1 id="plan-heading">Policy changes the board.</h1>
        <p>Every returned metric and plan difference below comes directly from the saved solver response.</p>
      </header>
      <div className="transformation-controls" aria-label="Plan transformation controls">
        <p className="transformation-controls__status" role="status" aria-live="polite">
          {phaseLabel}
        </p>
        <button className="secondary-button" type="button" onClick={replay}>
          Replay change
        </button>
        <p className="sr-only">The final policy-constrained metrics, solver proof, and plan differences are available while the visual transition runs.</p>
      </div>
      <div className="plan-proof-grid">
        <PlanProof plan={serviceFirstPlan} />
        <PlanProof plan={policyPlan} />
      </div>
      <MetricsBar current={activePlan.metrics} baseline={serviceFirstPlan.metrics} />
      <ServiceMap
        crews={scenario.crews}
        jobs={scenario.jobs}
        locations={scenario.locations}
        plan={activePlan}
        selectedJobId={selectedJobId}
        onJobClick={onJobClick}
        highlightedJobIds={phase === "highlight" ? changedJobIds : new Set()}
      />
      <Timeline
        crews={scenario.crews}
        jobs={scenario.jobs}
        segments={activePlan.timeline_segments}
        heatSeries={scenario.heat_series}
        dayEnd={scenario.day_end}
        selectedJobId={selectedJobId}
        onJobClick={onJobClick}
        highlightedJobIds={phase === "highlight" ? changedJobIds : new Set()}
      />
      <section className="plan-diff-section" aria-labelledby="plan-diff-heading">
        <div className="section-heading-row">
          <div>
            <p className="label-caps">Evidence-backed change list</p>
            <h2 id="plan-diff-heading">What the policy changed</h2>
          </div>
          <span className="data-value section-heading-row__count">{planDiff.length} work-order records</span>
        </div>
        <div className="plan-diff-list">
          {planDiff.map((diff) => (
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
  );
}
