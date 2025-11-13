from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, UploadFile
from sqlalchemy.orm import Session

from modules import audio_module, raw_module, survey_module
from modules.db import Base, engine, get_db
from modules.schemas import (
    AudioResult,
    HealthResponse,
    RawIngestResult,
    SurveyIngestResult,
)

# Ensure models are registered
from modules import models_db  # noqa: F401

DATA_DIR = Path(os.getenv("INGEST_DATA_DIR", Path(__file__).resolve().parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Ingestion Service", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/audio/upload", response_model=AudioResult)
async def upload_audio(
    file: UploadFile = File(...),
    teacher_id: Optional[int] = Form(default=None),
    workshop_id: Optional[int] = Form(default=None),
    db: Session = Depends(get_db),
) -> AudioResult:
    return await audio_module.handle_audio_upload(
        upload_file=file,
        db=db,
        base_dir=DATA_DIR,
        teacher_id=teacher_id,
        workshop_id=workshop_id,
    )


@app.post("/survey/ingest", response_model=SurveyIngestResult)
async def ingest_survey(
    file: UploadFile = File(...),
    workshop_id: Optional[int] = Form(default=None),
    db: Session = Depends(get_db),
) -> SurveyIngestResult:
    file_bytes = await file.read()
    return survey_module.process_survey_file(
        file_bytes=file_bytes,
        filename=file.filename or "survey.csv",
        workshop_id=workshop_id,
        db=db,
    )


@app.post("/raw/ingest", response_model=RawIngestResult)
async def ingest_raw(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Form(default=None),
    teacher_id: Optional[int] = Form(default=None),
    workshop_id: Optional[int] = Form(default=None),
    db: Session = Depends(get_db),
) -> RawIngestResult:
    file_bytes = await file.read()
    return raw_module.ingest_raw_file(
        file_bytes=file_bytes,
        filename=file.filename or "document.bin",
        doc_type=doc_type,
        teacher_id=teacher_id,
        workshop_id=workshop_id,
        db=db,
        base_dir=DATA_DIR,
    )
