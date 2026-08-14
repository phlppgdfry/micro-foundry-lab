from fastapi.testclient import TestClient

from micro_foundry.main import app


def test_health_reports_configuration_state() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "foundry_configured" in response.json()


def test_chat_requires_configuration() -> None:
    response = TestClient(app).post("/v1/chat", json={"question": "What is the expense policy?"})

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
