import type { ReactNode } from "react";

import { SolverEvidence } from "./SolverEvidence";
import { useAppDispatch, useAppState, type ChapterId } from "../state/appState";

interface AppShellProps {
  children: ReactNode;
}

const CHAPTERS: ReadonlyArray<{ id: ChapterId; index: string; label: string }> = [
  { id: "brief", index: "01", label: "Tomorrow's Brief" },
  { id: "plan", index: "02", label: "Plan Transformation" },
  { id: "why", index: "03", label: "Why / What-if" },
];

const DEFAULT_DISCLAIMER =
  "Synthetic demonstration policy. Not medical, legal, or workplace-safety guidance. Organizations must supply and approve their own policy.";

function chapterEnabled(chapter: ChapterId, hasSolve: boolean): boolean {
  if (chapter === "brief") return true;
  if (chapter === "plan") return hasSolve;
  return hasSolve;
}

export function AppShell({ children }: AppShellProps) {
  const state = useAppState();
  const dispatch = useAppDispatch();
  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="chapter-nav">
        <div className="chapter-nav__inner">
          <a className="brand-mark" href="#main-content" aria-label="HeatShift home">
            Heat<span className="brand-mark__accent">Shift</span>
          </a>
          <nav aria-label="Chapter navigation">
            <ol className="chapter-list">
              {CHAPTERS.map((chapter) => {
                const enabled = chapterEnabled(chapter.id, state.solveResult !== null);
                return (
                  <li key={chapter.id}>
                    <button
                      className="chapter-step"
                      type="button"
                      aria-current={state.chapter === chapter.id ? "step" : undefined}
                      disabled={!enabled}
                      onClick={() => dispatch({ type: "navigate", chapter: chapter.id })}
                    >
                      <span className="chapter-step__index" aria-hidden="true">
                        {chapter.index}
                      </span>
                      {chapter.label}
                    </button>
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>
      </header>

      <main className="app-main" id="main-content" tabIndex={-1}>
        {children}
      </main>

      <footer className="trust-bar" aria-label="Policy and solver trust information">
        <p className="trust-bar__disclaimer">
          <strong>Policy boundary.</strong> {state.policy?.disclaimer ?? DEFAULT_DISCLAIMER}
        </p>
        <div className="trust-bar__evidence" aria-live="polite">
          <SolverEvidence
            plan={state.solveResult?.plans.policy_constrained ?? null}
            dataSource={state.dataSource}
            savedManifest={state.manifest}
          />
        </div>
      </footer>
    </div>
  );
}
