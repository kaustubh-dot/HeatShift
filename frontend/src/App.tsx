import { useEffect } from "react";

import { BriefChapter } from "./components/BriefChapter";
import { AppShell } from "./components/AppShell";
import { PlanChapter } from "./components/PlanChapter";
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
        plan={state.solveResult.plans.policy_constrained}
        selectedJobId={state.selectedJobId}
        onJobClick={(jobId) => dispatch({ type: "select_job", jobId })}
      />
    ) : (
      <PendingChapter
        heading="Why / What-if"
        description="The next packets will expose the forced-inclusion diagnosis and +2°C counterfactual."
      />
    );

  return (
    <AppShell>{content}</AppShell>
  );
}
