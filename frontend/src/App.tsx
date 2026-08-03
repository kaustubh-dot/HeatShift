import { useEffect } from "react";

import { BriefChapter } from "./components/BriefChapter";
import { AppShell } from "./components/AppShell";
import { PlanChapter } from "./components/PlanChapter";
import { WhyChapter } from "./components/WhyChapter";
import { loadFallbackDemo } from "./api/fallback";
import { useAppDispatch, useAppState } from "./state/appState";

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
  const designatedDiagnosisId = state.manifest?.designated_diagnosis_job_id ?? null;
  const designatedDiagnosis = designatedDiagnosisId === null ? null : state.diagnoses[designatedDiagnosisId] ?? null;
  const designatedJob = designatedDiagnosis === null ? null : state.scenario?.jobs.find((job) => job.id === designatedDiagnosis.job_id) ?? null;

  useEffect(() => {
    if (state.scenario !== null || state.request.demo.status !== "idle") return;
    let active = true;
    dispatch({ type: "request_started", request: "demo" });
    loadFallbackDemo()
      .then((bundle) => {
        if (active) dispatch({ type: "demo_loaded", bundle, source: "saved" });
      })
      .catch((error: unknown) => {
        if (!active) return;
        const message = error instanceof Error ? error.message : "Saved demo data could not be loaded.";
        dispatch({ type: "request_failed", request: "demo", message });
      });
    return () => {
      active = false;
    };
  }, [dispatch, state.request.demo.status, state.scenario]);

  const applyHeatShock = (request: { heat_adjustment_c: 2 }) => {
    dispatch({ type: "request_started", request: "heatShock" });
    const result = state.heatShockResult;
    Promise.resolve().then(() => {
      if (result?.scenario.heat_adjustment_c !== request.heat_adjustment_c || result.plans.heat_shock === null) {
        dispatch({ type: "request_failed", request: "heatShock", message: "The saved heat-shock response did not match +2°C." });
        return;
      }
      dispatch({ type: "request_succeeded", request: "heatShock", result });
    });
  };

  const content =
    state.request.demo.status === "error" ? (
      <section className="fixture-error" role="alert" aria-labelledby="demo-error-heading">
        <p className="label-caps">Saved demo error</p>
        <h1 id="demo-error-heading">The locked demo could not load.</h1>
        <p>{state.request.demo.error ?? "The fallback response was not available."}</p>
      </section>
    ) : state.request.demo.status === "loading" || state.scenario === null ? (
      <section className="chapter-placeholder" aria-labelledby="loading-heading" role="status">
        <p className="label-caps">Locked demo scenario</p>
        <h1 id="loading-heading">Loading the saved solver run.</h1>
        <p>The first chapter will open when the genuine scenario and policy are ready.</p>
      </section>
    ) : state.chapter === "brief" ? (
      <BriefChapter
        scenario={state.scenario}
        fixtureError={state.request.demo.error}
        onGenerate={() => dispatch({ type: "navigate", chapter: "plan" })}
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
