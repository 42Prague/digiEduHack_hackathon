"""
Database Setup & Migrations
---------------------------
This script ensures the database is correctly set up by:
1. Checking if the database is ready.
2. Running Alembic migrations to set up schema.
3. Creating the initial superuser.
4. Seeding language translations.

Key Functions:
- `check_db_ready()`: Waits until the database is available.
- `run_alembic_migrations()`: Runs database schema migrations.
- `init_superuser()`: Ensures a superuser exists.
- `seed_languages()`: Adds initial translations from a JSON file.
- `setup_database()`: Runs the full database setup process.
"""

import json
import subprocess
import logging
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from swx_api.core.config.settings import settings
from swx_api.core.database.db import SessionLocal
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.models.language import Language
from swx_api.core.models.user import User, UserCreate
from swx_api.core.repositories.user_repository import create_user

# Retry settings for ensuring database readiness
max_tries = 60 * 5  # Retries up to 5 minutes
wait_seconds = 1

# Path to the translations JSON file
TRANSLATIONS_FILE = "swx_api/core/database/languages.json"


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def check_db_ready() -> None:
    """
    Ensures the database is ready before starting services.

    Retries for a maximum of `max_tries` attempts, waiting `wait_seconds` between each attempt.

    Raises:
        Exception: If the database is not ready after all attempts.
    """
    try:
        with SessionLocal() as session:
            session.exec(select(1))  # Run a simple test query
    except Exception as e:
        logger.error(f"Database is not ready: {e}")
        raise e


def run_alembic_migrations() -> None:
    """
    Runs Alembic migrations to set up the database schema.

    This function executes `alembic upgrade head` to apply the latest migrations.

    Raises:
        subprocess.CalledProcessError: If the Alembic migration fails.
    """
    logger.info("Running Alembic migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Alembic migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Alembic migration failed: {e}")
        raise


def init_superuser(session: Session) -> None:
    """
    Ensures a superuser exists in the database.

    If no superuser is found, one is created using `settings.FIRST_SUPERUSER`.

    Args:
        session (Session): Active database session.

    Logs:
        - Superuser creation status.
    """
    superuser_email = settings.FIRST_SUPERUSER
    existing_user = session.exec(select(User).where(User.email == superuser_email)).first()

    if not existing_user:
        user_in = UserCreate(
            email=superuser_email,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        create_user(session=session, user_create=user_in)
        session.commit()
        logger.info(f"Superuser '{superuser_email}' created.")
    else:
        logger.info("Superuser already exists. No changes made.")


def seed_languages(session: Session) -> None:
    """
    Seeds translations from the JSON file into the database.

    If a translation entry does not exist in the database, it is added.

    Args:
        session (Session): Active database session.

    Raises:
        Exception: If the file is missing or seeding fails.
    """
    logger.info("Seeding languages from JSON file...")
    try:
        with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as file:
            languages = json.load(file)

        for lang in languages:
            existing = session.exec(
                select(Language).where(
                    Language.language_code == lang["language_code"],
                    Language.key == lang["key"],
                )
            ).first()
            if not existing:
                session.add(Language(**lang))

        session.commit()
        logger.info("Translations seeded successfully.")
    except FileNotFoundError:
        logger.error(f"Translation file {TRANSLATIONS_FILE} not found.")
    except json.JSONDecodeError:
        logger.error("Error decoding JSON file.")
    except Exception as e:
        logger.error(f"Failed to seed translations: {e}")


def setup_database() -> None:
    """
    Runs the full database setup process.

    Steps:
    1. Ensures database readiness.
    2. Runs Alembic migrations.
    3. Creates a superuser (if not exists).
    4. Seeds translations.

    Logs:
        - Database readiness status.
        - Migration success or failure.
        - Superuser status.
        - Translation seeding status.
    """
    logger.info("Checking database readiness...")
    check_db_ready()

    # Step 1: Run Alembic migrations
    run_alembic_migrations()

    # Step 2: Initialize superuser and seed translations
    with SessionLocal() as session:
        # init_superuser(session)
        seed_languages(session)

    logger.info("Database is ready and initialized!")


if __name__ == "__main__":
    setup_database()
