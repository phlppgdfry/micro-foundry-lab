import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[\w'-]+", re.UNICODE)


@dataclass(frozen=True)
class SourceChunk:
    source: str
    text: str
    score: int


class LocalKnowledgeBase:
    """Tiny, dependency-free retrieval layer for the learning project.

    It deliberately uses transparent keyword scoring. Swap this class for Azure AI Search
    or a vector store once the lab's retrieval and evaluation fundamentals are clear.
    """

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def search(self, query: str, limit: int = 3) -> list[SourceChunk]:
        query_tokens = set(self._tokens(query))
        if not query_tokens or not self.directory.exists():
            return []

        matches: list[SourceChunk] = []
        for path in sorted(self.directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            score = len(query_tokens.intersection(self._tokens(text)))
            if score:
                matches.append(SourceChunk(source=path.name, text=text, score=score))
        return sorted(matches, key=lambda item: (-item.score, item.source))[:limit]

    @staticmethod
    def _tokens(value: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(value)]
