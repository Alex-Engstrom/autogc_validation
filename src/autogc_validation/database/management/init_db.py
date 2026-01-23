# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 15:03:24 2026

@author: aengstrom
"""

import logging
from pathlib import Path
from ..models.registry import MODEL_REGISTRY
from ..operations.create_table import create_table
from ..operations import voc_info
from ..utils.data_loaders import load_standard_voc_data

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
        logger.warning(f"Database already exists at {db_path}")
        raise FileExistsError(
            f"Database exists at {db_path}. Use force=True to overwrite."
        )
    
    if db_path.exists() and force:
        db_path.unlink()
        logger.info("Deleted existing database")
    
    # Create database directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing database at {db_path}")
    
    # Create tables
    logger.info("Creating tables...")
    for tablename in MODEL_REGISTRY.keys():
        create_table(database = database_path, tablename = tablename)
        
    
    # Load and insert VOC reference data
    logger.info("Loading VOC reference data...")
    voc_data = load_standard_voc_data()
    logger.info(f"Loaded {len(voc_data)} VOC compounds")
    
    logger.info("Inserting VOC data into database...")
    count = voc_info.bulk_insert(str(db_path), voc_data)
    logger.info(f"Inserted {count} VOC records")
    
    logger.info("Database initialization complete!")

