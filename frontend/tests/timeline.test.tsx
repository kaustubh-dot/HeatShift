/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { parseDemoBundle } from "../src/api/fallback";
import { Timeline } from "../src/components/Timeline";

afterEach(cleanup);

describe("complete-day timeline", () => {
  const bundle = parseDemoBundle(rawBundle);
  const scenario = bundle.scenario;
  const plan = bundle.base_solve.plans.policy_constrained;

  function renderTimeline(selectedJobId: string | null = null, onJobClick = vi.fn()) {
    return render(
      <Timeline
        crews={scenario.crews}
        jobs={scenario.jobs}
        segments={plan.timeline_segments}
        heatSeries={scenario.heat_series}
        dayEnd={scenario.day_end}
        selectedJobId={selectedJobId}
        onJobClick={onJobClick}
      />,
    );
  }

  it("renders every returned segment on a stable crew order and 40-slot grid", () => {
    renderTimeline();

    expect(screen.getByRole("grid", { name: "Crew schedule timeline" })).toBeVisible();
    expect(document.querySelectorAll('[data-segment="true"]')).toHaveLength(plan.timeline_segments.length);
    expect(document.querySelectorAll(".timeline-time-cell")).toHaveLength(40);
    expect(document.querySelectorAll(".timeline-heat-cell")).toHaveLength(40);
    expect(Array.from(document.querySelectorAll(".timeline-row")).map((row) => row.getAttribute("data-crew-id"))).toEqual([
      "crew-asphalt",
      "crew-drainage",
      "crew-general",
    ]);

    const schoolSegment = screen.getByRole("gridcell", { name: /Asphalt Crew: work on School-zone pothole cluster/ });
    expect(schoolSegment).toHaveStyle({ gridColumn: "2 / 8" });
    expect(screen.getByRole("gridcell", { name: /Asphalt Crew: travel state, 07:00 to 07:15/ })).toBeVisible();
  });

  it("uses native work controls with full labels and a selected detail summary", () => {
    const onJobClick = vi.fn();
    const view = renderTimeline(null, onJobClick);
    const schoolSegment = screen.getByRole("gridcell", { name: /job-school-potholes/ });

    expect(schoolSegment.tagName).toBe("BUTTON");
    schoolSegment.focus();
    fireEvent.keyDown(schoolSegment, { key: "Enter" });
    expect(onJobClick).toHaveBeenCalledWith("job-school-potholes");

    view.rerender(
      <Timeline
        crews={scenario.crews}
        jobs={scenario.jobs}
        segments={plan.timeline_segments}
        heatSeries={scenario.heat_series}
        dayEnd={scenario.day_end}
        selectedJobId="job-school-potholes"
        onJobClick={onJobClick}
      />,
    );
    expect(screen.getByRole("complementary", { name: "Selected timeline detail" })).toHaveTextContent(
      "School-zone pothole cluster",
    );
  });
});
