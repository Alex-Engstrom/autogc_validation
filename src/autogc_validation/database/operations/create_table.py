# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 15:34:20 2026

@author: aengstrom
"""
from autogc_validation.database.models import MODEL_REGISTRY
from autogc_validation.database.conn import transaction
import logging

logger = logging.getLogger(__name__)


def create_table(database: str, tablename: str) -> None:
    """
    Create a table in the database.

    Args:
        database: Path to the database file.
        tablename: Name of the table to create (must be in MODEL_REGISTRY).

    Raises:
        ValueError: If tablename is not a recognized model.
    """
    model = MODEL_REGISTRY.get(tablename)
    if model is None:
        raise ValueError(
            f"Unknown table '{tablename}'. "
            f"Valid tables: {', '.join(MODEL_REGISTRY.keys())}"
        )

    try:
        with transaction(database) as conn:
            conn.execute(model.__table_sql__)
            logger.info("Created table %s", tablename)
    except Exception:
        logger.exception("Error creating table %s", tablename)
        raise
