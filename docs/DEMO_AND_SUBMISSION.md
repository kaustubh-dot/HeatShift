# Demo and Submission Plan

## 1. Judge thesis

> Heat alerts tell supervisors that conditions are dangerous. HeatShift answers the operational question that remains: what is the highest public service we can deliver under our approved policy, and what would it cost to add the work we had to defer?

## 2. Three-to-five-minute storyboard

| Time | Action | Evidence |
|---:|---|---|
| 0:00–0:20 | “41 C. Three crews. Twelve work orders.” | Specific problem and user |
| 0:20–0:45 | Reveal crews, jobs, heat profile, and synthetic-policy disclaimer | Real inputs and honest boundary |
| 0:45–1:15 | Build service-first plan | Genuine counterfactual; conflicts appear |
| 1:15–1:55 | Find highest compliant service | Work/recovery/route transformation |
| 1:55–2:25 | Compare service, conflicts, travel, and recovery | Measurable trade-off |
| 2:25–3:15 | Select deferred job and ask what it costs to include | Counterfactual differentiator |
| 3:15–3:50 | Apply +2 C heat shock and re-optimize | Dynamic decision support |
| 3:50–4:20 | Show stage statuses, architecture, and tests | Technical credibility |
| 4:20–4:40 | Restate impact and limitations | Responsible close |

A three-minute cut keeps the baseline, transformation, one diagnosis, and heat shock.

## 3. Demo rules

- Use only actual solver outputs.
- Keep the bundled scenario preloaded.
- Do not spend demo time editing tables.
- Click-drive transitions; do not depend on scroll timing.
- Keep solver proof/status visible but secondary to the plan.
- State “synthetic policy” once verbally and keep the disclaimer visible.
- Use saved genuine output fallback if live solving becomes unreliable.

## 4. Required evidence

- Input scenario and policy committed to the repository
- Reproducible service-first, compliant, diagnosis, and heat-shock outputs
- Solver stage statuses and bounds
- Tests for recovery, travel, counterfactuals, and language gates
- Architecture diagram
- Fresh-start instructions
- Safety and limitations section

## 5. Devpost content checklist

- Project title and one-line value proposition
- Sustainability & Climate Tech track
- Municipal planned-maintenance problem
- Working application link
- Public source repository
- Three-to-five-minute video
- Installation and test commands
- Technology list and architecture diagram
- Exact scenario metrics, not generalized claims
- “Built during Orion” scope statement
- Third-party licenses and attributions
- Synthetic-data/policy disclosure
- Known limitations and responsible-use language

## 6. Thirty-second pitch

Municipal crews still have to repair roads, clear drainage, and protect public infrastructure during extreme heat. Existing schedules optimize service; heat tools warn about risk. HeatShift connects the two. It calculates the highest-service crew plan that satisfies an employer's approved heat policy, inserts eligible recovery, and proves what it would cost to include every deferred job. When tomorrow becomes two degrees hotter, it rebuilds the plan in seconds—with every operational compromise visible.

## 7. Hard judge questions

### Is the policy medically validated?

No. The bundled policy is synthetic. HeatShift's contribution is executing an organization's approved policy consistently, not creating or certifying that policy.

### Is the deferred job actually impossible?

Omission does not imply impossibility. HeatShift forces the job into a new solve and reports whether an equivalent alternative exists, what must be displaced, or whether infeasibility was proven under clearly stated retained commitments.

### Is this real routing?

It is crew sequencing using a directed travel-time matrix. The map is deliberately labelled schematic and does not claim turn-by-turn navigation.

### How is this different from weather-aware scheduling?

The core differentiator is solver-derived counterfactual diagnosis: it quantifies the service, travel, overtime, or operational change required to include deferred work under mandatory policy constraints.
