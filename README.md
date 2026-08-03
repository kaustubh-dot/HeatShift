# HeatShift

HeatShift is a policy-constrained service optimizer for municipal planned-maintenance supervisors. It computes the highest service achievable under an employer-defined heat policy, then uses counterfactual re-optimization to show the operational cost of including each deferred work order.

## Locked direction

- **Hackathon track:** Sustainability & Climate Tech
- **Primary user:** Municipal planned-maintenance supervisor
- **Planning scope:** One day, three pre-formed crews, approximately twelve work orders
- **Optimization core:** OR-Tools CP-SAT for crew, equipment, travel, work, and recovery scheduling
- **Differentiator:** Counterfactual service diagnosis under mandatory climate-safety constraints
- **Safety boundary:** HeatShift executes an employer-defined policy. It does not create, certify, or medically validate one.
- **Experience:** A click-driven React application with three chapters: Tomorrow's Brief, Plan Transformation, and Why / What-if

The topic is frozen unless the headless solver spike fails to produce a valid, nontrivial baseline, compliant plan, deferred-job counterfactual, and heat-shock re-plan.

## Documentation

| Document | Purpose |
|---|---|
| [PRD](docs/PRD.md) | Product goals, users, requirements, and acceptance criteria |
| [Architecture](docs/ARCHITECTURE.md) | System boundaries, components, runtime, and deployment |
| [Solver specification](docs/SOLVER_SPEC.md) | Domain model, valid execution patterns, routing, objectives, and diagnostics |
| [Data and API contracts](docs/DATA_AND_API_CONTRACTS.md) | Canonical schemas and HTTP endpoints |
| [Demo scenario](docs/DEMO_SCENARIO.md) | Evidence-informed synthetic crews, work orders, policy, and anti-cherry-picking rules |
| [Test plan](docs/TEST_PLAN.md) | Solver invariants, API, UI, performance, and release gates |
| [Safety and limitations](docs/SAFETY_AND_LIMITATIONS.md) | Responsible-use language and prohibited claims |
| [Demo and submission](docs/DEMO_AND_SUBMISSION.md) | Judge narrative, demo sequence, and submission checklist |
| [Design specification](docs/DESIGN.md) | Complete visual system: tokens, components, choreography, accessibility |
| [Frontend plan](docs/FRONTEND_PLAN.md) | Implementation blueprint: types, architecture, component specs, timeline |
| [Implementation master plan](docs/IMPLEMENTATION_MASTER_PLAN.md) | Frozen task order, gates, agent protocol, and handoff rules |
| [Backend implementation plan](docs/BACKEND_IMPLEMENTATION_PLAN.md) | File-by-file solver, evidence, API, and verification packets |
| [Release implementation plan](docs/RELEASE_IMPLEMENTATION_PLAN.md) | Fresh-start rehearsal, demo capture, evidence audit, and submission packets |
| [Design brief](docs/DESIGN_BRIEF.md) | Short handoff for the dedicated design specification |
| [Roadmap](ROADMAP.md) | Delivery phases and exit gates |
| [TODO](TODO.md) | Prioritized implementation queue |
| [Checkpoint](CHECKPOINT.md) | Current state, decisions, evidence, and restart instructions |

## Launch-critical user journey

1. Load the bundled Demo City scenario.
2. Inspect the service-first counterfactual and its policy conflicts.
3. Generate the policy-constrained plan.
4. Compare service, travel, recovery, and policy outcomes.
5. Select a deferred job and run a forced-inclusion counterfactual.
6. Apply a synthetic +2 C heat shock and re-optimize.

No authentication, LLM, live GPS, street-level routing, multi-day scheduling, worker mobile app, or compliance certification is in launch scope.

## Run the production-shaped app locally

Build the frontend into the FastAPI static directory, then start one server for the API and SPA:

```bash
cd frontend
npm ci
npm run test:run
npm run build
cd ..
.venv/bin/python -m uvicorn backend.heatshift.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The same process serves `/api/*`, direct app routes, the genuine fallback JSON, and bundled fonts. Use `?fallback=true` for the explicitly disclosed saved-results presentation mode.
