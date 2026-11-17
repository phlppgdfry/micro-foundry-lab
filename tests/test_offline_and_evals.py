from fastapi.testclient import TestClient

import micro_foundry.main as main
from micro_foundry.config import Settings
from micro_foundry.evals import run
from micro_foundry.foundry import NO_ANSWER, OfflineExtractiveService


def test_offline_api_answers_with_section_citations(monkeypatch) -> None:
    monkeypatch.setattr(main, "settings", Settings(MICRO_FOUNDRY_PROVIDER="offline"))

    body = TestClient(main.app).post(
        "/v1/chat", json={"question": "How long do employees have to submit expenses?"}
    ).json()

    assert body["provider"] == "offline-extractive"
    assert "30 days" in body["answer"]
    assert body["citations"][0]["anchor"] == "employee-handbook.md#expenses"
    assert body["citations"][0]["excerpt"]


def test_offline_declines_without_sources() -> None:
    assert OfflineExtractiveService().answer("What is the parental leave policy?", []) == NO_ANSWER


def test_web_page_is_served() -> None:
    response = TestClient(main.app).get("/")
    assert response.status_code == 200
    assert "Ask the documents" in response.text


def test_regression_cases_pass_on_the_offline_baseline(monkeypatch) -> None:
    monkeypatch.setenv("MICRO_FOUNDRY_PROVIDER", "offline")
    from micro_foundry.config import get_settings

    get_settings.cache_clear()
    try:
        results = run()
    finally:
        get_settings.cache_clear()
    assert all(r.passed for r in results), [(r.question, r.checks) for r in results if not r.passed]
