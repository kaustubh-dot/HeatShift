import { useEffect } from "react";

import { BriefChapter } from "./components/BriefChapter";
import { AppShell } from "./components/AppShell";
import { PlanChapter } from "./components/PlanChapter";
import { WhyChapter } from "./components/WhyChapter";
import { apiClient, ApiClientError } from "./api/client";
import { findSavedDiagnosis, findSavedSolve, loadFallbackDemo } from "./api/fallback";
import { useAppDispatch, useAppState } from "./state/appState";
import type { DiagnoseRequest, SolveRequest, SolveResponse } from "./types";

const SOLVE_TIME_LIMIT_SECONDS = 5;

function explicitFallbackRequested(): boolean {
  const queryRequested = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("fallback") === "true";
  return queryRequested || import.meta.env.VITE_FALLBACK_MODE === "true";
}

function canUseSavedFallback(error: unknown): boolean {
  return error instanceof ApiClientError && error.canUseSavedFallback;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) return error.toDisplayMessage();
  return error instanceof Error ? error.message : "The request failed.";
}

function firstDeferredJobId(result: SolveResponse | null, selectedJobId: string | null): string | null {
  if (result === null) return null;
  const deferredIds = result.plans.policy_constrained.jobs.filter((job) => !job.served).map((job) => job.job_id);
  return selectedJobId !== null && deferredIds.includes(selectedJobId) ? selectedJobId : deferredIds[0] ?? null;
}

function PendingChapter({ heading, description }: { heading: string; description: string }) {
  return (
    <section className="chapter-placeholder" aria-labelledby="pending-chapter-heading">
      <p className="label-caps">Chapter ready</p>
      <h1 id="pending-chapter-heading">{heading}</h1>
      <p>{description}</p>
    </section>
  );
}

export default function App() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const fallbackRequested = explicitFallbackRequested();
  const designatedDiagnosisId = state.manifest?.designated_diagnosis_job_id ?? firstDeferredJobId(state.solveResult, state.selectedJobId);
  const designatedDiagnosis = designatedDiagnosisId === null ? null : state.diagnoses[designatedDiagnosisId] ?? null;
  const designatedJobId = designatedDiagnosis?.job_id ?? designatedDiagnosisId;
  const designatedJob = designatedJobId === null ? null : state.scenario?.jobs.find((job) => job.id === designatedJobId) ?? null;

  useEffect(() => {
    if (state.request.demo.status !== "idle") return;
    let active = true;
    dispatch({ type: "request_started", request: "demo" });
    void (async () => {
      if (fallbackRequested) {
        try {
          const bundle = await loadFallbackDemo();
          if (active) dispatch({ type: "demo_loaded", bundle, source: "saved" });
        } catch (error) {
          if (active) dispatch({ type: "request_failed", request: "demo", message: errorMessage(error) });
        }
        return;
      }

      try {
        const demo = await apiClient.getDemo();
        if (active) dispatch({ type: "demo_inputs_loaded", demo });
      } catch (error) {
        if (!active) return;
        if (!canUseSavedFallback(error)) {
          dispatch({ type: "request_failed", request: "demo", message: errorMessage(error) });
          return;
        }
        try {
          const bundle = await loadFallbackDemo();
          if (active) dispatch({ type: "demo_loaded", bundle, source: "saved" });
        } catch (fallbackError) {
          if (active) dispatch({ type: "request_failed", request: "demo", message: `${errorMessage(error)} Saved fallback failed: ${errorMessage(fallbackError)}` });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [dispatch, fallbackRequested, state.request.demo.status]);

  useEffect(() => {
    if (
      state.dataSource !== "live" ||
      state.request.demo.status !== "success" ||
      state.request.solve.status !== "idle" ||
      state.scenario === null ||
      state.policy === null ||
      state.solveResult !== null
    ) {
      return;
    }
    const scenario = state.scenario;
    const policy = state.policy;
    const request: SolveRequest = {
      scenario,
      policy,
      heat_adjustment_c: 0,
      time_limit_seconds: SOLVE_TIME_LIMIT_SECONDS,
    };
    let active = true;
    dispatch({ type: "request_started", request: "solve" });
    void apiClient.solve(request)
      .then((result) => {
        if (active) dispatch({ type: "request_succeeded", request: "solve", result });
      })
      .catch(async (error: unknown) => {
        if (!active) return;
        if (!canUseSavedFallback(error)) {
          dispatch({ type: "request_failed", request: "solve", message: errorMessage(error) });
          return;
        }
        try {
          const bundle = await loadFallbackDemo();
          const savedResult = findSavedSolve(bundle, request);
          if (savedResult === null) {
            dispatch({ type: "request_failed", request: "solve", message: `${errorMessage(error)} No exact saved solve matches the returned scenario, policy, and heat adjustment.` });
            return;
          }
          dispatch({ type: "demo_loaded", bundle, source: "saved" });
          dispatch({ type: "request_succeeded", request: "solve", result: savedResult });
        } catch (fallbackError) {
          dispatch({ type: "request_failed", request: "solve", message: `${errorMessage(error)} Saved fallback failed: ${errorMessage(fallbackError)}` });
        }
      });
    return () => {
      active = false;
    };
  }, [dispatch, state.dataSource, state.policy, state.request.demo.status, state.request.solve.status, state.scenario, state.solveResult]);

  useEffect(() => {
    const diagnosisJobId = state.manifest?.designated_diagnosis_job_id ?? firstDeferredJobId(state.solveResult, state.selectedJobId);
    if (
      state.dataSource !== "live" ||
      state.chapter !== "why" ||
      state.request.diagnosis.status !== "idle" ||
      state.scenario === null ||
      state.policy === null ||
      state.solveResult === null ||
      diagnosisJobId === null ||
      state.diagnoses[diagnosisJobId] !== undefined
    ) {
      return;
    }
    const scenario = state.scenario;
    const policy = state.policy;
    const request: DiagnoseRequest = {
      scenario,
      policy,
      job_id: diagnosisJobId,
      heat_adjustment_c: 0,
      time_limit_seconds: SOLVE_TIME_LIMIT_SECONDS,
    };
    let active = true;
    dispatch({ type: "request_started", request: "diagnosis" });
    void apiClient.diagnose(request)
      .then((result) => {
        if (active) dispatch({ type: "request_succeeded", request: "diagnosis", result });
      })
      .catch(async (error: unknown) => {
        if (!active) return;
        if (!canUseSavedFallback(error)) {
          dispatch({ type: "request_failed", request: "diagnosis", message: errorMessage(error) });
          return;
        }
        try {
          const bundle = await loadFallbackDemo();
          const savedResult = findSavedDiagnosis(bundle, request);
          if (savedResult === null) {
            dispatch({ type: "request_failed", request: "diagnosis", message: `${errorMessage(error)} No exact saved diagnosis matches the returned scenario, policy, heat adjustment, and job.` });
            return;
          }
          dispatch({ type: "demo_loaded", bundle, source: "saved" });
          dispatch({ type: "request_succeeded", request: "diagnosis", result: savedResult });
        } catch (fallbackError) {
          dispatch({ type: "request_failed", request: "diagnosis", message: `${errorMessage(error)} Saved fallback failed: ${errorMessage(fallbackError)}` });
        }
      });
    return () => {
      active = false;
    };
  }, [dispatch, state.chapter, state.dataSource, state.diagnoses, state.manifest, state.policy, state.request.diagnosis.status, state.scenario, state.selectedJobId, state.solveResult]);

  const applyHeatShock = (request: { heat_adjustment_c: 2 }) => {
    dispatch({ type: "request_started", request: "heatShock" });
    if (state.scenario === null || state.policy === null) {
      dispatch({ type: "request_failed", request: "heatShock", message: "The scenario and policy are not available for heat shock." });
      return;
    }
    const solveRequest: SolveRequest = {
      scenario: state.scenario,
      policy: state.policy,
      heat_adjustment_c: request.heat_adjustment_c,
      time_limit_seconds: SOLVE_TIME_LIMIT_SECONDS,
    };
    if (state.dataSource === "saved") {
      const result = state.heatShockResult;
      Promise.resolve().then(() => {
        if (
          result === null ||
          result.scenario.id !== state.scenario!.id ||
          result.scenario.policy_id !== state.policy!.id ||
          result.scenario.heat_adjustment_c !== request.heat_adjustment_c ||
          result.plans.heat_shock === null
        ) {
          dispatch({ type: "request_failed", request: "heatShock", message: "The saved heat-shock response did not match +2°C." });
          return;
        }
        dispatch({ type: "request_succeeded", request: "heatShock", result });
      });
      return;
    }
    void apiClient.solve(solveRequest)
      .then((result) => dispatch({ type: "request_succeeded", request: "heatShock", result }))
      .catch(async (error: unknown) => {
        if (!canUseSavedFallback(error)) {
          dispatch({ type: "request_failed", request: "heatShock", message: errorMessage(error) });
          return;
        }
        try {
          const bundle = await loadFallbackDemo();
          const savedResult = findSavedSolve(bundle, solveRequest);
          if (savedResult === null || savedResult.plans.heat_shock === null) {
            dispatch({ type: "request_failed", request: "heatShock", message: `${errorMessage(error)} No exact saved heat-shock response matches the returned scenario, policy, and adjustment.` });
            return;
          }
          dispatch({ type: "demo_loaded", bundle, source: "saved" });
          dispatch({ type: "request_succeeded", request: "heatShock", result: savedResult });
        } catch (fallbackError) {
          dispatch({ type: "request_failed", request: "heatShock", message: `${errorMessage(error)} Saved fallback failed: ${errorMessage(fallbackError)}` });
        }
      });
  };

  const content =
    state.request.demo.status === "error" ? (
      <section className="fixture-error" role="alert" aria-labelledby="demo-error-heading">
        <p className="label-caps">Demo data error</p>
        <h1 id="demo-error-heading">The scenario inputs could not load.</h1>
        <p>{state.request.demo.error ?? "The fallback response was not available."}</p>
      </section>
    ) : state.request.demo.status === "loading" || state.scenario === null ? (
      <section className="chapter-placeholder" aria-labelledby="loading-heading" role="status">
        <p className="label-caps">{fallbackRequested ? "Locked demo scenario" : "Live scenario"}</p>
        <h1 id="loading-heading">{fallbackRequested ? "Loading the saved solver run." : "Loading the live solver inputs."}</h1>
        <p>The first chapter will open when the genuine scenario and policy are ready.</p>
      </section>
    ) : state.chapter === "brief" ? (
      <BriefChapter
        scenario={state.scenario}
        fixtureError={state.request.demo.error ?? state.request.solve.error}
        onGenerate={() => dispatch({ type: "navigate", chapter: "plan" })}
      />
    ) : state.chapter === "plan" && state.solveResult === null && state.request.solve.status === "error" ? (
      <section className="fixture-error" role="alert" aria-labelledby="solve-error-heading">
        <p className="label-caps">Solve unavailable</p>
        <h1 id="solve-error-heading">The live plan could not be loaded.</h1>
        <p>{state.request.solve.error}</p>
      </section>
    ) : state.chapter === "plan" && state.solveResult === null ? (
      <PendingChapter
        heading="Building the policy-constrained plan."
        description="The returned scenario is ready. The solver plan will appear here when it is available."
      />
    ) : state.chapter === "plan" && state.solveResult !== null ? (
      <PlanChapter
        scenario={state.scenario}
        serviceFirstPlan={state.solveResult.plans.service_first}
        policyPlan={state.solveResult.plans.policy_constrained}
        planDiff={state.solveResult.plan_diff}
        selectedJobId={state.selectedJobId}
        onJobClick={(jobId) => dispatch({ type: "select_job", jobId })}
      />
    ) : state.chapter === "why" ? (
      <WhyChapter
        job={designatedJob}
        diagnosis={designatedDiagnosis}
        jobs={state.scenario.jobs}
        policyPlan={state.solveResult?.plans.policy_constrained ?? null}
        heatShockResult={state.heatShockResult}
        heatShockStatus={state.request.heatShock.status}
        heatShockError={state.request.heatShock.error}
        selectedJobId={state.selectedJobId}
        onJobClick={(jobId) => dispatch({ type: "select_job", jobId })}
        onApplyHeatShock={applyHeatShock}
        onResetHeatShock={() => dispatch({ type: "heatShock_reset" })}
        diagnosisRequestStatus={state.request.diagnosis.status}
        diagnosisRequestError={state.request.diagnosis.error}
      />
    ) : (
      <PendingChapter heading="Why / What-if" description="The diagnosis chapter is waiting for a saved solver response." />
    );

  return (
    <AppShell>{content}</AppShell>
  );
}
