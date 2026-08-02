import { Timeline } from "./Timeline";
import type { Plan, Scenario } from "../types";

interface PlanChapterProps {
  scenario: Scenario;
  plan: Plan;
  selectedJobId: string | null;
  onJobClick: (jobId: string) => void;
}

export function PlanChapter({ scenario, plan, selectedJobId, onJobClick }: PlanChapterProps) {
  return (
    <section className="plan-chapter" aria-labelledby="plan-heading">
      <header className="plan-chapter__intro">
        <p className="label-caps">Plan transformation · policy-constrained view</p>
        <h1 id="plan-heading">{plan.label}</h1>
        <p>Every returned timeline segment stays inspectable by crew, time, job, exertion, and policy rule.</p>
      </header>
      <Timeline
        crews={scenario.crews}
        jobs={scenario.jobs}
        segments={plan.timeline_segments}
        heatSeries={scenario.heat_series}
        dayEnd={scenario.day_end}
        selectedJobId={selectedJobId}
        onJobClick={onJobClick}
      />
    </section>
  );
}
