/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { parseDemoBundle } from "../src/api/fallback";
import { PlanChapter } from "../src/components/PlanChapter";

const bundle = parseDemoBundle(rawBundle);
const baseSolve = bundle.base_solve;

function setReducedMotion(matches: boolean) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn().mockReturnValue({
      addEventListener: vi.fn(),
      matches,
      media: "(prefers-reduced-motion: reduce)",
      removeEventListener: vi.fn(),
    }),
  });
}

function renderPlan() {
  return render(
    <PlanChapter
      scenario={bundle.scenario}
      serviceFirstPlan={baseSolve.plans.service_first}
      policyPlan={baseSolve.plans.policy_constrained}
      planDiff={baseSolve.plan_diff}
      selectedJobId={null}
      onJobClick={vi.fn()}
    />,
  );
}

beforeEach(() => {
  vi.useFakeTimers();
  setReducedMotion(false);
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("signature plan transformation", () => {
  it("moves from baseline through the timed phases and settles on the same final plan", () => {
    renderPlan();
    const chapter = screen.getByRole("region", { name: "Policy changes the board." });

    expect(chapter).toHaveAttribute("data-transform-phase", "baseline");
    expect(screen.getByRole("status")).toHaveTextContent("Service-first plan");
    expect(document.querySelectorAll(".service-map__route")).toHaveLength(baseSolve.plans.service_first.route_segments.length);
    expect(screen.getByRole("region", { name: "Solver proof for maximum_service_compliant_plan" })).toBeVisible();
    expect(screen.getByRole("button", { name: /Bus-route pavement failure \(job-bus-route\): Deferred/ })).toBeVisible();

    act(() => vi.advanceTimersByTime(0));
    expect(chapter).toHaveAttribute("data-transform-phase", "highlight");
    expect(screen.getByRole("status")).toHaveTextContent("Policy changes highlighted");

    act(() => vi.advanceTimersByTime(299));
    expect(chapter).toHaveAttribute("data-transform-phase", "highlight");

    act(() => vi.advanceTimersByTime(1));
    expect(chapter).toHaveAttribute("data-transform-phase", "transforming");
    expect(screen.getByRole("status")).toHaveTextContent("Policy-constrained plan settling");
    expect(document.querySelectorAll(".service-map__route")).toHaveLength(baseSolve.plans.policy_constrained.route_segments.length);

    act(() => vi.advanceTimersByTime(499));
    expect(chapter).toHaveAttribute("data-transform-phase", "transforming");

    act(() => vi.advanceTimersByTime(251));
    expect(chapter).toHaveAttribute("data-transform-phase", "settled");
    expect(screen.getByRole("status")).toHaveTextContent("Policy-constrained plan ready");
    expect(screen.getByRole("article", { name: "Critical jobs: 3 / 4 scheduled, delta -1" })).toBeVisible();
  });

  it("replays without changing canonical data", () => {
    renderPlan();
    const chapter = screen.getByRole("region", { name: "Policy changes the board." });
    act(() => vi.runAllTimers());
    expect(chapter).toHaveAttribute("data-transform-phase", "settled");

    fireEvent.click(screen.getByRole("button", { name: "Replay change" }));
    expect(chapter).toHaveAttribute("data-transform-phase", "highlight");
    act(() => vi.runAllTimers());

    expect(chapter).toHaveAttribute("data-transform-phase", "settled");
    expect(screen.getByRole("article", { name: "Critical jobs: 3 / 4 scheduled, delta -1" })).toBeVisible();
    expect(screen.getByRole("button", { name: /Bus-route pavement failure \(job-bus-route\): Deferred/ })).toBeVisible();
  });
});

describe("reduced-motion transformation", () => {
  it("swaps immediately and keeps replay usable", () => {
    setReducedMotion(true);
    renderPlan();

    const chapter = screen.getByRole("region", { name: "Policy changes the board." });
    expect(chapter).toHaveAttribute("data-transform-phase", "settled");
    expect(screen.getByRole("status")).toHaveTextContent("Policy-constrained plan ready");
    expect(screen.getByRole("article", { name: "Critical jobs: 3 / 4 scheduled, delta -1" })).toBeVisible();
    expect(vi.getTimerCount()).toBe(0);

    fireEvent.click(screen.getByRole("button", { name: "Replay change" }));
    expect(chapter).toHaveAttribute("data-transform-phase", "settled");
    expect(vi.getTimerCount()).toBe(0);
  });
});
