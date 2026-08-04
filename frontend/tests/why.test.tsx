/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { parseDemoBundle } from "../src/api/fallback";
import { WhyChapter } from "../src/components/WhyChapter";

afterEach(cleanup);

describe("diagnosis chapter", () => {
  const bundle = parseDemoBundle(rawBundle);
  const diagnosis = bundle.diagnoses[bundle.manifest.designated_diagnosis_job_id];
  const job = bundle.scenario.jobs.find((candidate) => candidate.id === diagnosis.job_id)!;

  it("renders the designated saved diagnosis and every canonical evidence field", () => {
    render(<WhyChapter job={job} diagnosis={diagnosis} />);

    const chapter = screen.getByRole("region", { name: job.name });
    expect(screen.getByRole("heading", { name: job.name })).toBeVisible();
    expect(screen.getByText(diagnosis.job_id)).toBeVisible();
    expect(screen.getByText("proven infeasible under listed commitments")).toBeVisible();
    expect(chapter.querySelector(".diagnosis-result .solver-evidence__status")).toHaveTextContent("INFEASIBLE");

    for (const commitment of diagnosis.retained_commitments) expect(screen.getByText(commitment)).toBeVisible();
    for (const ruleId of diagnosis.binding_rule_ids) expect(screen.getByText(ruleId)).toBeVisible();
    expect(screen.getByText("None returned")).toBeVisible();

    const delta = document.querySelector('dl[aria-label="Counterfactual objective delta"]');
    expect(delta).not.toBeNull();
    expect(delta).toHaveTextContent("Critical service0");
    expect(delta).toHaveTextContent("Planned service value0");
    expect(delta).toHaveTextContent("Travel minutes0");
    expect(delta).toHaveTextContent("Overtime minutes0");

    const table = screen.getByRole("table", { name: "Every tested intervention returned by the diagnosis solver" });
    expect(within(table).getAllByRole("row")).toHaveLength(diagnosis.tested_interventions.length + 1);
    for (const intervention of diagnosis.tested_interventions) {
      expect(table).toHaveTextContent(`${intervention.value_minutes} min`);
      expect(table).toHaveTextContent(intervention.status);
    }
  });

  it("uses the exact allowed classification language and focuses requested results", () => {
    const classifications = [
      ["equivalent_alternative", "equivalent alternative"],
      ["feasible_with_cost", "feasible with displayed cost"],
      ["proven_infeasible", "proven infeasible under listed commitments"],
      ["not_proven", "not proven within limit"],
    ] as const;

    for (const [classification, copy] of classifications) {
      const view = render(
        <WhyChapter
          job={job}
          diagnosis={{ ...diagnosis, classification }}
        />,
      );
      expect(screen.getByText(copy)).toBeVisible();
      view.unmount();
    }

    render(<WhyChapter job={job} diagnosis={diagnosis} diagnosisRequestStatus="success" />);
    expect(document.activeElement).toBe(screen.getByRole("heading", { name: job.name }));
  });
});
