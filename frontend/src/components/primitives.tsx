import type { Crew, HeatSlot, Job } from "../types";

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

export function isHeatBand(value: string): value is HeatSlot["band"] {
  return HEAT_BANDS.includes(value as HeatSlot["band"]);
}
