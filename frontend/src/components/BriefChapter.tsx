import { ArrowRight, ThermometerSun } from "lucide-react";

import { CrewCard, HeatBandStrip, JobCard, TemperatureBadge } from "./primitives";
import type { Scenario } from "../types";

interface BriefChapterProps {
  scenario: Scenario;
  onGenerate: () => void;
  fixtureError?: string | null;
}

const SPOTLIGHT_JOB_IDS = ["job-school-potholes", "job-bus-route", "job-blocked-inlet"] as const;

export function BriefChapter({ scenario, onGenerate, fixtureError = null }: BriefChapterProps) {
  const maximumHeat = scenario.heat_series.reduce<Scenario["heat_series"][number] | null>(
    (maximum, slot) => (maximum === null || slot.temperature_c > maximum.temperature_c ? slot : maximum),
    null,
  );
  const spotlightJobs = SPOTLIGHT_JOB_IDS.map((jobId) => scenario.jobs.find((job) => job.id === jobId));
  const missingSpotlight = SPOTLIGHT_JOB_IDS.filter((jobId, index) => spotlightJobs[index]?.id !== jobId);

  if (fixtureError !== null || maximumHeat === null || missingSpotlight.length > 0) {
    const message =
      fixtureError ??
      (maximumHeat === null
        ? "The saved scenario contains no heat series."
        : `The saved scenario is missing spotlight job IDs: ${missingSpotlight.join(", ")}.`);
    return (
      <section className="fixture-error" role="alert" aria-labelledby="fixture-error-heading">
        <p className="label-caps">Fixture error</p>
        <h1 id="fixture-error-heading">The brief cannot be shown.</h1>
        <p>{message}</p>
      </section>
    );
  }

  return (
    <section className="brief-chapter" aria-labelledby="brief-heading">
      <header className="brief-hero">
        <div className="brief-hero__copy">
          <p className="label-caps">Tomorrow&apos;s Brief · {scenario.date}</p>
          <h1 id="brief-heading">How much public service survives the heat?</h1>
          <p className="brief-hero__summary">
            The day starts with a constrained maintenance board and a synthetic heat policy waiting to change it.
          </p>
        </div>
        <div className="brief-hero__heat">
          <TemperatureBadge temperatureC={maximumHeat.temperature_c} band={maximumHeat.band} />
          <p className="brief-hero__heat-caption">
            <ThermometerSun size={18} aria-hidden="true" /> Maximum submitted temperature
          </p>
        </div>
      </header>

      <p className="brief-count">
        <strong>{scenario.crews.length} crews.</strong> <strong>{scenario.jobs.length} work orders.</strong>
      </p>

      <section className="brief-crews" aria-labelledby="crew-heading">
        <div className="section-heading-row">
          <div>
            <p className="label-caps">Resources on shift</p>
            <h2 id="crew-heading">Pre-formed crews</h2>
          </div>
          <span className="data-value section-heading-row__count">{scenario.crews.length} active</span>
        </div>
        <div className="crew-row">
          {scenario.crews.map((crew) => (
            <CrewCard crew={crew} key={crew.id} />
          ))}
        </div>
      </section>

      <section className="brief-heat" aria-labelledby="heat-heading">
        <div className="section-heading-row">
          <div>
            <p className="label-caps">Supplied 15-minute bands</p>
            <h2 id="heat-heading">Thermal field</h2>
          </div>
          <span className="data-value section-heading-row__count">{scenario.slot_minutes} min slots</span>
        </div>
        <HeatBandStrip heatSeries={scenario.heat_series} />
        <div className="heat-band-legend" aria-label="Heat band legend">
          {(["normal", "elevated", "severe", "extreme"] as const).map((band) => (
            <span className="heat-band-legend__item" key={band}>
              <i data-band={band} aria-hidden="true" /> {band}
            </span>
          ))}
        </div>
      </section>

      <div className="brief-lower-grid">
        <section aria-labelledby="spotlight-heading">
          <div className="section-heading-row">
            <div>
              <p className="label-caps">The decisions that matter later</p>
              <h2 id="spotlight-heading">Spotlight work orders</h2>
            </div>
            <span className="data-value section-heading-row__count">{spotlightJobs.length} selected</span>
          </div>
          <div className="job-grid">
            {spotlightJobs.map((job) => (
              <JobCard job={job!} key={job!.id} />
            ))}
          </div>
        </section>

        <aside className="brief-action-panel" aria-labelledby="action-heading">
          <p className="label-caps">Next chapter</p>
          <h2 id="action-heading">Make the policy constraint visible.</h2>
          <p>Generate the compliant plan and inspect what moves, what waits, and what stays served.</p>
          <button className="primary-action" type="button" onClick={onGenerate}>
            Generate policy-constrained plan <ArrowRight size={18} aria-hidden="true" />
          </button>
        </aside>
      </div>
    </section>
  );
}
