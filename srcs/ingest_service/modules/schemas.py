"""
Pydantic schemas for API requests and responses.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str
    message: str
    row_index: Optional[int] = Field(default=None)
    column: Optional[str] = Field(default=None)


class AudioResult(BaseModel):
    success: bool
    audio_id: Optional[str] = None
    transcript_length: int = 0
    errors: List[ApiError] = Field(default_factory=list)


class SurveyIngestResult(BaseModel):
    success: bool
    inserted_rows: int = 0
    skipped_rows: int = 0
    errors: List[ApiError] = Field(default_factory=list)


class RawIngestResult(BaseModel):
    success: bool
    raw_id: Optional[str] = None
    has_text: bool = False
    has_table_data: bool = False
    errors: List[ApiError] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
