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

    transcript_text: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})

    # normalized LLM output for easier querying
    analysis_summary_text: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
    analysis_type: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})

    # Flattened structured metadata fields (wide-column friendly)
    school_year: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    date: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
    year: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    month: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    semester: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    intervention: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    intervention_type: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    intervention_detail: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
    target_group: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    participant_name: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
    organization_school: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    school_grade: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    school_type: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    region: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    feedback: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
    overall_satisfaction: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    lecturer_performance_and_skills: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    planned_goals: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    gained_professional_development: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    open_feedback: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
