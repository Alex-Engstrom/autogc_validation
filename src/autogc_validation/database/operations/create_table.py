# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 15:34:20 2026

@author: aengstrom
"""
from autogc_validation.database.models import MODEL_REGISTRY
from autogc_validation.database.conn import connection
from autogc_validation.utils.logging_config import get_logger

logger = get_logger(__name__)
def create_table(database: str, tablename: str) -> None:
    if MODEL_REGISTRY.get(tablename):
        obj = MODEL_REGISTRY.get(tablename)
    try:
        sql = obj.__table_sql__

        with connection(database) as conn:
            conn.execute(sql)
            logger.info("Created table %s", tablename)
    except Exception:
        logger.exception("Error creating table %s", tablename)
        raise