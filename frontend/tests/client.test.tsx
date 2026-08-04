/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it } from "vitest";

import rawBundle from "../public/fallback/demo.json";
import { ApiClientError, createApiClient } from "../src/api/client";
import { findSavedDiagnosis, findSavedSolve, parseDemoBundle } from "../src/api/fallback";
import { SolverEvidence } from "../src/components/SolverEvidence";
import type { DiagnoseRequest, DemoResponse, SolveRequest } from "../src/types";

afterEach(cleanup);

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("live API boundary and exact fallback", () => {
  const bundle = parseDemoBundle(rawBundle);
  const solveRequest: SolveRequest = {
    scenario: bundle.scenario,
    policy: bundle.policy,
    heat_adjustment_c: 0,
    time_limit_seconds: 5,
  };
  const shockRequest: SolveRequest = { ...solveRequest, heat_adjustment_c: 2 };
  const diagnosisRequest: DiagnoseRequest = {
    ...solveRequest,
    job_id: bundle.manifest.designated_diagnosis_job_id,
  };

  it("uses the live solve endpoint and parses a successful response", async () => {
    let receivedBody = "";
    const client = createApiClient({
      fetcher: async (input, init) => {
        expect(input).toBe("/api/solve");
        expect(init?.method).toBe("POST");
        receivedBody = String(init?.body);
        return jsonResponse(bundle.base_solve);
      },
    });

    const response = await client.solve(solveRequest);

    expect(response).toStrictEqual(bundle.base_solve);
    expect(JSON.parse(receivedBody)).toMatchObject({
      heat_adjustment_c: 0,
      time_limit_seconds: 5,
      scenario: { id: bundle.scenario.id },
      policy: { id: bundle.policy.id },
    });
  });

  it("parses live demo inputs without treating optional metadata as a solve response", async () => {
    const demo: DemoResponse = {
      scenario: bundle.scenario,
      policy: bundle.policy,
      display_coordinates: Object.fromEntries(bundle.scenario.locations.map((location) => [location.id, location.coordinates])),
      saved_result_metadata: null,
    };
    const client = createApiClient({ fetcher: async (input) => {
      expect(input).toBe("/api/demo");
      return jsonResponse(demo);
    } });

    const response = await client.getDemo();

    expect(response.scenario.id).toBe(bundle.scenario.id);
    expect(response.saved_result_metadata).toBeNull();
  });

  it("selects only exact saved solve and diagnosis entries", () => {
    expect(findSavedSolve(bundle, solveRequest)).toBe(bundle.base_solve);
    expect(findSavedSolve(bundle, shockRequest)).toBe(bundle.heat_shock_solve);
    expect(findSavedDiagnosis(bundle, diagnosisRequest)).toBe(bundle.diagnoses[diagnosisRequest.job_id]);

    expect(findSavedSolve(bundle, { ...solveRequest, scenario: { ...bundle.scenario, id: "other-scenario" } })).toBeNull();
    expect(findSavedSolve(bundle, { ...solveRequest, policy: { ...bundle.policy, id: "other-policy" } })).toBeNull();
    expect(
      findSavedSolve(bundle, {
        ...solveRequest,
        scenario: { ...bundle.scenario, jobs: [{ ...bundle.scenario.jobs[0], service_value: 999 }, ...bundle.scenario.jobs.slice(1)] },
      }),
    ).toBeNull();
    expect(
      findSavedSolve(bundle, {
        ...solveRequest,
        policy: { ...bundle.policy, rules: [{ ...bundle.policy.rules[0], max_active_slots: 99 }, ...bundle.policy.rules.slice(1)] },
      }),
    ).toBeNull();
    expect(findSavedSolve(bundle, { ...shockRequest, heat_adjustment_c: 3 })).toBeNull();
    expect(findSavedDiagnosis(bundle, { ...diagnosisRequest, job_id: "job-sidewalk" })).toBeNull();
    expect(findSavedDiagnosis(bundle, { ...diagnosisRequest, heat_adjustment_c: 2 })).toBeNull();
  });

  it("preserves structured validation code, path, and message without allowing fallback", async () => {
    const client = createApiClient({
      fetcher: async () =>
        jsonResponse(
          {
            error: {
              code: "INVALID_SCENARIO",
              message: "Scenario validation failed.",
              details: [{ path: "jobs[2].required_equipment[0]", code: "UNKNOWN_REFERENCE", message: "Equipment is not present." }],
            },
          },
          422,
        ),
    });

    const error = await client.solve(solveRequest).catch((value: unknown) => value);

    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({ kind: "client", code: "INVALID_SCENARIO", status: 422 });
    expect((error as ApiClientError).details[0]).toEqual({
      path: "jobs[2].required_equipment[0]",
      code: "UNKNOWN_REFERENCE",
      message: "Equipment is not present.",
    });
    expect((error as ApiClientError).toDisplayMessage()).toContain("INVALID_SCENARIO: Scenario validation failed. (jobs[2].required_equipment[0]: Equipment is not present.)");
    expect((error as ApiClientError).canUseSavedFallback).toBe(false);
  });

  it("does not treat a malformed 2xx response as a fallback-eligible failure", async () => {
    const client = createApiClient({ fetcher: async () => jsonResponse({ scenario: {} }) });

    const error = await client.solve(solveRequest).catch((value: unknown) => value);

    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({ kind: "malformed", code: "MALFORMED_RESPONSE" });
    expect((error as ApiClientError).canUseSavedFallback).toBe(false);
  });

  it("rejects malformed nested plan fields before the UI can dereference them", async () => {
    const malformed = structuredClone(bundle.base_solve) as Record<string, unknown>;
    const plans = malformed.plans as Record<string, unknown>;
    const policyPlan = plans.policy_constrained as Record<string, unknown>;
    const timeline = policyPlan.timeline_segments as Array<Record<string, unknown>>;
    timeline[0].state = "not-a-timeline-state";

    await expect(createApiClient({ fetcher: async () => jsonResponse(malformed) }).solve(solveRequest)).rejects.toMatchObject({
      kind: "malformed",
      code: "MALFORMED_RESPONSE",
    });
  });

  it("marks aborts and server failures as fallback-eligible", async () => {
    const abortClient = createApiClient({
      timeoutMs: 1,
      fetcher: async (_input, init) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
        }),
    });
    const abortError = await abortClient.solve(solveRequest).catch((value: unknown) => value);

    const serverClient = createApiClient({
      fetcher: async () => jsonResponse({ error: { code: "INTERNAL_ERROR", message: "The server could not complete the request.", details: [] } }, 500),
    });
    const serverError = await serverClient.solve(solveRequest).catch((value: unknown) => value);

    expect(abortError).toMatchObject({ kind: "abort", code: "REQUEST_ABORTED" });
    expect((abortError as ApiClientError).canUseSavedFallback).toBe(true);
    expect(serverError).toMatchObject({ kind: "server", code: "INTERNAL_ERROR", status: 500 });
    expect((serverError as ApiClientError).canUseSavedFallback).toBe(true);
  });

  it("keeps a live FEASIBLE response successful while showing the proof warning", () => {
    render(<SolverEvidence plan={bundle.base_solve.plans.service_first} dataSource="live" />);

    expect(screen.getByRole("status", { name: "Solver evidence status" }).querySelector('[data-status="FEASIBLE"]')).toBeVisible();
    expect(screen.getByText("Feasible incumbent returned; optimality was not proven.")).toBeVisible();
  });

  it("keeps the saved-run disclosure visible with fixture provenance", () => {
    render(<SolverEvidence plan={bundle.base_solve.plans.policy_constrained} dataSource="saved" savedManifest={bundle.manifest} />);

    expect(screen.getByText(/SAVED SOLVER RUN · Live API unavailable · Results generated from the locked demo scenario/)).toBeVisible();
    expect(screen.getByText(new RegExp(bundle.manifest.fixture_version))).toBeVisible();
  });
});
