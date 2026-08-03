import {
  createContext,
  useContext,
  useReducer,
  type Dispatch,
  type PropsWithChildren,
} from "react";

import type {
  DiagnosisResponse,
  DemoBundle,
  Plan,
  PlanDiff,
  Policy,
  SavedManifest,
  Scenario,
  SolveResponse,
} from "../types";

export type ChapterId = "brief" | "plan" | "why";
export type DataSource = "live" | "saved";
export type RequestKey = "demo" | "solve" | "diagnosis" | "heatShock";
export type RequestStatus = "idle" | "loading" | "success" | "error";

export interface RequestState {
  status: RequestStatus;
  error: string | null;
}

export interface AppState {
  chapter: ChapterId;
  scenario: Scenario | null;
  policy: Policy | null;
  solveResult: SolveResponse | null;
  heatShockResult: SolveResponse | null;
  diagnoses: Record<string, DiagnosisResponse>;
  manifest: SavedManifest | null;
  selectedJobId: string | null;
  selectedCrewId: string | null;
  dataSource: DataSource;
  request: Record<RequestKey, RequestState>;
}

const idleRequest = (): RequestState => ({ status: "idle", error: null });

export const initialAppState: AppState = {
  chapter: "brief",
  scenario: null,
  policy: null,
  solveResult: null,
  heatShockResult: null,
  diagnoses: {},
  manifest: null,
  selectedJobId: null,
  selectedCrewId: null,
  dataSource: "live",
  request: {
    demo: idleRequest(),
    solve: idleRequest(),
    diagnosis: idleRequest(),
    heatShock: idleRequest(),
  },
};

export type AppAction =
  | { type: "navigate"; chapter: ChapterId }
  | { type: "demo_loaded"; bundle: DemoBundle; source: DataSource }
  | { type: "select_job"; jobId: string | null }
  | { type: "select_crew"; crewId: string | null }
  | { type: "request_started"; request: RequestKey }
  | { type: "request_succeeded"; request: "solve" | "heatShock"; result: SolveResponse }
  | { type: "request_succeeded"; request: "diagnosis"; result: DiagnosisResponse }
  | { type: "request_failed"; request: RequestKey; message: string }
  | { type: "heatShock_reset" }
  | { type: "source_mode_changed"; source: DataSource };

function withRequest(
  state: AppState,
  request: RequestKey,
  next: RequestState,
): AppState {
  return {
    ...state,
    request: {
      ...state.request,
      [request]: next,
    },
  };
}

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "navigate":
      return { ...state, chapter: action.chapter };
    case "demo_loaded":
      return withRequest(
        {
          ...state,
          scenario: action.bundle.scenario,
          policy: action.bundle.policy,
          solveResult: action.bundle.base_solve,
          heatShockResult: action.bundle.heat_shock_solve,
          diagnoses: action.bundle.diagnoses,
          manifest: action.bundle.manifest,
          dataSource: action.source,
        },
        "demo",
        { status: "success", error: null },
      );
    case "select_job":
      return { ...state, selectedJobId: action.jobId };
    case "select_crew":
      return { ...state, selectedCrewId: action.crewId };
    case "request_started":
      return withRequest(state, action.request, { status: "loading", error: null });
    case "request_succeeded": {
      const next = withRequest(state, action.request, { status: "success", error: null });
      if (action.request === "solve") {
        return { ...next, solveResult: action.result };
      }
      if (action.request === "heatShock") {
        return { ...next, heatShockResult: action.result };
      }
      if (action.request === "diagnosis") {
        return {
          ...next,
          diagnoses: {
            ...next.diagnoses,
            [action.result.job_id]: action.result,
          },
        };
      }
      return next;
    }
    case "request_failed":
      return withRequest(state, action.request, {
        status: "error",
        error: action.message,
      });
    case "heatShock_reset":
      return withRequest(state, "heatShock", { status: "idle", error: null });
    case "source_mode_changed":
      return { ...state, dataSource: action.source };
  }
}

export function selectPolicyPlan(state: AppState): Plan | null {
  return state.solveResult?.plans.policy_constrained ?? null;
}

export function selectPlanDiff(state: AppState): PlanDiff[] {
  return state.solveResult?.plan_diff ?? [];
}

export function selectHeatShockPlan(state: AppState): Plan | null {
  if (state.request.heatShock.status !== "success") return null;
  return state.heatShockResult?.plans.heat_shock ?? null;
}

export function selectSelectedDiagnosis(state: AppState): DiagnosisResponse | null {
  if (state.selectedJobId === null) return null;
  return state.diagnoses[state.selectedJobId] ?? null;
}

const AppStateContext = createContext<AppState | null>(null);
const AppDispatchContext = createContext<Dispatch<AppAction> | null>(null);

export function AppStateProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(appReducer, initialAppState);
  return (
    <AppStateContext.Provider value={state}>
      <AppDispatchContext.Provider value={dispatch}>{children}</AppDispatchContext.Provider>
    </AppStateContext.Provider>
  );
}

export function useAppState(): AppState {
  const state = useContext(AppStateContext);
  if (state === null) throw new Error("useAppState must be used inside AppStateProvider");
  return state;
}

export function useAppDispatch(): Dispatch<AppAction> {
  const dispatch = useContext(AppDispatchContext);
  if (dispatch === null) throw new Error("useAppDispatch must be used inside AppStateProvider");
  return dispatch;
}
