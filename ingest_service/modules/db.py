"""
Database helpers shared across the ingestion service.
"""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required for the ingestion service."
    )

url = make_url(DATABASE_URL)
if url.drivername in {"postgresql", "postgresql+psycopg2"}:
    url = url.set(drivername="postgresql+psycopg")

engine = create_engine(url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db() -> Generator:
    """
    FastAPI dependency that yields a SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
