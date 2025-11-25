#!/usr/bin/env python3
"""
Create database tables directly using SQLModel.
This script creates all tables defined in the models.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swx_api.core.database.db import engine
from swx_api.core.utils.model import load_all_models
from sqlmodel import SQLModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all tables in the database."""
    try:
        # Load all models
        load_all_models()
        
        logger.info("Creating database tables...")
        logger.info(f"Tables to create: {list(SQLModel.metadata.tables.keys())}")
        
        # Create all tables
        SQLModel.metadata.create_all(engine)
        
        logger.info("✅ Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)

