from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import AnalysisRequest, AnalysisResponse, SessionHistory
from .agent import run_agent
from .settings import settings
from . import session_store

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
