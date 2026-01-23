# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 15:38:12 2026

@author: aengstrom
"""
from pydantic.dataclasses import dataclass
from .base import BaseModel, validate_date_format
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
    
    __tablename__ = "mdls"
    
    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS mdls (
                        site_id INTEGER,
                        date_applied TEXT,
                        aqs_code INTEGER,
                        concentration REAL,
                        PRIMARY KEY (site_id, aqs_code, date_applied),
                        FOREIGN KEY (site_id) REFERENCES sites(site_id),
                        FOREIGN KEY (aqs_code) REFERENCES voc_info(aqs_code)
                    );
                    """
    
    def validate(self) -> None:
        """Validate MDL data."""
        if self.site_id <= 0:
            raise ValueError(f"site_id must be positive, got {self.site_id}")
        
        if self.aqs_code <= 0:
            raise ValueError(f"aqs_code must be positive, got {self.aqs_code}")
        
        if self.concentration < 0:
            raise ValueError(f"concentration cannot be negative, got {self.concentration}")
        
        validate_date_format(self.date_applied, "date_applied")
    