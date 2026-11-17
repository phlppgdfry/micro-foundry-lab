"""
Regression evaluation: run every case in labs/04-evaluation/cases.json through retrieval and the
configured provider, and fail loudly when an answer regresses.

    MICRO_FOUNDRY_PROVIDER=offline python -m micro_foundry.evals  # free, deterministic
    python -m micro_foundry.evals                                 # Foundry model (costs tokens)
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .config import get_settings
from .foundry import NO_ANSWER, ChatService, build_service
from .knowledge import LocalKnowledgeBase

ROOT = Path(__file__).resolve().parents[2]
DECLINE_MARKERS = (
    "could not find",
    "not in the available",
    "don't know",
    "do not know",
    "no information",
)


@dataclass
class CaseResult:
    question: str
    passed: bool
    answer: str
    checks: list[str] = field(default_factory=list)


def run_case(case: dict, service: ChatService, kb: LocalKnowledgeBase) -> CaseResult:
    sources = kb.search(case["question"])
    answer = service.answer(case["question"], sources)
    checks: list[str] = []
    ok = True
    if expected := case.get("source"):
        found = any(s.citation == expected or s.source == expected for s in sources)
        checks.append(f"{'✓' if found else '✗'} retrieved {expected}")
        ok &= found
    for phrase in case.get("must_include", []):
        hit = phrase.lower() in answer.lower()
        checks.append(f"{'✓' if hit else '✗'} answer contains “{phrase}”")
        ok &= hit
    if case.get("must_decline"):
        declined = answer == NO_ANSWER or any(m in answer.lower() for m in DECLINE_MARKERS)
        checks.append(f"{'✓' if declined else '✗'} declines instead of inventing an answer")
        ok &= declined
    return CaseResult(case["question"], ok, answer, checks)


def run(cases_path: Path = ROOT / "labs/04-evaluation/cases.json") -> list[CaseResult]:
    settings = get_settings()
    service = build_service(settings)
    kb = LocalKnowledgeBase(ROOT / "data")
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    return [run_case(case, service, kb) for case in cases]


def main() -> int:
    results = run()
    print(f"provider: {get_settings().provider}\n")
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'}  {r.question}")
        for check in r.checks:
            print(f"      {check}")
    passed = sum(r.passed for r in results)
    print(f"\n{passed}/{len(results)} cases passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
