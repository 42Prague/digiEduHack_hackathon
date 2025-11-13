from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


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
    tus_id: str = Field(default=None, primary_key=True)
    filename: str

    school_id: Optional[int] = Field(default=None, foreign_key="school.id")
