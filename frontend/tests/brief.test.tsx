/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { BriefChapter } from "../src/components/BriefChapter";
import { parseDemoBundle } from "../src/api/fallback";

afterEach(cleanup);

describe("Tomorrow's Brief", () => {
  const bundle = parseDemoBundle(rawBundle);

  it("renders scenario-derived heat, counts, crews, slots, and fixed spotlight jobs", () => {
    render(<BriefChapter scenario={bundle.scenario} onGenerate={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "How much public service survives the heat?" })).toBeVisible();
    expect(screen.getByLabelText("Temperature: 41 degrees Celsius, severe heat band")).toBeVisible();
    expect(screen.getByText("3 crews.")).toBeVisible();
    expect(screen.getByText("12 work orders.")).toBeVisible();
    expect(screen.getByRole("img", { name: /Heat progression:/ })).toBeVisible();
    expect(document.querySelectorAll(".heat-band-strip__slot")).toHaveLength(40);
    expect(document.querySelectorAll(".crew-card")).toHaveLength(3);
    expect(screen.getByText("School-zone pothole cluster")).toBeVisible();
    expect(screen.getByText("Bus-route pavement failure")).toBeVisible();
    expect(screen.getByText("Blocked storm inlet")).toBeVisible();
  });

  it("advances with one primary action and fails explicitly for a missing spotlight ID", () => {
    const onGenerate = vi.fn();
    render(<BriefChapter scenario={bundle.scenario} onGenerate={onGenerate} />);

    fireEvent.click(screen.getByRole("button", { name: /Generate policy-constrained plan/ }));
    expect(onGenerate).toHaveBeenCalledOnce();

    cleanup();
    const brokenScenario = {
      ...bundle.scenario,
      jobs: bundle.scenario.jobs.filter((job) => job.id !== "job-bus-route"),
    };
    render(<BriefChapter scenario={brokenScenario} onGenerate={vi.fn()} />);

    expect(screen.getByRole("alert")).toHaveTextContent("job-bus-route");
  });
});
