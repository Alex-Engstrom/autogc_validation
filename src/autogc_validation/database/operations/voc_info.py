# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:05:49 2026

@author: aengstrom
"""

import logging
from typing import List, Optional
import pandas as pd

from autogc_validation.database.conn import connection, transaction
from autogc_validation.database.models import VOCInfo

logger = logging.getLogger(__name__)

def bulk_insert(database: str, vocs: List[VOCInfo]) -> int:
    """
    Insert multiple VOC records.
    
    Args:
        database: Database path
        vocs: List of VOCInfo objects
        
    Returns:
        Number of records inserted
    """
    sql = """
    INSERT OR IGNORE INTO voc_info 
    (aqs_code, compound, category, carbon_count, molecular_weight, 
     column, elution_order, priority)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Convert dataclasses to tuples for insertion
    # Use .value to get enum string values
    data = [
        (
            v.aqs_code, 
            v.compound, 
            v.category.value,      # Get enum value
            v.carbon_count,
            v.molecular_weight, 
            v.column.value,        # Get enum value
            v.elution_order, 
            v.priority.value       # Get enum value
        )
        for v in vocs
    ]
    
    with transaction(database) as conn:
        cursor = conn.executemany(sql, data)
        count = cursor.rowcount
        logger.info(f"Inserted {count} VOC records")
        return count

def get_by_aqs_code(database: str, aqs_code: int) -> Optional[VOCInfo]:
    """Get a VOC by its AQS code."""
    sql = "SELECT * FROM voc_info WHERE aqs_code = ?"
    
    with connection(database) as conn:
        cursor = conn.execute(sql, (aqs_code,))
        row = cursor.fetchone()
        
        if row:
            return VOCInfo.from_dict(dict(row))
        return None


def get_all_voc_data(database: str) -> List[VOCInfo]:
    """Get all VOC information as list of VOCInfo objects."""
    sql = "SELECT * FROM voc_info ORDER BY column DESC, elution_order"
    
    with connection(database) as conn:
        cursor = conn.execute(sql)
        return [VOCInfo.from_dict(dict(row)) for row in cursor.fetchall()]


def get_all_voc_data_as_dataframe(database: str) -> pd.DataFrame:
    """Get all VOC information as a DataFrame."""
    sql = "SELECT * FROM voc_info ORDER BY elution_order"
    
    with connection(database) as conn:
        return pd.read_sql_query(sql, conn)
