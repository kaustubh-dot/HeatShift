"""FastAPI boundary for the canonical HeatShift contracts."""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.status import (
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_504_GATEWAY_TIMEOUT,
)

from .cli import FIXTURE_DIR, load_fixtures
from .diagnostics import DiagnosisValidationError, _adjust_scenario, diagnose_job
from .metrics import ModelReconciliationError, extract_plan_facts
from .models import (
    ApiError,
    ApiErrorCode,
    ApiErrorDetail,
    DiagnoseRequest,
    DiagnosisResponse,
    DemoResponse,
    SavedResultMetadata,
    SolveRequest,
    SolveResponse,
    SolverStatus,
)
from .optimizer import build_optimizer_model, solve_staged
from .patterns import generate_policy_constrained_patterns
from .service import SolveServiceError, solve_scenario
from .validation import validate_scenario


app = FastAPI(title="HeatShift API")
STATIC_DIR = FIXTURE_DIR.parent / "static"
STATIC_ROOT = STATIC_DIR.resolve()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Return process readiness without exposing product or solver data."""

    return {"status": "ok"}


@app.get("/api/demo", response_model=DemoResponse)
def get_demo() -> DemoResponse:
    """Return bundled inputs, schematic coordinates, and saved-result metadata."""

    return load_bundled_demo()


@app.post("/api/solve", response_model=SolveResponse)
def post_solve(request: SolveRequest) -> SolveResponse | JSONResponse:
    """Solve the submitted scenario through the canonical service orchestration."""

    try:
        return solve_scenario(request)
    except SolveServiceError as error:
        return _solve_service_error_response(error)


@app.post("/api/diagnose", response_model=DiagnosisResponse)
def post_diagnose(request: DiagnoseRequest) -> DiagnosisResponse | JSONResponse:
    """Force the requested deferred job while retaining the original commitments."""

    try:
        _reject_unknown_job_before_solving(request)
        scenario_issues = validate_scenario(request.scenario, request.policy)
        if scenario_issues:
            return _error_response(
                ApiErrorCode.INVALID_SCENARIO,
                "Scenario and policy validation failed.",
                scenario_issues,
                HTTP_422_UNPROCESSABLE_CONTENT,
            )
        adjusted_scenario = _adjust_scenario(
            request.scenario,
            request.policy,
            request.heat_adjustment_c,
        )
        adjusted_issues = validate_scenario(adjusted_scenario, request.policy)
        if adjusted_issues:
            return _error_response(
                ApiErrorCode.INVALID_SCENARIO,
                "Scenario and policy validation failed.",
                adjusted_issues,
                HTTP_422_UNPROCESSABLE_CONTENT,
            )

        original_facts, original_result = _build_constrained_context(request)
        return diagnose_job(
            request.scenario,
            request.policy,
            original_facts,
            original_result,
            request.job_id,
            heat_adjustment_c=request.heat_adjustment_c,
            time_limit_seconds=request.time_limit_seconds,
        )
    except DiagnosisValidationError as error:
        return _error_response(
            ApiErrorCode.INVALID_SCENARIO,
            "Diagnosis request validation failed.",
            error.details,
            HTTP_422_UNPROCESSABLE_CONTENT,
        )
    except SolveServiceError as error:
        return _solve_service_error_response(error)


@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str) -> FileResponse:
    """Serve compiled assets and fall back to the SPA entry point for app routes."""

    if path == "api" or path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    index_path = STATIC_ROOT / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Frontend build not found")
    if path == "":
        return FileResponse(index_path)

    candidate = (STATIC_ROOT / path).resolve()
    if not candidate.is_relative_to(STATIC_ROOT):
        raise HTTPException(status_code=404, detail="Asset not found")
    if candidate.is_file():
        return FileResponse(candidate)
    if Path(path).suffix:
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(index_path)


def load_bundled_demo() -> DemoResponse:
    """Load all `/api/demo` inputs through one deterministic service function."""

    scenario, policy = load_fixtures(FIXTURE_DIR)
    display_coordinates = {
        location.id: list(location.coordinates)
        for location in scenario.locations
    }
    return DemoResponse(
        scenario=scenario,
        policy=policy,
        display_coordinates=display_coordinates,
        saved_result_metadata=_load_saved_result_metadata(),
    )


def _load_saved_result_metadata() -> SavedResultMetadata | None:
    manifest_path = FIXTURE_DIR / "saved" / "manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_hash = manifest.get("output_hashes", {}).get("base-solve.json")
    required_values = (
        manifest.get("fixture_version"),
        manifest.get("generated_at"),
        manifest.get("ortools_version"),
        output_hash,
    )
    if not all(isinstance(value, str) and value for value in required_values):
        return None
    return SavedResultMetadata(
        fixture_version=manifest["fixture_version"],
        generated_at=manifest["generated_at"],
        solver_version=manifest["ortools_version"],
        sha256=output_hash,
    )


def _reject_unknown_job_before_solving(request: DiagnoseRequest) -> None:
    if any(job.id == request.job_id for job in request.scenario.jobs):
        return
    raise DiagnosisValidationError(
        (
            ApiErrorDetail(
                path="job_id",
                code="UNKNOWN_REFERENCE",
                message=f"unknown job ID {request.job_id!r}",
            ),
        )
    )


def _build_constrained_context(request: DiagnoseRequest):
    scenario = _adjust_scenario(
        request.scenario,
        request.policy,
        request.heat_adjustment_c,
    )
    patterns = generate_policy_constrained_patterns(scenario, request.policy)
    optimizer_model = build_optimizer_model(
        scenario,
        request.policy,
        patterns,
        enforce_policy=True,
    )
    result = solve_staged(optimizer_model, request.time_limit_seconds)
    if result.status in (SolverStatus.UNKNOWN, SolverStatus.MODEL_INVALID, SolverStatus.INFEASIBLE):
        if not result.selected_pattern_indices:
            code = {
                SolverStatus.UNKNOWN: ApiErrorCode.SOLVER_TIMEOUT,
                SolverStatus.MODEL_INVALID: ApiErrorCode.MODEL_INVALID,
                SolverStatus.INFEASIBLE: ApiErrorCode.NO_FEASIBLE_PLAN,
            }[result.status]
            raise SolveServiceError(
                code=code,
                message=f"{result.status.value} solve produced no reportable plan.",
            )
    try:
        facts = extract_plan_facts(optimizer_model, result)
    except ModelReconciliationError as error:
        raise SolveServiceError(
            code=ApiErrorCode.MODEL_INVALID,
            message="Solver output failed model reconciliation.",
            details=(
                ApiErrorDetail(
                    path="solver_result",
                    code="MODEL_RECONCILIATION",
                    message=str(error),
                ),
            ),
        ) from error
    if facts.conflicts.count != 0:
        raise SolveServiceError(
            code=ApiErrorCode.MODEL_INVALID,
            message="The policy-constrained plan failed independent conflict reconciliation.",
            details=(
                ApiErrorDetail(
                    path="plans.policy_constrained.metrics.mandatory_policy_conflicts",
                    code="POLICY_CONFLICT",
                    message=f"{facts.conflicts.count} policy conflicts remain",
                ),
            ),
        )
    return facts, result


def _solve_service_error_response(error: SolveServiceError) -> JSONResponse:
    status_code = {
        ApiErrorCode.INVALID_SCENARIO: HTTP_422_UNPROCESSABLE_CONTENT,
        ApiErrorCode.INVALID_POLICY: HTTP_422_UNPROCESSABLE_CONTENT,
        ApiErrorCode.SOLVER_TIMEOUT: HTTP_504_GATEWAY_TIMEOUT,
        ApiErrorCode.NO_FEASIBLE_PLAN: HTTP_409_CONFLICT,
        ApiErrorCode.MODEL_INVALID: HTTP_500_INTERNAL_SERVER_ERROR,
        ApiErrorCode.INTERNAL_ERROR: HTTP_500_INTERNAL_SERVER_ERROR,
    }[error.code]
    return _error_response(error.code, error.message, error.details, status_code)


def _error_response(
    code: ApiErrorCode,
    message: str,
    details: Iterable[ApiErrorDetail],
    status_code: int,
) -> JSONResponse:
    payload = ApiError(
        code=code,
        message=message,
        details=list(details),
    ).model_dump(mode="json")
    return JSONResponse(status_code=status_code, content={"error": payload})


def _request_error_path(location: tuple[Any, ...]) -> str:
    parts = list(location)
    if parts and parts[0] in {"body", "query", "path"}:
        parts.pop(0)
    if not parts:
        return "request"
    result = ""
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result = f"{result}.{part}" if result else str(part)
    return result


def _request_validation_details(errors: Iterable[dict[str, Any]]) -> list[ApiErrorDetail]:
    details: list[ApiErrorDetail] = []
    for error in errors:
        error_type = str(error.get("type", "invalid_value"))
        code = (
            "MISSING_FIELD"
            if error_type == "missing"
            else "UNKNOWN_FIELD"
            if error_type == "extra_forbidden"
            else "INVALID_ENUM"
            if error_type in {"enum", "literal_error"}
            else "INVALID_VALUE"
        )
        details.append(
            ApiErrorDetail(
                path=_request_error_path(tuple(error.get("loc", ()))),
                code=code,
                message=str(error.get("msg", "invalid request value")),
            )
        )
    return details


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    details = _request_validation_details(exception.errors())
    code = (
        ApiErrorCode.INVALID_POLICY
        if details and all(detail.path == "policy" or detail.path.startswith("policy.") for detail in details)
        else ApiErrorCode.INVALID_SCENARIO
    )
    return _error_response(
        code,
        "Request validation failed.",
        details,
        HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(
    _request: Request,
    _exception: ResponseValidationError,
) -> JSONResponse:
    return _error_response(
        ApiErrorCode.INTERNAL_ERROR,
        "The server produced an invalid response.",
        (),
        HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.exception_handler(Exception)
async def internal_exception_handler(
    _request: Request,
    _exception: Exception,
) -> JSONResponse:
    return _error_response(
        ApiErrorCode.INTERNAL_ERROR,
        "The server could not complete the request.",
        (),
        HTTP_500_INTERNAL_SERVER_ERROR,
    )
