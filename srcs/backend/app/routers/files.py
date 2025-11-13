from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, SQLModel, Field
from ..db import get_session
from ..models import FileMeta, School

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
    return file_meta


@router.get("", response_model=List[FileMeta])
def list_files(session: Session = Depends(get_session)):
    return session.exec(select(FileMeta)).all()
