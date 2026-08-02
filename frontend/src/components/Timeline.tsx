import type { CSSProperties, KeyboardEvent } from "react";

import type { Crew, HeatSlot, Job, TimelineSegment } from "../types";

interface TimelineProps {
  crews: Crew[];
  jobs: Job[];
  segments: TimelineSegment[];
  heatSeries: HeatSlot[];
  dayEnd: string;
  selectedJobId: string | null;
  onJobClick: (jobId: string) => void;
}

const STATE_LABELS: Record<TimelineSegment["state"], string> = {
  work: "work",
  recovery: "recovery",
  travel: "travel",
  idle: "idle",
  unavailable: "unavailable",
};

function segmentName(segment: TimelineSegment, crew: Crew, job: Job | undefined): string {
  const subject = job === undefined ? `${segment.state} state` : `${segment.state} on ${job.name} (${job.id})`;
  const exertion = segment.exertion === null ? "" : `, ${segment.exertion} exertion`;
  const rules = segment.policy_rule_ids.length === 0 ? "" : `, policy rules ${segment.policy_rule_ids.join(", ")}`;
  return `${crew.name}: ${subject}, ${segment.start} to ${segment.end}${exertion}${rules}`;
}

function handleSegmentKeyDown(event: KeyboardEvent<HTMLButtonElement>, jobId: string, onJobClick: (jobId: string) => void) {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  onJobClick(jobId);
}

function SlotHeader({ heatSeries, slotCount }: { heatSeries: HeatSlot[]; slotCount: number }) {
  return (
    <>
      <div className="timeline-corner" aria-hidden="true">
        Crew / time
      </div>
      <div className="timeline-header-track" role="row" aria-label="Timeline time slots">
        {heatSeries.map((slot) => (
          <span
            className="timeline-time-cell"
            data-major={slot.slot % 4 === 0 ? "true" : "false"}
            data-slot={slot.slot}
            key={slot.slot}
            style={{ gridColumn: slot.slot + 1 }}
            title={slot.start}
          >
            {slot.slot % 4 === 0 ? slot.start : ""}
          </span>
        ))}
        {heatSeries.length < slotCount &&
          Array.from({ length: slotCount - heatSeries.length }, (_, index) => (
            <span className="timeline-time-cell" data-slot={heatSeries.length + index} key={heatSeries.length + index} />
          ))}
      </div>
      <div className="timeline-corner timeline-corner--heat" aria-hidden="true">
        Heat band
      </div>
      <div className="timeline-heat-track" aria-label="Supplied heat bands">
        {heatSeries.map((slot) => (
          <span
            className="timeline-heat-cell"
            data-band={slot.band}
            data-slot={slot.slot}
            key={slot.slot}
            style={{ gridColumn: slot.slot + 1 }}
            title={`${slot.start}: ${slot.temperature_c}°C, ${slot.band}`}
          />
        ))}
      </div>
    </>
  );
}

export function Timeline({ crews, jobs, segments, heatSeries, dayEnd, selectedJobId, onJobClick }: TimelineProps) {
  const slotCount = Math.max(heatSeries.length, ...segments.map((segment) => segment.end_slot), 1);
  const jobById = new Map(jobs.map((job) => [job.id, job]));
  const segmentByCrew = new Map<string, TimelineSegment[]>();
  for (const crew of crews) segmentByCrew.set(crew.id, []);
  for (const segment of segments) segmentByCrew.get(segment.crew_id)?.push(segment);
  const selectedSegment = selectedJobId === null ? undefined : segments.find((segment) => segment.job_id === selectedJobId);
  const selectedCrew = selectedSegment === undefined ? undefined : crews.find((crew) => crew.id === selectedSegment.crew_id);

  return (
    <section className="timeline-panel" aria-labelledby="timeline-heading">
      <div className="section-heading-row">
        <div>
          <p className="label-caps">Complete day · {slotCount} slots</p>
          <h2 id="timeline-heading">Crew schedule timeline</h2>
        </div>
        <span className="data-value section-heading-row__count">{heatSeries[0]?.start}–{dayEnd}</span>
      </div>

      <div
        className="timeline-grid"
        role="grid"
        aria-label="Crew schedule timeline"
        aria-rowcount={crews.length + 2}
        aria-colcount={slotCount + 1}
        style={{ "--slot-count": slotCount } as CSSProperties}
      >
        <SlotHeader heatSeries={heatSeries} slotCount={slotCount} />
        {crews.map((crew) => (
          <div className="timeline-row" role="row" data-crew-id={crew.id} key={crew.id} aria-label={`${crew.name} schedule`}>
            <div className="timeline-crew-label" role="rowheader">
              <strong>{crew.name}</strong>
              <span className="data-value">{crew.shift_start}–{crew.shift_end}</span>
            </div>
            <div className="timeline-track" role="presentation">
              {segmentByCrew.get(crew.id)?.map((segment) => {
                const job = segment.job_id === null ? undefined : jobById.get(segment.job_id);
                const selected = segment.job_id !== null && segment.job_id === selectedJobId;
                const dimmed = selectedJobId !== null && !selected;
                const segmentKey = `${crew.id}-${segment.start_slot}-${segment.end_slot}-${segment.state}-${segment.job_id ?? "state"}`;
                const commonProps = {
                  "data-end-slot": segment.end_slot,
                  "data-exertion": segment.exertion ?? undefined,
                  "data-segment": "true",
                  "data-start-slot": segment.start_slot,
                  "data-state": segment.state,
                  style: {
                    gridColumn: `${segment.start_slot + 1} / ${segment.end_slot + 1}`,
                  },
                };
                if (segment.state === "work" && segment.job_id !== null) {
                  return (
                    <button
                      {...commonProps}
                      aria-label={segmentName(segment, crew, job)}
                      aria-selected={selected}
                      className={`timeline-segment timeline-segment--button${selected ? " is-selected" : ""}${dimmed ? " is-dimmed" : ""}`}
                      data-job-id={segment.job_id}
                      key={segmentKey}
                      onClick={() => onJobClick(segment.job_id!)}
                      onKeyDown={(event) => handleSegmentKeyDown(event, segment.job_id!, onJobClick)}
                      role="gridcell"
                      tabIndex={0}
                      type="button"
                    >
                      <span className="timeline-segment__text">{job?.id ?? segment.job_id}</span>
                    </button>
                  );
                }
                return (
                  <div
                    {...commonProps}
                    aria-label={segmentName(segment, crew, job)}
                    className={`timeline-segment${dimmed ? " is-dimmed" : ""}`}
                    key={segmentKey}
                    role="gridcell"
                  >
                    <span className="timeline-segment__text">{STATE_LABELS[segment.state]}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <aside className="timeline-detail" aria-live="polite" aria-label="Selected timeline detail">
        {selectedSegment !== undefined && selectedCrew !== undefined ? (
          <>
            <p className="label-caps">Selected work order</p>
            <h3>{jobById.get(selectedSegment.job_id!)?.name ?? selectedSegment.job_id}</h3>
            <p className="data-value">
              {selectedCrew.name} · {selectedSegment.start}–{selectedSegment.end} · {selectedSegment.exertion ?? "non-work"}
            </p>
            <p className="timeline-detail__rules">
              {selectedSegment.policy_rule_ids.length === 0
                ? "No policy rule IDs attached to this segment."
                : `Policy rules: ${selectedSegment.policy_rule_ids.join(", ")}`}
            </p>
          </>
        ) : (
          <p>Select a work segment to inspect its crew, state, time, exertion, and policy rule IDs.</p>
        )}
      </aside>
    </section>
  );
}
