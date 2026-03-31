from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_expected_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "Altgramm API"
    assert payload["status"] in {"ok", "degraded"}
    assert payload["database"] in {"online", "offline"}
