/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { loadFallbackDemo, parseDemoBundle } from "../src/api/fallback";
import {
  appReducer,
  initialAppState,
  selectPlanDiff,
  selectPolicyPlan,
  type AppAction,
} from "../src/state/appState";
import type { DemoBundle } from "../src/types";

function FixtureEvidence({ bundle }: { bundle: DemoBundle }) {
  return (
    <output role="status" aria-label="saved fixture evidence">
      {bundle.scenario.id} · {bundle.policy.id} · {bundle.base_solve.plans.policy_constrained.status}
    </output>
  );
}

describe("saved solver fallback", () => {
  it("parses and renders IDs and solver status from the genuine B15 bundle", () => {
    const bundle = parseDemoBundle(rawBundle);

    render(<FixtureEvidence bundle={bundle} />);

    expect(screen.getByRole("status", { name: "saved fixture evidence" })).toHaveTextContent(
      "demo-city-day-01 · demo-city-hs-01 · OPTIMAL",
    );
    expect(bundle.diagnoses["job-bus-route"].classification).toBe("proven_infeasible");
  });

  it("loads the same bundle through the fallback fetch boundary", async () => {
    const response = new Response(JSON.stringify(rawBundle), {
      status: 200,
      headers: { "content-type": "application/json" },
    });

    const bundle = await loadFallbackDemo({ fetcher: async () => response });

    expect(bundle.fixture_version).toBe("demo-v1");
    expect(bundle.heat_shock_solve.scenario.heat_adjustment_c).toBe(2);
  });

  it("fails visibly when a required saved result is malformed", () => {
    const malformed = { ...rawBundle, base_solve: null };

    expect(() => parseDemoBundle(malformed)).toThrow("bundle.base_solve");
  });
});

describe("reducer-owned application state", () => {
  const bundle = parseDemoBundle(rawBundle);
  const actions: AppAction[] = [
    { type: "demo_loaded", bundle, source: "saved" },
    { type: "select_job", jobId: "job-bus-route" },
    { type: "navigate", chapter: "plan" },
    { type: "request_started", request: "diagnosis" },
    { type: "request_succeeded", request: "diagnosis", result: bundle.diagnoses["job-bus-route"] },
  ];

  it("applies the same action sequence deterministically", () => {
    const first = actions.reduce(appReducer, initialAppState);
    const second = actions.reduce(appReducer, initialAppState);

    expect(first).toEqual(second);
    expect(first.dataSource).toBe("saved");
    expect(first.chapter).toBe("plan");
    expect(first.selectedJobId).toBe("job-bus-route");
    expect(first.request.diagnosis.status).toBe("success");
  });

  it("derives plans, metrics, and differences without duplicating them in state", () => {
    const state = appReducer(initialAppState, { type: "demo_loaded", bundle, source: "saved" });

    expect(selectPolicyPlan(state)).toBe(state.solveResult?.plans.policy_constrained);
    expect(selectPolicyPlan(state)?.metrics).toBe(state.solveResult?.plans.policy_constrained.metrics);
    expect(selectPlanDiff(state)).toBe(state.solveResult?.plan_diff);
    expect("metrics" in state).toBe(false);
    expect("policyPlan" in state).toBe(false);
  });
});
