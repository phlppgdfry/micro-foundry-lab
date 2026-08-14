from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from micro_foundry.config import get_settings
from micro_foundry.foundry import FoundryChatService
from micro_foundry.knowledge import LocalKnowledgeBase, SourceChunk

ROOT = Path(__file__).resolve().parents[2]
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
    relevance: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "foundry_configured": bool(settings.foundry_project_endpoint),
        "model": settings.foundry_model,
    }


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    sources: list[SourceChunk] = LocalKnowledgeBase(DATA_DIRECTORY).search(request.question)
    try:
        answer = FoundryChatService(settings).answer(request.question, sources)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:  # Azure SDK errors are intentionally not exposed to callers.
        raise HTTPException(
            status_code=502, detail="The Foundry request failed. Check server logs."
        ) from error

    return ChatResponse(
        answer=answer,
        citations=[Citation(source=item.source, relevance=item.score) for item in sources],
    )
