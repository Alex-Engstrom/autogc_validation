# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:12 2026

@author: aengstrom
"""

from pydantic.dataclasses import dataclass
from dataclasses import asdict
from typing import Optional, Dict, Any, ClassVar
from datetime import datetime


@dataclass
class BaseModel:
    """Base class for all data models."""
    
    __tablename__: ClassVar[str] # Name of SQL table
    __table_sql__: ClassVar[str] # SQL command that creates the table
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary."""
        # Filter to only fields that exist in the dataclass
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    @staticmethod
    def validate_date_format(date_str: str) -> str:
        """Validate date format and raise error if invalid."""
        formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return date_str
            except ValueError:
                continue
        
        raise ValueError(
            f"Invalid date format: '{date_str}'. "
            f"Expected: YYYY-MM-DD HH:MM:SS or YYYY-MM-DD HH:MM"
        )