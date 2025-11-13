from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field


class FileDescriptor(BaseModel):
    """
    Description of a data file the agent could use.
    For now your tools return dummy data; later you can plug real metadata in.
    """
    id: str
    name: str
    summary: str
    path: Optional[str] = None


class AnalysisRequest(BaseModel):
    query: str = Field(..., description="Natural language question from the UI.")
    files: List[FileDescriptor] = Field(
        default_factory=list,
        description="Optional list of known files; for now unused by dummy tools."
    )
    language: Optional[str] = Field(
        default="en",
        description="Preferred language of the answer, e.g. 'en' or 'cs'.",
    )
    max_steps: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Optional override for maximum reasoning steps (default from server settings).",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Existing session identifier to continue an analysis conversation.",
    )


class PlotSpec(BaseModel):
    title: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    series: Optional[str] = None
    description: Optional[str] = None  # human-readable description of aggregation logic


class Step(BaseModel):
    type: Literal["llm_call", "tool_call", "final"]
    label: str
    detail: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict] = None


class AnalysisResponse(BaseModel):
    answer: str
    steps: List[Step]
    plot: Optional[PlotSpec] = None
    model: str
    token_usage: Optional[Dict] = None
    session_id: str


class SessionMessage(BaseModel):
    role: Literal["user", "assistant", "tool", "system", "internal"] = "user"
    content: str
    type: Optional[str] = None
    tool_name: Optional[str] = None
    timestamp: Optional[str] = None


class SessionHistory(BaseModel):
    session_id: str
    messages: List[SessionMessage] = Field(default_factory=list)
