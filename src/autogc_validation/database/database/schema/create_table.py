# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 15:34:20 2026

@author: aengstrom
"""
from .schemas import SCHEMAS
from autogc_validation.database.utils.connection import get_connection
from autogc_validation.utils.logging_config import get_logger

logger = get_logger(__name__)
def create_table(database: str, key: str) -> None:
    try:
        schema = SCHEMAS[key]
        table_name = schema.name
        sql = schema.sql

        with get_connection(database) as conn:
            conn.execute(sql)
            logger.info("Created table %s", table_name)
    except Exception:
        logger.exception("Error creating table %s", key)
        raise