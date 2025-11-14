from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..db import get_session
from ..models import School, Region

router = APIRouter(prefix="/schools", tags=["schools"])


@router.post("", response_model=School)
def create_school(
    school: School,
    session: Session = Depends(get_session),
):
    # ensure region exists
    region = session.get(Region, school.region_id)
    if not region:
        raise HTTPException(status_code=400, detail="Region does not exist")

    session.add(school)
    session.commit()
    session.refresh(school)
    return school


@router.get("", response_model=List[School])
def list_schools(
    region_id: Optional[int] = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(School)
    if region_id is not None:
        statement = statement.where(School.region_id == region_id)
    return session.exec(statement).all()


@router.get("/{school_id}", response_model=School)
def get_school(school_id: int, session: Session = Depends(get_session)):
    school = session.get(School, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.put("/{school_id}", response_model=School)
def update_school(
    school_id: int,
    data: School,
    session: Session = Depends(get_session),
):
    school = session.get(School, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    # if region_id changes, check new region exists
    if data.region_id != school.region_id:
        new_region = session.get(Region, data.region_id)
        if not new_region:
            raise HTTPException(status_code=400, detail="New region does not exist")

    school.name = data.name
    school.region_id = data.region_id
    session.add(school)
    session.commit()
    session.refresh(school)
    return school


@router.delete("/{school_id}")
def delete_school(school_id: int, session: Session = Depends(get_session)):
    school = session.get(School, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    session.delete(school)
    session.commit()
    return {"ok": True}
