from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.heatshift import api


pytestmark = pytest.mark.skipif(
    not api.STATIC_DIR.exists(),
    reason="run `cd frontend && npm run build` before the production static-serving checks",
)


def test_fastapi_serves_spa_routes_assets_and_api_before_fallback() -> None:
    client = TestClient(api.app)

    home = client.get("/")
    direct_route = client.get("/why")
    api_response = client.get("/api/demo")
    fallback = client.get("/fallback/demo.json")
    javascript_asset = next((api.STATIC_DIR / "assets").glob("index-*.js"))
    asset = client.get(f"/assets/{javascript_asset.name}")

    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]
    assert '<div id="root"></div>' in home.text
    assert direct_route.status_code == 200
    assert direct_route.text == home.text
    assert api_response.status_code == 200
    assert api_response.headers["content-type"].startswith("application/json")
    assert api_response.json()["scenario"]["id"] == "demo-city-day-01"
    assert fallback.status_code == 200
    assert fallback.headers["content-type"].startswith("application/json")
    assert fallback.json()["fixture_version"] == "demo-v1"
    assert asset.status_code == 200
    assert "javascript" in asset.headers["content-type"]


def test_unknown_api_paths_do_not_receive_the_spa_shell() -> None:
    response = TestClient(api.app).get("/api/not-a-route")

    assert response.status_code == 404
    assert "text/html" not in response.headers.get("content-type", "")
