import os
from sqlmodel import SQLModel, create_engine, Session

# SQLite file is in /data/app.db inside container, i.e. ./data/app.db on host
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/app.db")

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    # ensure models are imported so metadata is filled
    from . import models  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
