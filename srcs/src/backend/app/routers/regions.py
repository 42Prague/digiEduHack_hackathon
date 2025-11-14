from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Region

router = APIRouter(prefix="/regions", tags=["regions"])


@router.post("", response_model=Region)
def create_region(region: Region, session: Session = Depends(get_session)):
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


@router.get("", response_model=List[Region])
def list_regions(session: Session = Depends(get_session)):
    return session.exec(select(Region)).all()


@router.get("/{region_id}", response_model=Region)
def get_region(region_id: int, session: Session = Depends(get_session)):
    region = session.get(Region, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.put("/{region_id}", response_model=Region)
def update_region(region_id: int, data: Region, session: Session = Depends(get_session)):
    region = session.get(Region, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    region.name = data.name
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


@router.delete("/{region_id}")
def delete_region(region_id: int, session: Session = Depends(get_session)):
    from ..models import School  # avoid circular import

    region = session.get(Region, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    # prevent deleting region if schools exist (simpler for now)
    has_schools = session.exec(
        select(School).where(School.region_id == region_id)
    ).first()
    if has_schools:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete region with schools assigned. Remove or reassign schools first.",
        )

    session.delete(region)
    session.commit()
    return {"ok": True}
