# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:26 2026

@author: aengstrom
"""

"""Site-related data models."""

from pydantic.dataclasses import dataclass
from pydantic import field_validator
from .base import BaseModel


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

    @field_validator('site_id')
    @classmethod
    def validate_site_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"site_id must be positive, got {v}")
        return v

    @field_validator('name_short')
    @classmethod
    def validate_name_short(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name_short cannot be empty")
        return v

    @field_validator('name_long')
    @classmethod
    def validate_name_long(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name_long cannot be empty")
        return v

    @field_validator('lat')
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError(f"lat must be between -90 and 90, got {v}")
        return v

    @field_validator('long')
    @classmethod
    def validate_long(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError(f"long must be between -180 and 180, got {v}")
        return v

    @field_validator('date_started')
    @classmethod
    def validate_date(cls, v: str) -> str:
        return BaseModel.validate_date_format(v)
