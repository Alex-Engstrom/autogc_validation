# -*- coding: utf-8 -*-
"""
Delete operations for the AutoGC validation database.

Provides hard deletion of erroneous records. Use retire_site_canister
and retire_mdl in update.py for intentional end-of-life records.
"""
from dataclasses import fields
from enum import Enum

import logging

from autogc_validation.database.conn import transaction, connection
from autogc_validation.database.models import MODELS

logger = logging.getLogger(__name__)


def delete(database: str, obj) -> bool:
    """Delete a record from the database by exact match on all fields.

    Intended for removing erroneously inserted records. To retire a
    still-valid record (e.g. a replaced canister or superseded MDL),
    use retire_site_canister or retire_mdl instead.

    The recommended workflow:
        1. Call get_table() to inspect records and identify the bad one.
        2. Construct the matching model instance.
        3. Pass it to delete().

    Args:
        database: Path to the database file.
        obj: A model instance exactly matching the record to delete.

    Returns:
        True if a record was deleted, False if no matching record was found.

    Raises:
        TypeError: If obj is not a recognised model type.
    """
    if type(obj) not in MODELS:
        raise TypeError(
            f"Expected one of ({', '.join(cls.__name__ for cls in MODELS)}), "
            f"got {type(obj).__name__}"
        )

    table = obj.__tablename__
    all_fields = fields(obj)

    # Build WHERE clause handling NULL fields explicitly
    conditions = []
    values = []
    for f in all_fields:
        raw = getattr(obj, f.name)
        value = raw.value if isinstance(raw, Enum) else raw
        if value is None:
            conditions.append(f"{f.name} IS NULL")
        else:
            conditions.append(f"{f.name} = ?")
            values.append(value)

    sql = f"DELETE FROM {table} WHERE {' AND '.join(conditions)}"

    # Check the record exists before attempting deletion
    check_sql = f"SELECT 1 FROM {table} WHERE {' AND '.join(conditions)}"
    with connection(database) as conn:
        row = conn.execute(check_sql, values).fetchone()

    if row is None:
        logger.warning("No matching record found in %s — nothing deleted", table)
        return False

    with transaction(database) as conn:
        conn.execute(sql, values)
        logger.info("Deleted record from %s: %s", table, {f.name: getattr(obj, f.name) for f in all_fields})

    return True
