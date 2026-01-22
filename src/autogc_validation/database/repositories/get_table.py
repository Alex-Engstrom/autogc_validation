# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:25:38 2026

@author: aengstrom
"""
from ..models.registry import MODEL_REGISTRY
from ..connection.manager import get_connection
from autogc_validation.utils.logging_config import get_logger
import pandas as pd

logger = get_logger(__name__)

def get_table(database: str, tablename: str, order_by: list[str] = None)-> None:
    if MODEL_REGISTRY.get(tablename):
        obj = MODEL_REGISTRY.get(tablename)
        if order_by:            
            sql = f"""SELECT * FROM {tablename} ORDER BY {", ".join(order_by)}"""
        else:
            sql = f"""SELECT * FROM {tablename}"""
        
        with get_connection(database) as conn:
            return pd.read_sql_query(sql, conn)
    else:
        logger.warning(f"{tablename} not a valid table")