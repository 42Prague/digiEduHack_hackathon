from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_ratio: float = Field(ge=0.0, le=1.0)
    is_numeric: bool


class DatasetSummary(BaseModel):
    name: str
    classification: str
    row_count: Optional[int] = None
    metrics: Optional[Dict[str, Dict[str, float]]] = None
    themes: Optional[List[str]] = None
    generated_at: str


class IngestionResponse(BaseModel):
    filename: str
    stored_path: str
    normalized_path: str
    classification: str
    row_count: Optional[int] = None
    numeric_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    columns: Optional[List[ColumnProfile]] = None
    summary: DatasetSummary
    summary_path: str
    dq_report_path: Optional[str] = None


class DatasetInfo(BaseModel):
    name: str
    normalized_path: Optional[str]
    summary_path: Optional[str]
    raw_files: List[str]


class SummaryResponse(BaseModel):
    summary: DatasetSummary
    tone: Optional[str] = None


class MetricsResponse(BaseModel):
    total_datasets: int
    quantitative_datasets: int
    qualitative_datasets: int

