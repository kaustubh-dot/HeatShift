/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { parseDemoBundle } from "../src/api/fallback";
import { PlanChapter } from "../src/components/PlanChapter";
import { PlanDiffBadge, PlanProof } from "../src/components/primitives";
import type { PlanChange } from "../src/types";

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("plan evidence chapter", () => {
  const bundle = parseDemoBundle(rawBundle);
  const baseSolve = bundle.base_solve;

  function renderPlan(selectedJobId: string | null = null, onJobClick = vi.fn()) {
    const view = render(
      <PlanChapter
        scenario={bundle.scenario}
        serviceFirstPlan={baseSolve.plans.service_first}
        policyPlan={baseSolve.plans.policy_constrained}
        planDiff={baseSolve.plan_diff}
        selectedJobId={selectedJobId}
        onJobClick={onJobClick}
      />,
    );
    act(() => vi.runAllTimers());
    return view;
  }

  it("renders supplied metrics, solver proof, and every base plan difference", () => {
    renderPlan();

    expect(screen.getByRole("region", { name: "Plan metrics comparison" })).toBeVisible();
    for (const metric of [
      "Critical jobs: 3 / 4 scheduled, delta -1",
      "Planned service: 368 value, delta -32",
      "Policy conflicts: 0 conflicts, delta -11",
      "Travel: 160 min, delta +78",
      "Overtime: 0 min, delta 0",
      "Active work: 390 min, delta +90",
      "Eligible recovery: 0 min, delta 0",
    ]) {
      expect(screen.getByRole("article", { name: metric })).toBeVisible();
    }

    const serviceProof = screen.getByRole("region", {
      name: "Solver proof for service_first_counterfactual",
    });
    expect(serviceProof.querySelector(".solver-evidence__status")).toHaveTextContent("FEASIBLE");
    expect(serviceProof).toHaveTextContent("Feasible incumbent; optimality was not proven.");
    expect(
      within(serviceProof).getByRole("listitem", {
        name: "critical_service: FEASIBLE, value 4, bound 13",
      }),
    ).toBeVisible();

    const policyProof = screen.getByRole("region", {
      name: "Solver proof for maximum_service_compliant_plan",
    });
    expect(policyProof.querySelector(".solver-evidence__status")).toHaveTextContent("OPTIMAL");
    expect(policyProof).toHaveTextContent("Maximum-service claim permitted by all required objective stages.");
    expect(
      within(policyProof).getByRole("listitem", {
        name: "critical_service: OPTIMAL, value 3, bound 3",
      }),
    ).toBeVisible();

    expect(document.querySelectorAll(".plan-diff-card")).toHaveLength(baseSolve.plan_diff.length);
    expect(new Set(Array.from(document.querySelectorAll(".plan-diff-card")).map((card) => card.getAttribute("data-change")))).toEqual(
      new Set(["unchanged", "moved_time", "served", "deferred"]),
    );

    const deferred = screen.getByRole("button", {
      name: /Bus-route pavement failure \(job-bus-route\): Deferred\./,
    });
    expect(deferred).toHaveAccessibleName(
      /Before crew-asphalt · 09:00–11:00\. After Not scheduled\. hs01-heavy-elevated\. Explanation POLICY_CAPACITY_CONFLICT\./,
    );
    expect(deferred).toHaveTextContent("hs01-heavy-elevated");
    expect(deferred).toHaveTextContent("POLICY_CAPACITY_CONFLICT");
  });

  it("uses one selected job ID for timeline and difference evidence", () => {
    const onJobClick = vi.fn();
    const view = renderPlan(null, onJobClick);

    fireEvent.click(screen.getByRole("gridcell", { name: /job-school-potholes/ }));
    expect(onJobClick).toHaveBeenCalledWith("job-school-potholes");

    view.rerender(
      <PlanChapter
        scenario={bundle.scenario}
        serviceFirstPlan={baseSolve.plans.service_first}
        policyPlan={baseSolve.plans.policy_constrained}
        planDiff={baseSolve.plan_diff}
        selectedJobId="job-school-potholes"
        onJobClick={onJobClick}
      />,
    );

    expect(
      screen.getByRole("button", { name: /School-zone pothole cluster \(job-school-potholes\): Unchanged/ }),
    ).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("complementary", { name: "Selected timeline detail" })).toHaveTextContent(
      "School-zone pothole cluster",
    );
  });
});

describe("fixture solver statuses and diff vocabulary", () => {
  const bundle = parseDemoBundle(rawBundle);

  it("covers every solver status and every change type present in saved evidence", () => {
    const fixtureStatuses = new Set([
      bundle.base_solve.plans.service_first.status,
      bundle.base_solve.plans.policy_constrained.status,
      bundle.heat_shock_solve.plans.policy_constrained.status,
      bundle.diagnoses["job-bus-route"].proof_status,
    ]);
    expect(fixtureStatuses).toEqual(new Set(["FEASIBLE", "OPTIMAL", "UNKNOWN", "INFEASIBLE"]));

    const shockPolicyPlan = bundle.heat_shock_solve.plans.policy_constrained;
    render(
      <PlanProof plan={shockPolicyPlan} />,
    );
    const unknownProof = screen.getByRole("region", {
      name: `Solver proof for ${shockPolicyPlan.label}`,
    });
    expect(unknownProof.querySelector(".solver-evidence__status")).toHaveTextContent("UNKNOWN");
    expect(unknownProof).toHaveTextContent("Maximum-service wording withheld until the required stages prove optimality.");

    const fixtureChanges = new Set(
      [...bundle.base_solve.plan_diff, ...bundle.heat_shock_solve.plan_diff].map((diff) => diff.change),
    );
    expect(fixtureChanges).toEqual(new Set(["unchanged", "moved_time", "served", "deferred", "recovery_added"]));

    const allChanges: PlanChange[] = [
      "unchanged",
      "moved_time",
      "moved_crew",
      "recovery_added",
      "served",
      "deferred",
    ];
    render(
      <div>
        {allChanges.map((change) => (
          <PlanDiffBadge change={change} key={change} />
        ))}
      </div>,
    );
    const labels: Record<PlanChange, string> = {
      unchanged: "Unchanged",
      moved_time: "Moved time",
      moved_crew: "Moved crew",
      recovery_added: "Recovery added",
      served: "Served",
      deferred: "Deferred",
    };
    for (const change of allChanges) {
      expect(document.querySelector(`.plan-diff-badge[data-change="${change}"]`)).toHaveTextContent(labels[change]);
    }
  });
});
