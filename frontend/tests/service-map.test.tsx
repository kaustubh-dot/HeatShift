/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { parseDemoBundle } from "../src/api/fallback";
import { PlanChapter } from "../src/components/PlanChapter";
import { ServiceMap } from "../src/components/ServiceMap";

afterEach(cleanup);

describe("schematic service map", () => {
  const bundle = parseDemoBundle(rawBundle);
  const plan = bundle.base_solve.plans.policy_constrained;

  it("uses the submitted coordinates and preserves backend route order", () => {
    render(
      <ServiceMap
        crews={bundle.scenario.crews}
        jobs={bundle.scenario.jobs}
        locations={bundle.scenario.locations}
        plan={plan}
        selectedJobId={null}
        onJobClick={vi.fn()}
      />,
    );

    expect(screen.getByRole("img", { name: /Schematic service map/ })).toBeVisible();
    expect(document.querySelectorAll(".service-map__job-node")).toHaveLength(bundle.scenario.jobs.length);
    expect(document.querySelectorAll(".service-map__depot")).toHaveLength(1);
    expect(document.querySelectorAll(".service-map__route")).toHaveLength(plan.route_segments.length);
    expect(Array.from(document.querySelectorAll<SVGPolylineElement>(".service-map__route")).map((route) => [
      route.getAttribute("data-route-index"),
      route.getAttribute("data-crew-id"),
      route.getAttribute("data-from-location"),
      route.getAttribute("data-to-location"),
    ])).toEqual(
      plan.route_segments.map((segment, index) => [
        `${index}`,
        segment.crew_id,
        segment.from_location_id,
        segment.to_location_id,
      ]),
    );
  });

  it("sends the same job ID to map, timeline, and difference selection", () => {
    const onJobClick = vi.fn();
    const view = render(
      <PlanChapter
        scenario={bundle.scenario}
        serviceFirstPlan={bundle.base_solve.plans.service_first}
        policyPlan={plan}
        planDiff={bundle.base_solve.plan_diff}
        selectedJobId={null}
        onJobClick={onJobClick}
      />,
    );

    const mapNode = screen.getByRole("button", {
      name: /School-zone pothole cluster \(job-school-potholes\), assigned to crew-asphalt/,
    });
    fireEvent.keyDown(mapNode, { key: "Enter" });
    expect(onJobClick).toHaveBeenCalledWith("job-school-potholes");

    view.rerender(
      <PlanChapter
        scenario={bundle.scenario}
        serviceFirstPlan={bundle.base_solve.plans.service_first}
        policyPlan={plan}
        planDiff={bundle.base_solve.plan_diff}
        selectedJobId="job-school-potholes"
        onJobClick={onJobClick}
      />,
    );

    expect(screen.getByRole("button", { name: /School-zone pothole cluster \(job-school-potholes\), assigned/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: /School-zone pothole cluster \(job-school-potholes\): Unchanged/ })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByRole("complementary", { name: "Selected timeline detail" })).toHaveTextContent(
      "School-zone pothole cluster",
    );
  });
});
