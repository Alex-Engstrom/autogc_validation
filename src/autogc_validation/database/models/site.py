# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:26 2026

@author: aengstrom
"""

"""Site-related data models."""

from pydantic.dataclasses import dataclass
from typing import Optional
from .base import BaseModel, validate_date_format


@dataclass
class Site(BaseModel):
    """
    Monitoring site information.
    
    Attributes:
        site_id: Unique site identifier
        name_short: Short site name (e.g., "HW")
        name_long: Full site name (e.g., "Hawthorne")
        lat: Latitude in decimal degrees
        long: Longitude in decimal degrees
        date_started: Date monitoring started (YYYY-MM-DD HH:MM:SS)
    """
    site_id: int
    name_short: str
    name_long: str
    lat: float
    long: float
    date_started: str
    
    __tablename__ = "sites"
    
    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS sites (
                        site_id INTEGER PRIMARY KEY,
                        name_short TEXT UNIQUE,
                        name_long TEXT UNIQUE,
                        lat REAL,
                        long REAL,
                        date_started TEXT
                    );
                    """
    
    def validate(self) -> None:
        """Validate site data."""
        if self.site_id <= 0:
            raise ValueError(f"site_id must be positive, got {self.site_id}")
        
        if not self.name_short or not self.name_short.strip():
            raise ValueError("name_short cannot be empty")
        
        if not self.name_long or not self.name_long.strip():
            raise ValueError("name_long cannot be empty")
        
        if not (-90 <= self.lat <= 90):
            raise ValueError(f"lat must be between -90 and 90, got {self.lat}")
        
        if not (-180 <= self.long <= 180):
            raise ValueError(f"long must be between -180 and 180, got {self.long}")
        
        validate_date_format(self.date_started, "date_started")
    


