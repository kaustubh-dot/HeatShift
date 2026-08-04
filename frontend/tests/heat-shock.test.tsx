/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { parseDemoBundle } from "../src/api/fallback";
import { WhyChapter } from "../src/components/WhyChapter";
import { appReducer, initialAppState } from "../src/state/appState";

afterEach(cleanup);

describe("heat shock journey", () => {
  const bundle = parseDemoBundle(rawBundle);
  const diagnosis = bundle.diagnoses[bundle.manifest.designated_diagnosis_job_id];
  const job = bundle.scenario.jobs.find((candidate) => candidate.id === diagnosis.job_id)!;
  const policyPlan = bundle.base_solve.plans.policy_constrained;

  const chapterProps = {
    job,
    diagnosis,
    jobs: bundle.scenario.jobs,
    policyPlan,
    heatShockResult: bundle.heat_shock_solve,
  };

  it("sends exactly a +2°C adjustment from the primary action", () => {
    const onApplyHeatShock = vi.fn();
    render(<WhyChapter {...chapterProps} onApplyHeatShock={onApplyHeatShock} />);

    fireEvent.click(screen.getByRole("button", { name: "Apply plus 2 degrees Celsius heat shock to re-optimize the plan" }));

    expect(onApplyHeatShock).toHaveBeenCalledTimes(1);
    expect(onApplyHeatShock).toHaveBeenCalledWith({ heat_adjustment_c: 2 });
  });

  it("keeps diagnosis evidence visible and disables only the duplicate shock action while loading", () => {
    render(<WhyChapter {...chapterProps} heatShockStatus="loading" />);

    expect(screen.getByText("proven infeasible under listed commitments")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("SOLVING…");
    expect(screen.getByRole("button", { name: "Apply plus 2 degrees Celsius heat shock to re-optimize the plan" })).toBeDisabled();
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Reset heat shock" })).not.toBeInTheDocument();
  });

  it("renders the returned heat-shock plan and puts its first decision before supporting metrics", () => {
    const view = render(<WhyChapter {...chapterProps} heatShockStatus="success" />);
    const result = view.container.querySelector(".heat-shock-result")!;
    const decision = result.querySelector(".heat-shock-decision")!;
    const metrics = result.querySelector(".metrics-bar")!;

    expect(screen.getByText("heat_shock_policy_constrained_plan")).toBeVisible();
    expect(screen.getByText("390")).toBeVisible();
    expect(result.querySelector(".plan-proof .solver-evidence__status")).toHaveTextContent("OPTIMAL");
    expect(result.querySelectorAll(".heat-shock-diff-list .plan-diff-card")).toHaveLength(bundle.heat_shock_solve.plan_diff.length);
    expect(decision.compareDocumentPosition(metrics) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(decision).toHaveTextContent(bundle.heat_shock_solve.plan_diff[0].job_id);
    expect(decision).toHaveTextContent("Moved time");
  });

  it("keeps a successful heat-shock response visible when every work order is unchanged", () => {
    const unchangedResult = {
      ...bundle.heat_shock_solve,
      plan_diff: bundle.heat_shock_solve.plan_diff.map((diff) => ({ ...diff, change: "unchanged" as const })),
    };
    render(<WhyChapter {...chapterProps} heatShockResult={unchangedResult} heatShockStatus="success" />);

    expect(screen.getByRole("heading", { name: "The heat shock returned no changed work-order decision." })).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("Every returned work order is unchanged");
    expect(screen.getByText("heat_shock_policy_constrained_plan")).toBeVisible();
  });

  it("resets the displayed shock without requesting another result", () => {
    const onApplyHeatShock = vi.fn();
    const onResetHeatShock = vi.fn();
    render(<WhyChapter {...chapterProps} heatShockStatus="success" onApplyHeatShock={onApplyHeatShock} onResetHeatShock={onResetHeatShock} />);

    fireEvent.click(screen.getByRole("button", { name: "Reset heat shock" }));

    expect(onResetHeatShock).toHaveBeenCalledTimes(1);
    expect(onApplyHeatShock).not.toHaveBeenCalled();
  });

  it("preserves the cached canonical response when the reducer resets the view", () => {
    const loaded = appReducer(initialAppState, { type: "demo_loaded", bundle, source: "saved" });
    const succeeded = appReducer(
      appReducer(loaded, { type: "request_started", request: "heatShock" }),
      { type: "request_succeeded", request: "heatShock", result: bundle.heat_shock_solve },
    );
    const reset = appReducer(succeeded, { type: "heatShock_reset" });

    expect(reset.request.heatShock).toEqual({ status: "idle", error: null });
    expect(reset.heatShockResult).toBe(bundle.heat_shock_solve);
    expect(reset.solveResult).toBe(bundle.base_solve);
  });
});
