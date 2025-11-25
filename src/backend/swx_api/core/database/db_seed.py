"""
Database Seeding Script
------------------------
This script populates the database with initial data, including:
- Superuser creation
- Language translations

Usage:
    Run this script to seed initial data into the database.

Safety Checks:
- Prevents execution in production unless explicitly allowed.

Functions:
- `seed_data()`: Runs database seeding tasks.
- `main()`: Entry point with environment safety check.
"""

import sys

from swx_api.core.config.settings import settings
from swx_api.core.database.db import SessionLocal
from swx_api.core.database.db_setup import init_superuser, seed_languages
from swx_api.core.middleware.logging_middleware import logger

def seed_data() -> None:
    """
    Seeds initial data into the database, such as the superuser and translations.
    Logs errors if seeding fails.
    """
    try:
        with SessionLocal() as session:
            logger.info("Starting database seeding...")
            # init_superuser(session)
            seed_languages(session)
            session.commit()
        logger.info("Initial data successfully created.")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}", exc_info=True)
        print(f"Seeding failed due to: {e}")
        sys.exit(1)  # <-- Triggers the failure in FastAPI



def main() -> None:
    """
    Entry point for database seeding.

    Checks the environment before running to prevent accidental seeding in production.
    """
    if settings.ENVIRONMENT == "production":
        logger.warning("Seeding data in production is disabled for safety!")
        return

    logger.info("Seeding initial data...")
    seed_data()

if __name__ == "__main__":
    main()
