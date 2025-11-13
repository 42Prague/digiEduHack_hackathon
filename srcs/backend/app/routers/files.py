from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import FileMeta, School

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=FileMeta)
def create_file(
    tus_id: str,
    filename: str,
    school_id: Optional[int] = None,
    session: Session = Depends(get_session),
):
    if school_id is not None:
        school = session.get(School, school_id)
        if not school:
            raise HTTPException(status_code=400, detail="School does not exist")

    file_meta = FileMeta(tus_id=tus_id, filename=filename, school_id=school_id)
    session.add(file_meta)
    session.commit()
    session.refresh(file_meta)
    return file_meta


@router.get("", response_model=List[FileMeta])
def list_files(session: Session = Depends(get_session)):
    return session.exec(select(FileMeta)).all()
