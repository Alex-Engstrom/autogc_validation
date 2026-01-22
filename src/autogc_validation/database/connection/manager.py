# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:04:59 2026

@author: aengstrom
"""

"""Database connection utilities - shared across all repos."""
from contextlib import contextmanager
import sqlite3
from autogc_validation.utils.logging_config import get_logger

logger = get_logger(__name__)

@contextmanager
def get_connection(database: str):
    logger.debug("Opening database connection: %s", database)
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    except Exception:
        logger.exception("Unhandled exception during DB connection usage")
    finally:
        conn.close()
        logger.debug("Closed database connection: %s", database)

@contextmanager
def transaction(database: str):
    logger.debug("Starting transaction: %s", database)
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
        logger.debug("Transaction committed: %s", database)
    except Exception:
        conn.rollback()
        logger.warning("Transaction rolled back: %s", database)
        logger.exception("Exception during transaction")
        raise
    finally:
        conn.close()
        logger.debug("Closed database connection: %s", database)