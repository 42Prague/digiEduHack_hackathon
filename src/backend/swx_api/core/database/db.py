"""
Database Connection Module
--------------------------
This module establishes the database connection, manages sessions,
and provides dependency injection for FastAPI routes.

Key Components:
- `engine`: SQLAlchemy engine for database connection.
- `SessionLocal`: Session factory for handling transactions.
- `get_db()`: FastAPI dependency for database sessions.
- `log_sql_execute()`: Logs executed SQL queries.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import event, Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

from swx_api.core.config.settings import settings
from swx_api.core.middleware.logging_middleware import logger

# Create the database engine with connection pooling
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=False,  # Disables verbose SQL logging for performance
    pool_size=20,  # Maintain up to 20 active connections
    max_overflow=10,  # Allow up to 10 extra connections when needed
)

# Session factory for creating new database sessions
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database session management in FastAPI.

    Yields:
        Session: A new database session that is automatically closed after use.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Log all executed SQL queries for debugging purposes
@event.listens_for(Engine, "before_cursor_execute")
def log_sql_execute(conn, cursor, statement, parameters, context, executemany):
    """
    SQLAlchemy event listener to log SQL queries before execution.

    Args:
        conn: Database connection.
        cursor: Database cursor.
        statement (str): The SQL statement being executed.
        parameters (tuple): Query parameters.
        context: Execution context.
        executemany: Boolean indicating batch execution.
    """
    logger.debug(f"SQL QUERY: {statement} | Params: {parameters}")

# FastAPI Dependency Injection for session usage in routes
SessionDep = Annotated[Session, Depends(get_db)]
