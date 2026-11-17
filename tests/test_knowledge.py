from pathlib import Path

from micro_foundry.knowledge import LocalKnowledgeBase, split_sections, tokens


def test_search_returns_relevant_document(tmp_path: Path) -> None:
    (tmp_path / "policy.md").write_text("Expenses require a receipt above 25 euros.")
    (tmp_path / "other.md").write_text("The garden has green plants.")

    results = LocalKnowledgeBase(tmp_path).search("What receipt is needed for expenses?")

    assert [result.source for result in results] == ["policy.md"]


def test_search_cites_the_matching_section(tmp_path: Path) -> None:
    (tmp_path / "handbook.md").write_text(
        "# Handbook\n\n## Expenses\n\nSubmit expenses within 30 days.\n\n"
        "## Remote work\n\nWork remotely up to three days each week.\n"
    )

    [hit] = LocalKnowledgeBase(tmp_path).search("How many remote days each week?")

    assert hit.citation == "handbook.md#remote-work"
    assert "three days" in hit.text and "30 days" not in hit.text


def test_stop_words_alone_never_match(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("What is the way to do it and how can you have it?")

    assert LocalKnowledgeBase(tmp_path).search("how do you have what") == []
    assert tokens("How do employees submit") == ["employees", "submit"]


def test_split_sections_keeps_intro_under_title() -> None:
    sections = split_sections("# Brief\n\nIntro text.\n\n## Scope\n\nScope text.")
    assert sections == [("", "Intro text."), ("Scope", "Scope text.")]
