# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:04:59 2026

@author: aengstrom
"""

"""Database connection utilities - shared across all repos."""
from contextlib import contextmanager
import sqlite3

@contextmanager
def get_connection(database: str):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def transaction(database: str):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()