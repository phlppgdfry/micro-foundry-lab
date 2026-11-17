import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[\w'-]+", re.UNICODE)
HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)

# Small on purpose: just enough that "how long do employees have" does not match every file
# on "how", "do" and "have". Domain words are never stop words.
STOP_WORDS = frozenset(
    """a an and are as at be by can could do does for from has have how i if in is it its may
    me my of on or our should so than that the their them then there these they this to us was
    we what when where which who why will with would you your""".split()
)


@dataclass(frozen=True)
class SourceChunk:
    source: str
    section: str
    text: str
    score: int

    @property
    def citation(self) -> str:
        """`file.md#section-slug`, so a reader can jump to the exact paragraph."""
        slug = re.sub(r"[^a-z0-9]+", "-", self.section.lower()).strip("-")
        return f"{self.source}#{slug}" if slug else self.source


def tokens(value: str) -> list[str]:
    return [t.lower() for t in TOKEN_PATTERN.findall(value) if t.lower() not in STOP_WORDS]


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into (heading, body) sections. Text before the first heading keeps the H1."""
    matches = list(HEADING_PATTERN.finditer(text))
    if not matches:
        return [("", text.strip())]
    sections: list[tuple[str, str]] = []
    title = matches[0].group(2).strip()
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if body:
            heading = match.group(2).strip()
            sections.append((heading if heading != title else "", body))
    return sections


class LocalKnowledgeBase:
    """Tiny, dependency-free retrieval layer for the learning project.

    Transparent keyword scoring over Markdown *sections* (not whole files), with stop words
    and a minimum score. Swap this class for Azure AI Search or a vector store once the lab's
    retrieval and evaluation fundamentals are clear.
    """

    def __init__(self, directory: Path, min_score: int = 2) -> None:
        self.directory = directory
        self.min_score = min_score

    def search(self, query: str, limit: int = 3) -> list[SourceChunk]:
        query_tokens = set(tokens(query))
        if not query_tokens or not self.directory.exists():
            return []

        matches: list[SourceChunk] = []
        for path in sorted(self.directory.glob("*.md")):
            for section, body in split_sections(path.read_text(encoding="utf-8")):
                score = len(query_tokens.intersection(tokens(f"{section} {body}")))
                if score >= self.min_score:
                    matches.append(
                        SourceChunk(source=path.name, section=section, text=body, score=score)
                    )
        return sorted(matches, key=lambda item: (-item.score, item.source, item.section))[:limit]
