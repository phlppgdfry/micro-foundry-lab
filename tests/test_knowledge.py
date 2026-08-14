from pathlib import Path

from micro_foundry.knowledge import LocalKnowledgeBase


def test_search_returns_relevant_document(tmp_path: Path) -> None:
    (tmp_path / "policy.md").write_text("Expenses require a receipt above 25 euros.")
    (tmp_path / "other.md").write_text("The garden has green plants.")

    results = LocalKnowledgeBase(tmp_path).search("What receipt is needed for expenses?")

    assert [result.source for result in results] == ["policy.md"]
