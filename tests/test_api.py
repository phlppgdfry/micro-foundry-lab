from fastapi.testclient import TestClient

import micro_foundry.main as main
from micro_foundry.config import Settings


def test_health_reports_configuration_state() -> None:
    response = TestClient(main.app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "foundry_configured" in response.json()


def test_chat_requires_configuration(monkeypatch) -> None:
    monkeypatch.setattr(main, "settings", Settings(foundry_project_endpoint=None))

    response = TestClient(main.app).post(
        "/v1/chat", json={"question": "What is the expense policy?"}
    )

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
