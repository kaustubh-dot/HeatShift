import { Timeline } from "./Timeline";
import { MetricsBar, PlanDiffCard, PlanProof } from "./primitives";
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
  return (
    <section className="plan-chapter" aria-labelledby="plan-heading">
      <header className="plan-chapter__intro">
        <p className="label-caps">Plan transformation · policy-constrained view</p>
        <h1 id="plan-heading">Policy changes the board.</h1>
        <p>Every returned metric and plan difference below comes directly from the saved solver response.</p>
      </header>
      <div className="plan-proof-grid">
        <PlanProof plan={serviceFirstPlan} />
        <PlanProof plan={policyPlan} />
      </div>
      <MetricsBar current={policyPlan.metrics} baseline={serviceFirstPlan.metrics} />
      <Timeline
        crews={scenario.crews}
        jobs={scenario.jobs}
        segments={policyPlan.timeline_segments}
        heatSeries={scenario.heat_series}
        dayEnd={scenario.day_end}
        selectedJobId={selectedJobId}
        onJobClick={onJobClick}
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
