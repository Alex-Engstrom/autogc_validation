# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:02:07 2026

@author: aengstrom
"""
from dataclasses import is_dataclass, fields
from ..connection.manager import transaction

def insert(database: str, model)-> None:
    if not is_dataclass(model):
        raise TypeError("Expected dataclass object")
    
    columns = [f.name for f in fields(model)]
    
    values = [getattr(model, f) for f in columns]
    table = model.__tablename__
    
    sql = f"""
    INSERT OR IGNORE INTO {table}
    ({", ".join(columns)})
    VALUES ({", ".join("?" for _ in columns)})
    """
    
    with transaction(database) as conn:
        conn.execute(sql, values)
    
    
    
    