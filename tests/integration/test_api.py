from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.heatshift import api
from backend.heatshift.models import ApiErrorCode, DemoResponse, DiagnosisResponse, SolveResponse
from backend.heatshift.service import SolveServiceError


FIXTURE_DIR = Path(__file__).parents[2] / "backend" / "heatshift" / "fixtures"


def load_request_payload() -> dict:
    return {
        "scenario": json.loads((FIXTURE_DIR / "scenario.json").read_text(encoding="utf-8")),
        "policy": json.loads((FIXTURE_DIR / "policy.json").read_text(encoding="utf-8")),
        "heat_adjustment_c": 0,
        "time_limit_seconds": 5,
    }


@pytest.fixture()
def client() -> TestClient:
    return TestClient(api.app)


def test_demo_and_healthz_return_contracts(client: TestClient) -> None:
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    response = client.get("/api/demo")
    assert response.status_code == 200
    demo = DemoResponse.model_validate(response.json())
    assert len(demo.scenario.jobs) == 12
    assert len(demo.display_coordinates) == len(demo.scenario.locations)
    assert demo.saved_result_metadata is not None
    assert demo.saved_result_metadata.fixture_version == "demo-v1"


def test_solve_endpoint_returns_canonical_response(client: TestClient) -> None:
    response = client.post("/api/solve", json=load_request_payload())

    assert response.status_code == 200
    solve = SolveResponse.model_validate(response.json())
    assert solve.scenario.heat_adjustment_c == 0
    assert solve.plans.heat_shock is None
    assert solve.plans.policy_constrained.metrics.mandatory_policy_conflicts == 0


def test_diagnose_endpoint_returns_genuine_designated_diagnosis(client: TestClient) -> None:
    payload = load_request_payload()
    payload["job_id"] = "job-bus-route"

    response = client.post("/api/diagnose", json=payload)

    assert response.status_code == 200
    diagnosis = DiagnosisResponse.model_validate(response.json())
    assert diagnosis.job_id == "job-bus-route"
    assert diagnosis.proof_status.value == "INFEASIBLE"
    assert diagnosis.classification.value == "proven_infeasible"


def test_request_validation_uses_common_error_envelope(client: TestClient) -> None:
    payload = load_request_payload()
    payload["unexpected"] = True

    response = client.post("/api/solve", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == ApiErrorCode.INVALID_SCENARIO.value
    assert body["error"]["details"]
    assert all(set(detail) == {"path", "code", "message"} for detail in body["error"]["details"])


def test_cross_reference_errors_are_returned_before_solver(client: TestClient) -> None:
    payload = load_request_payload()
    payload["scenario"]["jobs"][0]["location_id"] = "loc-missing"

    response = client.post("/api/solve", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ApiErrorCode.INVALID_SCENARIO.value
    assert response.json()["error"]["details"][0]["path"] == "jobs[0].location_id"


def test_policy_shape_errors_use_invalid_policy_code(client: TestClient) -> None:
    payload = load_request_payload()
    payload["policy"]["id"] = "not valid"

    response = client.post("/api/solve", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ApiErrorCode.INVALID_POLICY.value


def test_unknown_diagnosis_job_is_rejected_before_solver(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(api.app)

    def fail_if_called(_request: object) -> None:
        raise AssertionError("unknown diagnosis IDs must not reach the solver")

    monkeypatch.setattr(api, "_build_constrained_context", fail_if_called)
    payload = load_request_payload()
    payload["job_id"] = "job-missing"

    response = client.post("/api/diagnose", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["code"] == "UNKNOWN_REFERENCE"


@pytest.mark.parametrize(
    ("error_code", "expected_status"),
    [
        (ApiErrorCode.INVALID_SCENARIO, 422),
        (ApiErrorCode.INVALID_POLICY, 422),
        (ApiErrorCode.SOLVER_TIMEOUT, 504),
        (ApiErrorCode.NO_FEASIBLE_PLAN, 409),
        (ApiErrorCode.MODEL_INVALID, 500),
        (ApiErrorCode.INTERNAL_ERROR, 500),
    ],
)
def test_solve_service_errors_map_to_status_and_envelope(
    monkeypatch: pytest.MonkeyPatch,
    error_code: ApiErrorCode,
    expected_status: int,
) -> None:
    client = TestClient(api.app)

    def fail(_request: object) -> None:
        raise SolveServiceError(code=error_code, message="controlled test failure")

    monkeypatch.setattr(api, "solve_scenario", fail)
    response = client.post("/api/solve", json=load_request_payload())

    assert response.status_code == expected_status
    assert response.json() == {
        "error": {
            "code": error_code.value,
            "message": "controlled test failure",
            "details": [],
        }
    }
