from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, SQLModel
from ..db import get_session
from ..models import FileMeta, School
from ..chat.RAG import RAG

router = APIRouter(prefix="/files", tags=["files"])


class FileMetaCreate(SQLModel):
    tus_id: str
    filename: str
    school_id: Optional[int] = None


@router.post("", response_model=FileMeta)
def create_file(
    payload: FileMetaCreate,
    session: Session = Depends(get_session),
):
    if payload.school_id is not None:
        school = session.get(School, payload.school_id)
        if not school:
            raise HTTPException(status_code=400, detail="School does not exist")

    file_meta = FileMeta(
        tus_id=payload.tus_id,
        filename=payload.filename,
        school_id=payload.school_id,
    )
    session.add(file_meta)
    session.commit()
    session.refresh(file_meta)

    school = session.get(School, payload.school_id)

    rag = RAG()
    rag.add_document(f"/data/uploads/{payload.tus_id}", payload.filename, school, file_meta.uploaded_at)

    return file_meta


@router.get("", response_model=List[FileMeta])
def list_files(session: Session = Depends(get_session)):
    return session.exec(select(FileMeta)).all()


@router.post("/{file_id}/retry", response_model=FileMeta)
def retry_file(
    file_id: int,
    session: Session = Depends(get_session),
):
    file_meta = session.get(FileMeta, file_id)
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")

    # Reset analysis metadata
    file_meta.analysis_status = "pending"
    file_meta.analysis_error = None
    file_meta.analysis_started_at = None
    file_meta.analysis_finished_at = None

    # Optional: clear transcript & llm summary if you want to re-generate everything
    # file_meta.transcript_text = None
    # file_meta.llm_summary = None

    session.add(file_meta)
    session.commit()
    session.refresh(file_meta)

    return file_meta
