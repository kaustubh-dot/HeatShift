# TODO

This is the implementation ledger. Execute tasks in ID order using [docs/IMPLEMENTATION_MASTER_PLAN.md](docs/IMPLEMENTATION_MASTER_PLAN.md). Check a task only after its packet-specific acceptance command passes and `CHECKPOINT.md` records the evidence.

## Active task

- [ ] **B06** — Implement CP-SAT selection, route flow, occupancy, and global rolling constraints.

## Gate G1 — Inputs and patterns

- [x] **B00** — Create the Python 3.12 project and pin the verified runtime/test environment.
- [x] **B01** — Implement strict canonical Pydantic models.
- [x] **B02** — Implement tested time-grid, heat-remapping, and matrix helpers.
- [x] **B03** — Encode the locked deterministic scenario and policy fixtures.
- [x] **B04** — Implement cross-reference and semantic validation with stable error paths.
- [x] **B05** — Implement deterministic baseline and constrained execution-pattern generation.

## Gate G2 — Solver evidence

- [ ] **B06** — Implement CP-SAT selection, route flow, occupancy, and global rolling constraints.
- [ ] **B07** — Implement staged lexicographic objectives and honest proof capture.
- [ ] **B08** — Extract and reconcile timeline, route, metrics, and policy conflicts.
- [ ] **B09** — Orchestrate service-first and policy-constrained solves.
- [ ] **B10** — Derive explicit plan differences.
- [ ] **B11** — Implement forced-inclusion diagnosis.
- [ ] **B12** — Implement the bounded intervention catalogue.
- [ ] **B13** — Implement +2°C remapping and re-solve.
- [ ] **B14** — Perform at most one declared fixture-tuning pass and pass scenario gates.
- [ ] **B15** — Generate deterministic saved outputs and a hash manifest.

## Gate G3 — API and backend release

- [ ] **B16** — Implement the three FastAPI endpoints and canonical errors.
- [ ] **B17** — Pass the complete backend release gate and write release evidence.

## Gate G4 — Frontend

- [ ] **F00** — Create and pin the minimal React/TypeScript/Vite shell.
- [ ] **F01** — Implement contract types, genuine fallback loading, and reducer state.
- [ ] **F02** — Implement tokens, bundled fonts, shell, navigation, and TrustBar.
- [ ] **F03** — Implement Tomorrow's Brief.
- [ ] **F04** — Implement the complete-day accessible timeline.
- [ ] **F05** — Implement metrics and plan-difference evidence.
- [ ] **F06** — Implement the schematic map and synchronized selection.
- [ ] **F07** — Implement the short transformation and reduced-motion path.
- [ ] **F08** — Implement the diagnosis chapter.
- [ ] **F09** — Implement the +2°C heat-shock journey.
- [ ] **F10** — Integrate the live API, exact-match fallback, and failure states.
- [ ] **F11** — Pass accessibility and presentation-viewport checks.
- [ ] **F12** — Build and serve the frontend through FastAPI.

## Gate G5 — Release and submission

- [ ] **R00** — Pass a fresh clone/install/start rehearsal.
- [ ] **R01** — Pass live and disconnected demo rehearsals.
- [ ] **R02** — Capture release screenshots and the 3–5 minute demo.
- [ ] **R03** — Finalize README evidence, architecture, licenses, and limitations.
- [ ] **R04** — Audit and submit the Devpost entry.

## Explicitly not planned

- Authentication or multiple organizations
- Live municipal integrations or weather dependency
- Street-level routing, navigation, GPS, or employee tracking
- Real-time or multi-day dispatch
- Worker mobile application
- LLM/chat or natural-language policy ingestion
- Drag-and-drop schedule editing
- WebGL city models
- PDF report generation
- Medical, legal, or compliance certification
