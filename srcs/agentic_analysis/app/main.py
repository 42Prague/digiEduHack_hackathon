from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    AnalysisRequest,
    AnalysisResponse,
    SessionHistory,
    SummaryRequest,
    SummaryResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from .agent import run_agent
from .settings import settings
from . import session_store
from .azure_client import client
from .embeddings import embed_text, EMBEDDING_MODEL_NAME

app = FastAPI(
    title="EduScale LLM Analysis Service",
    description="Agentic natural-language analysis layer using Azure OpenAI.",
    version="0.1.0",
)

# Simple CORS for your frontend; tweak origins as needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": settings.azure_openai_model}


@app.post("/fancy_analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """
    Main endpoint used by the frontend/backend.
    - Receives a natural language query (+ optional file descriptors).
    - Runs an agent with tool calling against Azure OpenAI Responses API.
    - Returns a short answer + execution steps + optional plot spec.
    """
    session_id = request.session_id or str(uuid4())
    sessions = session_store.list_sessions()

    if request.session_id:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        existing_messages = sessions[session_id].get("messages", [])
    else:
        session_store.ensure_session(session_id)
        existing_messages = []

    # Update request model so downstream logic can treat it as existing session.
    request.session_id = session_id

    return run_agent(
        request,
        session_id=session_id,
        existing_messages=existing_messages,
    )


@app.get("/session/{session_id}", response_model=SessionHistory)
def get_session(session_id: str) -> SessionHistory:
    sessions = session_store.list_sessions()
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    return SessionHistory(session_id=session_id, messages=session.get("messages", []))


@app.post("/summarize", response_model=SummaryResponse)
def summarize(request: SummaryRequest) -> SummaryResponse:
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")
    if len(text) > 8000:
        raise HTTPException(status_code=400, detail="Text is too long to summarize in one call.")

    language = request.language or "en"

    response = client.responses.create(
        model=settings.azure_openai_model,
        instructions=(
            "You are a helpful assistant that writes a single concise paragraph summarizing the provided text. "
            "The output must be under 20 words, and be in the requested language."
        ),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Target language: {language}\n\nSource text:\n{text}",
                    }
                ],
            }
        ],
    )

    summary = getattr(response, "output_text", None)
    if not summary:
        pieces = []
        for output in getattr(response, "output", []) or []:
            if getattr(output, "type", None) == "message":
                for item in getattr(output, "content", []) or []:
                    text_piece = getattr(item, "text", None)
                    if text_piece:
                        pieces.append(text_piece)
        summary = "\n".join(pieces)

    summary = summary.strip()
    if not summary:
        raise HTTPException(status_code=502, detail="Model did not return a summary.")

    usage = getattr(response, "usage", None)
    token_usage = None
    if usage is not None:
        token_usage = {
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            "total_tokens": getattr(usage, "total_tokens", 0) or 0,
        }

    return SummaryResponse(summary=summary, model=settings.azure_openai_model, token_usage=token_usage)


@app.post("/embed", response_model=EmbeddingResponse)
def embed(request: EmbeddingRequest) -> EmbeddingResponse:
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    vector = embed_text(text)
    return EmbeddingResponse(embedding=vector, model=EMBEDDING_MODEL_NAME)
