import type { KeyboardEvent } from "react";

import type { Crew, Job, Location, Plan } from "../types";

const VIEWBOX = "0 0 800 600";
const CREW_ROUTE_COLORS: Record<string, string> = {
  "crew-asphalt": "var(--crew-asphalt)",
  "crew-drainage": "var(--crew-drainage)",
  "crew-general": "var(--crew-general)",
};

interface ServiceMapProps {
  crews: Crew[];
  jobs: Job[];
  locations: Location[];
  plan: Plan;
  selectedJobId: string | null;
  onJobClick: (jobId: string) => void;
}

function routeColor(crewId: string): string {
  return CREW_ROUTE_COLORS[crewId] ?? "var(--text-tertiary)";
}

function handleNodeKeyDown(event: KeyboardEvent<SVGGElement>, jobId: string, onJobClick: (jobId: string) => void) {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  onJobClick(jobId);
}

function shortJobLabel(jobId: string): string {
  return jobId.replace(/^job-/, "");
}

export function ServiceMap({ crews, jobs, locations, plan, selectedJobId, onJobClick }: ServiceMapProps) {
  const locationById = new Map(locations.map((location) => [location.id, location]));
  const resultByJobId = new Map(plan.jobs.map((job) => [job.job_id, job]));
  const depotIds = new Set(crews.flatMap((crew) => [crew.start_depot_id, crew.end_depot_id]));

  return (
    <section className="service-map-panel" aria-labelledby="service-map-heading">
      <div className="section-heading-row">
        <div>
          <p className="label-caps">Submitted schematic coordinates</p>
          <h2 id="service-map-heading">Schematic service map</h2>
        </div>
        <span className="data-value section-heading-row__count">{plan.route_segments.length} route segments</span>
      </div>

      <div className="service-map-frame">
        <svg
          className="service-map"
          viewBox={VIEWBOX}
          role="img"
          aria-labelledby="service-map-heading service-map-description"
          preserveAspectRatio="xMidYMid meet"
        >
          <desc id="service-map-description">
            Submitted schematic locations with {plan.route_segments.length} backend-ordered route segments. Focus a job node to select the same work order in the timeline and evidence list.
          </desc>
          <rect className="service-map__background" x="0" y="0" width="800" height="600" aria-hidden="true" />

          <g className="service-map__routes" aria-hidden="true">
            {plan.route_segments.map((segment, index) => (
              <polyline
                className="service-map__route"
                data-crew-id={segment.crew_id}
                data-from-location={segment.from_location_id}
                data-route-index={index}
                data-to-location={segment.to_location_id}
                fill="none"
                key={`${segment.crew_id}-${index}-${segment.from_location_id}-${segment.to_location_id}`}
                points={`${segment.from_coordinates[0]},${segment.from_coordinates[1]} ${segment.to_coordinates[0]},${segment.to_coordinates[1]}`}
                stroke={routeColor(segment.crew_id)}
              />
            ))}
          </g>

          <g className="service-map__depots" aria-hidden="true">
            {locations
              .filter((location) => depotIds.has(location.id))
              .map((location) => (
                <g data-depot-id={location.id} key={location.id}>
                  <rect
                    className="service-map__depot"
                    height="12"
                    width="12"
                    x={location.coordinates[0] - 6}
                    y={location.coordinates[1] - 6}
                  />
                  <text className="service-map__depot-label" x={location.coordinates[0] + 14} y={location.coordinates[1] + 4}>
                    {location.id}
                  </text>
                </g>
              ))}
          </g>

          <g className="service-map__jobs">
            {jobs.map((job) => {
              const location = locationById.get(job.location_id);
              if (location === undefined) return null;
              const result = resultByJobId.get(job.id);
              const selected = selectedJobId === job.id;
              const assignment = result?.crew_id === null || result === undefined ? "unassigned" : `assigned to ${result.crew_id}`;
              return (
                <g
                  aria-label={`${job.name} (${job.id}), ${assignment}, location ${job.location_id}${selected ? ", selected" : ""}`}
                  aria-pressed={selected}
                  className={`service-map__job-node${selected ? " is-selected" : ""}`}
                  data-job-id={job.id}
                  data-selected={selected ? "true" : "false"}
                  key={job.id}
                  onClick={() => onJobClick(job.id)}
                  onKeyDown={(event) => handleNodeKeyDown(event, job.id, onJobClick)}
                  role="button"
                  tabIndex={0}
                  transform={`translate(${location.coordinates[0]} ${location.coordinates[1]})`}
                >
                  <title>{job.name}</title>
                  <circle className="service-map__selection-ring" r="14" />
                  <circle className="service-map__job" r="8" />
                  <text className="service-map__job-label" x="14" y="4">
                    {shortJobLabel(job.id)}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>
      <p className="service-map__caption">Route color identifies crew only. The complete timeline and change list below remain the text alternative for every returned fact.</p>
    </section>
  );
}
