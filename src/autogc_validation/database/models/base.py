# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:12 2026

@author: aengstrom
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class BaseModel:
    """Base class for all data models."""
    
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
    
    def validate(self) -> None:
        """
        Validate the model instance.
        Override in subclasses to add validation logic.
        Raises ValueError if validation fails.
        """
        pass


def validate_date_format(date_str: Optional[str], field_name: str = "date") -> None:
    """Validate date string format."""
    if date_str is None:
        return
    
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
    for fmt in formats:
        try:
            datetime.strptime(date_str, fmt)
            return
        except ValueError:
            continue
    
    raise ValueError(
        f"{field_name} must be in format 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD HH:MM', "
        f"got: {date_str}"
    )