from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from micro_foundry.config import get_settings
from micro_foundry.foundry import build_service
from micro_foundry.knowledge import LocalKnowledgeBase, SourceChunk

ROOT = Path(__file__).resolve().parents[2]
PAGE = Path(__file__).with_name("static") / "index.html"
DATA_DIRECTORY = ROOT / "data"
settings = get_settings()

app = FastAPI(
    title="Micro Foundry Lab",
    version="0.1.0",
    description="A transparent, learning-first Microsoft Foundry document assistant.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4_000, examples=["What is the refund policy?"])


class Citation(BaseModel):
    source: str
    section: str = ""
    anchor: str = Field(description="file.md#section, for linking to the exact paragraph")
    relevance: int
    excerpt: str = Field(description="The retrieved text, so the answer can be checked")


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    provider: str


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "foundry_configured": bool(settings.foundry_project_endpoint),
        "model": settings.foundry_model,
        "provider": settings.provider,
    }


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def page() -> str:
    """A minimal page to ask questions and inspect citations (Swagger stays at /docs)."""
    return PAGE.read_text(encoding="utf-8")


@app.get("/favicon.svg", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(PAGE.with_name("favicon.svg"), media_type="image/svg+xml")


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    sources: list[SourceChunk] = LocalKnowledgeBase(DATA_DIRECTORY).search(request.question)
    try:
        service = build_service(settings)
        answer = service.answer(request.question, sources)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:  # Azure SDK errors are intentionally not exposed to callers.
        raise HTTPException(
            status_code=502, detail="The Foundry request failed. Check server logs."
        ) from error

    return ChatResponse(
        answer=answer,
        citations=[
            Citation(
                source=item.source,
                section=item.section,
                anchor=item.citation,
                relevance=item.score,
                excerpt=item.text,
            )
            for item in sources
        ],
        provider=service.name,
    )
