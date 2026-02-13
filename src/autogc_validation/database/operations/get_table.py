# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:25:38 2026

@author: aengstrom
"""
from dataclasses import fields
from typing import Optional
from autogc_validation.database.models import MODEL_REGISTRY
from autogc_validation.database.conn import connection
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def get_table(database: str, tablename: str, order_by: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Retrieve a full table as a DataFrame.

    Args:
        database: Path to the database file.
        tablename: Name of the table to query (must be in MODEL_REGISTRY).
        order_by: Optional list of column names to sort by.

    Returns:
        DataFrame containing all rows from the table.

    Raises:
        ValueError: If tablename is not recognized or order_by contains invalid columns.
    """
    model = MODEL_REGISTRY.get(tablename)
    if model is None:
        raise ValueError(
            f"Unknown table '{tablename}'. "
            f"Valid tables: {', '.join(MODEL_REGISTRY.keys())}"
        )

    if order_by:
        valid_columns = {f.name for f in fields(model)}
        invalid = [col for col in order_by if col not in valid_columns]
        if invalid:
            raise ValueError(
                f"Invalid column(s) for {tablename}: {', '.join(invalid)}. "
                f"Valid columns: {', '.join(valid_columns)}"
            )
        sql = f"""SELECT * FROM {tablename} ORDER BY {", ".join(order_by)}"""
    else:
        sql = f"""SELECT * FROM {tablename}"""

    with connection(database) as conn:
        return pd.read_sql_query(sql, conn)
