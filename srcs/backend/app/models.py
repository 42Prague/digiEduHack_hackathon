from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from datetime import datetime

class Region(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # backref
    schools: list["School"] = Relationship(back_populates="region")


class School(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    region_id: int = Field(foreign_key="region.id")

    region: Optional[Region] = Relationship(back_populates="schools")


class FileMeta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    tus_id: str
    filename: str
    school_id: int

    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # analysis
    analysis_status: str = Field(default="pending")  # "pending" | "processing" | "done" | "failed"
    analysis_started_at: Optional[datetime] = None
    analysis_finished_at: Optional[datetime] = None
    analysis_error: Optional[str] = None

    # raw text (optional, if you want to reuse it)
    extracted_text: Optional[str] = None

    # stats + LLM result (use JSON column)
    basic_stats: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
    llm_summary: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
