import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint_returns_standard_response(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "service is healthy"
    assert payload["data"] == {
        "status": "healthy",
        "service": "tuoke-agent-backend",
    }


def test_health_endpoint_method_not_allowed_returns_standard_error_envelope(client: TestClient) -> None:
    response = client.post("/api/v1/health")

    assert response.status_code == 405
    payload = response.json()
    assert payload["code"] == "METHOD_NOT_ALLOWED"
    assert payload["message"]
    assert payload["data"] is None
