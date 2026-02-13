# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 13:53:01 2026

@author: aengstrom
"""

from contextlib import contextmanager
from autogc_validation.utils.logging_config import get_logger
from .config import get_connection
logger = get_logger(__name__)

def get_connection(database: str):
    """Internal helper to create configured connection."""
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def connection(database: str):
    logger.debug("Opening database connection: %s", database)
    conn = get_connection(database)
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
    conn = get_connection(database)
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