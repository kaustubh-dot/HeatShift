from __future__ import annotations

import json
from pathlib import Path

from backend.heatshift.cli import (
    BASE_OUTPUT_FILENAME,
    BUNDLE_OUTPUT_FILENAME,
    CANONICAL_TIME_LIMIT_SECONDS,
    DESIGNATED_DIAGNOSIS_JOB_ID,
    DIAGNOSIS_OUTPUT_FILENAME,
    HEAT_SHOCK_OUTPUT_FILENAME,
    SAVED_DIR,
    canonical_projection,
    generate_saved,
)
from backend.heatshift.models import DiagnosisResponse, Policy, Scenario, SolveResponse


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def comparable(value: object) -> object:
    projected = canonical_projection(value)
    if isinstance(projected, dict):
        return {
            key: comparable(item)
            for key, item in projected.items()
            if key != "generated_at"
        }
    if isinstance(projected, list):
        return [comparable(item) for item in projected]
    return projected


def test_saved_generation_is_contract_shaped_and_canonically_deterministic(tmp_path: Path) -> None:
    generated_dir = tmp_path / "generated"
    generated_manifest = generate_saved(generated_dir)

    assert generated_manifest["fixture_version"] == "demo-v1"
    assert generated_manifest["designated_diagnosis_job_id"] == DESIGNATED_DIAGNOSIS_JOB_ID
    assert generated_manifest["canonical_hash_excluded_fields"] == ["wall_time_seconds"]
    assert generated_manifest["time_limit_seconds"] == CANONICAL_TIME_LIMIT_SECONDS
    committed_manifest = read_json(SAVED_DIR / "manifest.json")
    assert generated_manifest["input_hashes"] == committed_manifest["input_hashes"]
    assert generated_manifest["output_hashes"] == committed_manifest["output_hashes"]

    for filename in (
        BASE_OUTPUT_FILENAME,
        HEAT_SHOCK_OUTPUT_FILENAME,
        DIAGNOSIS_OUTPUT_FILENAME,
        "manifest.json",
        BUNDLE_OUTPUT_FILENAME,
    ):
        assert comparable(read_json(generated_dir / filename)) == comparable(read_json(SAVED_DIR / filename))

    base = SolveResponse.model_validate(read_json(generated_dir / BASE_OUTPUT_FILENAME))
    heat_shock = SolveResponse.model_validate(read_json(generated_dir / HEAT_SHOCK_OUTPUT_FILENAME))
    diagnosis = DiagnosisResponse.model_validate(read_json(generated_dir / DIAGNOSIS_OUTPUT_FILENAME))
    bundle = read_json(generated_dir / BUNDLE_OUTPUT_FILENAME)

    assert base.scenario.heat_adjustment_c == 0
    assert base.plans.heat_shock is None
    assert heat_shock.scenario.heat_adjustment_c == 2
    assert heat_shock.plans.heat_shock is not None
    assert diagnosis.job_id == DESIGNATED_DIAGNOSIS_JOB_ID
    assert set(bundle) == {
        "fixture_version",
        "generated_at",
        "scenario",
        "policy",
        "base_solve",
        "heat_shock_solve",
        "diagnoses",
        "manifest",
    }
    Scenario.model_validate(bundle["scenario"])
    Policy.model_validate(bundle["policy"])
    assert SolveResponse.model_validate(bundle["base_solve"]) == base
    assert SolveResponse.model_validate(bundle["heat_shock_solve"]) == heat_shock
    assert DiagnosisResponse.model_validate(bundle["diagnoses"][DESIGNATED_DIAGNOSIS_JOB_ID]) == diagnosis
