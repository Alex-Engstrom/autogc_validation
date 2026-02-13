# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:02:07 2026

@author: aengstrom
"""
import sqlite3
from enum import Enum
from dataclasses import fields
from autogc_validation.database.conn import transaction
from autogc_validation.utils.logging_config import get_logger
from autogc_validation.database.models import MODELS

logger = get_logger(__name__)


def insert(database: str, obj) -> bool:
    """
    Insert a model instance into the database.

    Args:
        database: Path to the database file.
        obj: A model instance to insert.

    Returns:
        True if the row was inserted, False if it was a duplicate.

    Raises:
        TypeError: If obj is not a recognized model type.
        AttributeError: If obj is missing __tablename__.
    """
    if type(obj) not in MODELS:
        raise TypeError(
            f"Expected one of ({', '.join(cls.__name__ for cls in MODELS)}), "
            f"got {type(obj).__name__}"
        )

    table = getattr(obj, "__tablename__", None)
    if table is None:
        raise AttributeError("Dataclass missing __tablename__")

    columns = [f.name for f in fields(obj)]
    values = [
        v.value if isinstance(v, Enum) else v
        for v in (getattr(obj, col) for col in columns)
    ]

    sql = f"""
    INSERT INTO {table}
    ({", ".join(columns)})
    VALUES ({", ".join("?" for _ in columns)})
    """

    with transaction(database) as conn:
        try:
            conn.execute(sql, values)
            return True
        except sqlite3.IntegrityError as e:
            logger.warning("Duplicate entry skipped for %s: %s", table, e)
            return False
