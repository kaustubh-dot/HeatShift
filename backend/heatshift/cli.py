"""Command-line entry points for bundled validation and saved solver evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
from typing import Any

import ortools

from .diagnostics import DiagnosisValidationError, diagnose_job
from .metrics import ModelReconciliationError, extract_plan_facts
from .models import ApiErrorCode, ApiErrorDetail, DiagnosisResponse, Policy, Scenario, SolveResponse, SolverStatus
from .optimizer import SOLVER_NUM_SEARCH_WORKERS, SOLVER_RANDOM_SEED, build_optimizer_model, solve_staged
from .patterns import generate_policy_constrained_patterns
from .service import SolveServiceError, solve_scenario
from .validation import ScenarioValidationError, validate_scenario


FIXTURE_VERSION = "demo-v1"
DESIGNATED_DIAGNOSIS_JOB_ID = "job-bus-route"
DEFAULT_TIME_LIMIT_SECONDS = 5.0
CANONICAL_TIME_LIMIT_SECONDS = 30.0
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
SAVED_DIR = FIXTURE_DIR / "saved"
BASE_OUTPUT_FILENAME = "base-solve.json"
HEAT_SHOCK_OUTPUT_FILENAME = "heat-shock.json"
DIAGNOSIS_OUTPUT_FILENAME = f"diagnosis-{DESIGNATED_DIAGNOSIS_JOB_ID}.json"
BUNDLE_OUTPUT_FILENAME = "demo-bundle.json"
RUNTIME_FIELDS_EXCLUDED_FROM_OUTPUT_HASH = ("wall_time_seconds",)


def load_fixtures(fixture_dir: Path = FIXTURE_DIR) -> tuple[Scenario, Policy]:
    """Load the checked-in scenario and policy through their strict models."""

    scenario = Scenario.model_validate(
        json.loads((fixture_dir / "scenario.json").read_text(encoding="utf-8"))
    )
    policy = Policy.model_validate(
        json.loads((fixture_dir / "policy.json").read_text(encoding="utf-8"))
    )
    return scenario, policy


def validate_fixtures(fixture_dir: Path = FIXTURE_DIR) -> list[ApiErrorDetail]:
    """Return semantic fixture issues without invoking the solver."""

    scenario, policy = load_fixtures(fixture_dir)
    return validate_scenario(scenario, policy)


def solve_base_fixture(*, time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS) -> SolveResponse:
    """Solve the bundled service-first and unadjusted constrained plans."""

    scenario, policy = load_fixtures()
    return solve_scenario(
        scenario,
        policy,
        heat_adjustment_c=0,
        time_limit_seconds=time_limit_seconds,
    )


def solve_heat_shock_fixture(*, time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS) -> SolveResponse:
    """Solve the bundled scenario with the declared +2°C adjustment."""

    scenario, policy = load_fixtures()
    return solve_scenario(
        scenario,
        policy,
        heat_adjustment_c=2,
        time_limit_seconds=time_limit_seconds,
    )


def diagnose_designated_job(*, time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS) -> DiagnosisResponse:
    """Run forced-inclusion diagnosis for the fixture's designated deferred job."""

    scenario, policy = load_fixtures()
    issues = validate_scenario(scenario, policy)
    if issues:
        raise SolveServiceError(
            code=ApiErrorCode.INVALID_SCENARIO,
            message="Scenario and policy validation failed.",
            details=tuple(issues),
        )

    patterns = generate_policy_constrained_patterns(scenario, policy)
    optimizer_model = build_optimizer_model(
        scenario,
        policy,
        patterns,
        enforce_policy=True,
    )
    result = solve_staged(optimizer_model, time_limit_seconds)
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

    designated = next(
        (job for job in facts.jobs if job.job_id == DESIGNATED_DIAGNOSIS_JOB_ID),
        None,
    )
    if designated is None:
        raise SolveServiceError(
            code=ApiErrorCode.INVALID_SCENARIO,
            message="The designated diagnosis job is missing from the constrained plan.",
            details=(
                ApiErrorDetail(
                    path="jobs",
                    code="UNKNOWN_REFERENCE",
                    message=f"unknown job ID {DESIGNATED_DIAGNOSIS_JOB_ID!r}",
                ),
            ),
        )
    if designated.served:
        raise SolveServiceError(
            code=ApiErrorCode.MODEL_INVALID,
            message="The designated diagnosis job is served by the constrained fixture plan.",
            details=(
                ApiErrorDetail(
                    path="jobs",
                    code="DESIGNATED_JOB_SERVED",
                    message=f"job ID {DESIGNATED_DIAGNOSIS_JOB_ID!r} is not deferred",
                ),
            ),
        )
    try:
        return diagnose_job(
            scenario,
            policy,
            facts,
            result,
            DESIGNATED_DIAGNOSIS_JOB_ID,
            time_limit_seconds=time_limit_seconds,
        )
    except DiagnosisValidationError as error:
        raise SolveServiceError(
            code=ApiErrorCode.MODEL_INVALID,
            message="Diagnosis failed validation or reconciliation.",
            details=tuple(error.details),
        ) from error


def generate_saved(
    output_dir: Path = SAVED_DIR,
    *,
    time_limit_seconds: float = CANONICAL_TIME_LIMIT_SECONDS,
) -> dict[str, Any]:
    """Generate canonical solver artifacts and a provenance manifest."""

    scenario, policy = load_fixtures()
    issues = validate_scenario(scenario, policy)
    if issues:
        raise SolveServiceError(
            code=ApiErrorCode.INVALID_SCENARIO,
            message="Scenario and policy validation failed.",
            details=tuple(issues),
        )

    base_payload = solve_scenario(
        scenario,
        policy,
        heat_adjustment_c=0,
        time_limit_seconds=time_limit_seconds,
    ).model_dump(mode="json")
    heat_shock_payload = solve_scenario(
        scenario,
        policy,
        heat_adjustment_c=2,
        time_limit_seconds=time_limit_seconds,
    ).model_dump(mode="json")
    diagnosis_payload = diagnose_designated_job(
        time_limit_seconds=time_limit_seconds,
    ).model_dump(mode="json")

    artifact_payloads = {
        BASE_OUTPUT_FILENAME: base_payload,
        HEAT_SHOCK_OUTPUT_FILENAME: heat_shock_payload,
        DIAGNOSIS_OUTPUT_FILENAME: diagnosis_payload,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, payload in artifact_payloads.items():
        _write_json(output_dir / filename, payload)

    manifest = {
        "fixture_version": FIXTURE_VERSION,
        "generated_at": _utc_timestamp(),
        "python_version": platform.python_version(),
        "ortools_version": ortools.__version__,
        "solver_seed": SOLVER_RANDOM_SEED,
        "solver_workers": SOLVER_NUM_SEARCH_WORKERS,
        "time_limit_seconds": time_limit_seconds,
        "designated_diagnosis_job_id": DESIGNATED_DIAGNOSIS_JOB_ID,
        "input_hashes": {
            "scenario.json": _sha256_bytes(
                _canonical_json_bytes(scenario.model_dump(mode="json"))
            ),
            "policy.json": _sha256_bytes(
                _canonical_json_bytes(policy.model_dump(mode="json"))
            ),
        },
        "output_hashes": {
            filename: _sha256_bytes(_canonical_json_bytes(payload))
            for filename, payload in artifact_payloads.items()
        },
        "canonical_hash_excluded_fields": list(RUNTIME_FIELDS_EXCLUDED_FROM_OUTPUT_HASH),
        "canonical_hash_format": "sorted JSON with compact separators and a trailing newline",
    }
    _write_json(output_dir / "manifest.json", manifest)

    bundle = {
        "fixture_version": FIXTURE_VERSION,
        "generated_at": manifest["generated_at"],
        "scenario": scenario.model_dump(mode="json"),
        "policy": policy.model_dump(mode="json"),
        "base_solve": base_payload,
        "heat_shock_solve": heat_shock_payload,
        "diagnoses": {DESIGNATED_DIAGNOSIS_JOB_ID: diagnosis_payload},
        "manifest": manifest,
    }
    _write_json(output_dir / BUNDLE_OUTPUT_FILENAME, bundle)
    return manifest


def canonical_projection(value: Any) -> Any:
    """Return the JSON projection used for deterministic output hashes."""

    if isinstance(value, dict):
        return {
            key: canonical_projection(item)
            for key, item in sorted(value.items())
            if key not in RUNTIME_FIELDS_EXCLUDED_FROM_OUTPUT_HASH
        }
    if isinstance(value, list):
        return [canonical_projection(item) for item in value]
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            canonical_projection(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _error_payload(error: Exception) -> dict[str, Any]:
    if isinstance(error, (SolveServiceError, DiagnosisValidationError, ScenarioValidationError)):
        if isinstance(error, SolveServiceError):
            code = error.code.value
            message = error.message
            details = error.details
        elif isinstance(error, ScenarioValidationError):
            code = ApiErrorCode.INVALID_SCENARIO.value
            message = str(error)
            details = error.issues
        else:
            code = ApiErrorCode.INVALID_SCENARIO.value
            message = str(error)
            details = tuple(error.details)
        return {
            "error": {
                "code": code,
                "message": message,
                "details": [detail.model_dump(mode="json") for detail in details],
            }
        }
    return {
        "error": {
            "code": ApiErrorCode.INTERNAL_ERROR.value,
            "message": "The CLI command failed.",
            "details": [],
        }
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HeatShift bundled evidence commands")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="validate the bundled scenario and policy")
    for name, help_text in (
        ("solve", "solve the base scenario"),
        ("diagnose", "diagnose the designated deferred job"),
        ("solve-heat-shock", "solve the scenario with +2°C heat shock"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--time-limit-seconds", type=float, default=DEFAULT_TIME_LIMIT_SECONDS)
    generate = commands.add_parser("generate-saved", help="generate saved solver artifacts and manifest")
    generate.add_argument("--time-limit-seconds", type=float, default=CANONICAL_TIME_LIMIT_SECONDS)
    generate.add_argument("--output-dir", type=Path, default=SAVED_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            issues = validate_fixtures()
            payload = {
                "valid": not issues,
                "scenario_id": load_fixtures()[0].id,
                "policy_id": load_fixtures()[1].id,
                "issues": [issue.model_dump(mode="json") for issue in issues],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if not issues else 1
        if args.command == "solve":
            payload = solve_base_fixture(time_limit_seconds=args.time_limit_seconds)
            print(json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        if args.command == "diagnose":
            payload = diagnose_designated_job(time_limit_seconds=args.time_limit_seconds)
            print(json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        if args.command == "solve-heat-shock":
            payload = solve_heat_shock_fixture(time_limit_seconds=args.time_limit_seconds)
            print(json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        if args.command == "generate-saved":
            manifest = generate_saved(
                args.output_dir,
                time_limit_seconds=args.time_limit_seconds,
            )
            print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
    except Exception as error:  # CLI boundary: keep failures structured and traceback-free.
        print(json.dumps(_error_payload(error), ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
