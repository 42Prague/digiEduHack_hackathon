from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import AnalysisRequest, AnalysisResponse
from .agent import run_agent
from .settings import settings

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


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """
    Main endpoint used by the frontend/backend.
    - Receives a natural language query (+ optional file descriptors).
    - Runs an agent with tool calling against Azure OpenAI Responses API.
    - Returns a short answer + execution steps + optional plot spec.
    """
    return run_agent(request)
