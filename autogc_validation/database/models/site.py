# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:26 2026

@author: aengstrom
"""

"""Site-related data models."""

from dataclasses import dataclass
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
    
    def __repr__(self) -> str:
        return f"Site(site_id={self.site_id}, name_short='{self.name_short}')"


@dataclass
class MDL(BaseModel):
    """
    Method Detection Limit for a compound at a site.
    
    Attributes:
        site_id: Site identifier
        aqs_code: Compound AQS code
        concentration: MDL concentration in ppbv
        date_applied: Date this MDL became effective
    """
    site_id: int
    aqs_code: int
    concentration: float
    date_applied: str
    
    def validate(self) -> None:
        """Validate MDL data."""
        if self.site_id <= 0:
            raise ValueError(f"site_id must be positive, got {self.site_id}")
        
        if self.aqs_code <= 0:
            raise ValueError(f"aqs_code must be positive, got {self.aqs_code}")
        
        if self.concentration < 0:
            raise ValueError(f"concentration cannot be negative, got {self.concentration}")
        
        validate_date_format(self.date_applied, "date_applied")
    
    def __repr__(self) -> str:
        return f"MDL(site_id={self.site_id}, aqs_code={self.aqs_code}, concentration={self.concentration})"