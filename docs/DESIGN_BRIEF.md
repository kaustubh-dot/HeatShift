# Design Brief

This is a short handoff. A separate design specification should define the full visual system, component states, responsive behavior, and motion choreography.

## Experience goal

Create a premium, memorable **Climate Operations Command Center**—editorial and cinematic rather than a conventional SaaS or Streamlit dashboard. Visual polish must reveal genuine solver behavior.

## Structure

One click-driven application with three chapters:

1. **Tomorrow's Brief** — “41 C. Three crews. Twelve work orders. How much public service survives the heat?”
2. **Plan Transformation** — synchronized schematic map and crew timelines moving from service-first to policy-constrained.
3. **Why / What-if** — deferred-job counterfactual followed by the +2 C heat shock.

## Direction

- Near-black charcoal, warm ivory, amber-to-vermilion heat, cool cyan recovery
- Bold grotesk display typography, restrained interface sans, monospaced operational data
- Thin cartographic lines, subtle grain, thermal gradients, crisp schedule blocks
- Purposeful layout and state transitions driven by `plan_diff`
- Click-driven presentation; no scroll hijacking

## Required visuals

- Schematic service map, explicitly not street navigation
- Crew timelines with work, recovery, travel, idle, and unavailable states
- Heat bands and policy conflicts
- Baseline-to-plan movement animation
- Solver status and proof details
- Counterfactual cost/intervention panel
- Tactile +2 C heat-shock control

## Guardrails

- React + TypeScript; no Streamlit or generic admin template
- No WebGL/Three.js until the complete workflow works
- No custom cursor, long intro, hidden navigation, or decorative AI
- Laptop presentation is the primary viewport
- Reduced-motion mode preserves all information
- The UI must never fabricate, infer, or smooth over solver facts
