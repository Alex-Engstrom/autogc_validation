# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 15:03:24 2026

@author: aengstrom
"""

import logging
from pathlib import Path
from autogc_validation.database.enums import CanisterType
from autogc_validation.database.models import MODEL_REGISTRY, CanisterTypes
from autogc_validation.database.operations import create_table, insert
from autogc_validation.database.utils.data_loaders import load_standard_voc_data

logger = logging.getLogger(__name__)


def initialize_database(database_path: str, force: bool = False) -> None:
    """
    Initialize database with schema and reference data.
    
    Args:
        database_path: Path to database file
        force: If True, drop existing tables and recreate
    """
    db_path = Path(database_path)
    
    if db_path.exists() and not force:
        logger.warning("Database already exists at %s", db_path)
        raise FileExistsError(
            f"Database exists at {db_path}. Use force=True to overwrite."
        )
    
    if db_path.exists() and force:
        db_path.unlink()
        logger.info("Deleted existing database")
    
    # Create database directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Initializing database at %s", db_path)
    
    # Create tables
    logger.info("Creating tables...")
    for tablename in MODEL_REGISTRY.keys():
        create_table(database=str(db_path), tablename=tablename)
        
    
    # Load and insert VOC reference data
    logger.info("Loading VOC reference data...")
    voc_data = load_standard_voc_data()
    logger.info("Loaded %d VOC compounds", len(voc_data))
    
    logger.info("Inserting VOC data into database...")
    inserted = sum(1 for voc in voc_data if insert(str(db_path), voc))
    logger.info("Inserted %d/%d VOC records", inserted, len(voc_data))

    # Seed canister types
    logger.info("Inserting canister types...")
    for ct in CanisterType:
        insert(str(db_path), CanisterTypes(canister_type=ct))
    logger.info("Inserted %d canister types", len(CanisterType))

    logger.info("Database initialization complete!")

