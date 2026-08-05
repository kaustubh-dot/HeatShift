import { FallbackDataError, parseDemoResponse, parseDiagnosisResponse, parseSolveResponse } from "./fallback";
import type {
  ApiErrorDetail,
  DemoResponse,
  DiagnoseRequest,
  DiagnosisResponse,
  SolveRequest,
  SolveResponse,
} from "../types";

export const API_TIMEOUT_MS = 15_000;
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export type ApiFailureKind = "network" | "abort" | "client" | "server" | "malformed";

export class ApiClientError extends Error {
  constructor(
    readonly kind: ApiFailureKind,
    readonly status: number | null,
    readonly code: string,
    message: string,
    readonly details: ApiErrorDetail[] = [],
  ) {
    super(message);
    this.name = "ApiClientError";
  }

  get path(): string | null {
    return this.details[0]?.path ?? null;
  }

  get canUseSavedFallback(): boolean {
    return this.kind === "network" || this.kind === "abort" || this.kind === "server";
  }

  toDisplayMessage(): string {
    const detailText = this.details.map((detail) => `${detail.path}: ${detail.message}`).join("; ");
    return `${this.code}: ${this.message}${detailText === "" ? "" : ` (${detailText})`}`;
  }
}

export interface ApiClientOptions {
  fetcher?: typeof fetch;
  timeoutMs?: number;
}

export interface ApiClient {
  getDemo: () => Promise<DemoResponse>;
  solve: (request: SolveRequest) => Promise<SolveResponse>;
  diagnose: (request: DiagnoseRequest) => Promise<DiagnosisResponse>;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

function structuredError(value: unknown): { code: string; message: string; details: ApiErrorDetail[] } | null {
  const root = asRecord(value);
  const error = asRecord(root?.error);
  if (error === null || typeof error.code !== "string" || typeof error.message !== "string") return null;
  const details = Array.isArray(error.details)
    ? error.details.flatMap((detail) => {
        const item = asRecord(detail);
        if (item === null || typeof item.path !== "string" || typeof item.code !== "string" || typeof item.message !== "string") return [];
        return [{ path: item.path, code: item.code, message: item.message }];
      })
    : [];
  return { code: error.code, message: error.message, details };
}

async function readJson(response: Response): Promise<unknown | null> {
  try {
    return (await response.json()) as unknown;
  } catch {
    return null;
  }
}

function malformedResponse(error: unknown): ApiClientError {
  if (error instanceof FallbackDataError) {
    return new ApiClientError(
      "malformed",
      200,
      "MALFORMED_RESPONSE",
      "The server response did not match the frontend contract.",
      [{ path: error.path, code: "INVALID_RESPONSE", message: error.message }],
    );
  }
  return new ApiClientError("malformed", 200, "MALFORMED_RESPONSE", "The server response was not valid JSON.");
}

async function requestJson<T>(
  path: string,
  parser: (value: unknown) => T,
  options: ApiClientOptions,
  init: RequestInit = {},
): Promise<T> {
  const fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeoutMs ?? API_TIMEOUT_MS);
  try {
    let response: Response;
    try {
      response = await fetcher(path, { ...init, signal: controller.signal });
    } catch (error) {
      const aborted = controller.signal.aborted || (error instanceof DOMException && error.name === "AbortError") || (error instanceof Error && error.name === "AbortError");
      throw new ApiClientError(
        aborted ? "abort" : "network",
        null,
        aborted ? "REQUEST_ABORTED" : "NETWORK_ERROR",
        aborted ? "The request exceeded the 15-second browser timeout or was aborted." : "The API could not be reached.",
      );
    }

    if (!response.ok) {
      const payload = await readJson(response);
      const error = structuredError(payload);
      const kind: ApiFailureKind = response.status >= 500 ? "server" : "client";
      throw new ApiClientError(
        kind,
        response.status,
        error?.code ?? `HTTP_${response.status}`,
        error?.message ?? `The API returned HTTP ${response.status}.`,
        error?.details ?? [],
      );
    }

    const payload = await readJson(response);
    if (payload === null) throw malformedResponse(null);
    try {
      return parser(payload);
    } catch (error) {
      throw malformedResponse(error);
    }
  } finally {
    clearTimeout(timeoutId);
  }
}

export function createApiClient(options: ApiClientOptions = {}): ApiClient {
  return {
    getDemo: () => requestJson(apiUrl("/api/demo"), parseDemoResponse, options),
    solve: (request) =>
      requestJson(apiUrl("/api/solve"), parseSolveResponse, options, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      }),
    diagnose: (request) =>
      requestJson(apiUrl("/api/diagnose"), parseDiagnosisResponse, options, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      }),
  };
}

export const apiClient = createApiClient();
