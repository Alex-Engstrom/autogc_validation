# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:02:07 2026

@author: aengstrom
"""
from dataclasses import is_dataclass, fields
from ..connection.manager import transaction
from autogc_validation.utils.logging_config import get_logger
from ..models.registry import MODEL_REGISTRY, MODEL_LIST

logger = get_logger(__name__)


def insert(database: str, obj)-> None:

    if not type(obj) in MODEL_LIST:
        logger.warning(f"{obj} must be of the type ({' '.join(cls.__name__ for cls in MODEL_LIST)})")    
    
    
    columns = [f.name for f in fields(obj)]
    
    values = [getattr(obj, f) for f in columns]
    
    table = getattr(obj, "__tablename__", None)
    if table is None:
        raise AttributeError("Dataclass missing __tablename__")
    
    sql = f"""
    INSERT OR IGNORE INTO {table}
    ({", ".join(columns)})
    VALUES ({", ".join("?" for _ in columns)})
    """
    
    with transaction(database) as conn:
        conn.execute(sql, values)
    
    
    
    