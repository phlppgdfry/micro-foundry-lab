"""
Lab 02: treat model output as untrusted data.

    python labs/02-structured-output/structured.py            # asks your Foundry model
    python labs/02-structured-output/structured.py --offline  # validates two canned replies

The lesson is in `parse_review`: JSON that *looks* right is still rejected unless every field
has the right type and shape. Only validated objects reach application code.
"""

import json
import os
import sys

from pydantic import BaseModel, Field, ValidationError


class DocumentReview(BaseModel):
    summary: str = Field(min_length=10, max_length=400)
    risks: list[str] = Field(max_length=5)
    next_actions: list[str] = Field(min_length=1, max_length=5)


PROMPT = """Review the expense policy below. Reply with JSON only, using exactly these keys:
summary (string), risks (list of strings), next_actions (list of strings).

Policy: Employees may submit reasonable business expenses within 30 days. Include a receipt
for purchases above €25."""


def parse_review(raw: str) -> DocumentReview:
    """Strip an accidental ```json fence, then validate; raise ValueError with a clear reason."""
    text = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return DocumentReview.model_validate_json(text)
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or 'body'}: {e['msg']}" for e in error.errors()
        )
        raise ValueError(f"Model output rejected: {problems}") from error


CANNED = {
    "valid": json.dumps({
        "summary": "Expenses must be submitted within 30 days, with receipts above €25.",
        "risks": ["Late claims are lost", "Missing receipts delay reimbursement"],
        "next_actions": ["Add a reminder at day 25"],
    }),
    "looks fine, is not": '{"summary": "OK", "risks": "none", "next_actions": []}',
}


def main() -> None:
    if "--offline" in sys.argv:
        for label, raw in CANNED.items():
            try:
                print(f"[{label}] accepted →", parse_review(raw).model_dump())
            except ValueError as error:
                print(f"[{label}] {error}")
        return

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from dotenv import load_dotenv

    load_dotenv()
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    raw = project.get_openai_client().responses.create(
        model=os.getenv("FOUNDRY_MODEL", "gpt-5-mini"), input=PROMPT
    ).output_text
    print(parse_review(raw).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
