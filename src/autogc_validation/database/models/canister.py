# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:32 2026

@author: aengstrom
"""

"""Canister-related data models."""

from pydantic.dataclasses import dataclass
from autogc_validation.database.enums import CanisterType, ConcentrationUnit
from typing import Optional
from autogc_validation.database.models import BaseModel

@dataclass 
class CanisterTypes(BaseModel):
    """Table of valid canister types
    Attributes:
        canister_type: Type of canister (CVS, RTS, LCS, etc.)"""
    
    canister_type: CanisterType
    
    __tablename__ = "canister_types"
    
    __table_sql__ = """CREATE TABLE IF NOT EXISTS canister_types (
                            canister_type TEXT PRIMARY KEY
                        );
                        """
    
@dataclass
class PrimaryCanister(BaseModel):
    """
    Primary standard canister with known concentrations.
    
    Attributes:
        primary_canister_id: Unique canister identifier
        canister_type: Type of canister (CVS, RTS, LCS, etc.)
        expiration_date: Date the canister expires (optional)
    """
    primary_canister_id: str
    canister_type: CanisterType
    expiration_date: Optional[str] = None
    
    __tablename__ = "primary_canisters"
    
    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS primary_canisters (
                        primary_canister_id TEXT PRIMARY KEY,
                        canister_type TEXT NOT NULL,
                        expiration_date TEXT NOT NULL,
                        FOREIGN KEY(canister_type) REFERENCES canister_types(canister_type)
                    );
                    """
                    
    def validate(self) -> None:
        """Validate primary canister data."""
        if not self.primary_canister_id or not self.primary_canister_id.strip():
            raise ValueError("primary_canister_id cannot be empty")
        
        if not self.canister_type or not self.canister_type.strip():
            raise ValueError("canister_type cannot be empty")
        
        if self.expiration_date:
            BaseModel.validate_date_format(self.expiration_date, "expiration_date")
    


@dataclass
class CanisterConcentration(BaseModel):
    """
    Concentration of a compound in a primary canister.
    
    Attributes:
        primary_canister_id: Canister identifier
        aqs_code: Compound AQS code
        concentration: Concentration in ppbv (stored in database)
        canister_type: Type of canister
    """
    primary_canister_id: str
    aqs_code: int
    concentration: float
    units: ConcentrationUnit
    canister_type: CanisterType
    
    __tablename__ = "primary_canister_concentration"
    
    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS primary_canister_concentration (
                        primary_canister_id TEXT,
                        aqs_code INTEGER,
                        concentration REAL,
                        units TEXT,
                        canister_type TEXT,
                        PRIMARY KEY (primary_canister_id, aqs_code),
                        FOREIGN KEY (primary_canister_id) REFERENCES primary_canisters(primary_canister_id),
                        FOREIGN KEY (aqs_code) REFERENCES voc_info(aqs_code),
                        FOREIGN KEY (canister_type) REFERENCES canister_types(canister_type)
                    );
                    """
    
    def validate(self) -> None:
        """Validate canister concentration."""
        if not self.primary_canister_id:
            raise ValueError("primary_canister_id cannot be empty")
        
        if self.aqs_code <= 0:
            raise ValueError(f"aqs_code must be positive, got {self.aqs_code}")
        
        if self.concentration < 0:
            raise ValueError(f"concentration cannot be negative, got {self.concentration}")
    

@dataclass
class SiteCanister(BaseModel):
    """
    Diluted canister deployed at a monitoring site.
    
    Attributes:
        site_canister_id: Unique identifier for this site canister
        site_id: Site where canister is deployed
        primary_canister_id: Source primary canister
        dilution_ratio: Dilution factor applied
        blend_date: Date canister was blended
        date_on: Date canister was deployed
        date_off: Date canister was removed (None if still active)
        in_use: Whether canister is currently in use (0 or 1)
    """
    site_canister_id: str
    site_id: int
    primary_canister_id: str
    dilution_ratio: float
    blend_date: str
    date_on: str
    date_off: Optional[str] = None
    in_use: int = 0
    
    __tablename__ = "site_canisters"
    
    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS site_canisters (
                        site_canister_id TEXT PRIMARY KEY,
                        site_id INTEGER NOT NULL,
                        primary_canister_id TEXT NOT NULL,
                        dilution_ratio REAL,
                        blend_date TEXT,
                        date_on TEXT,
                        date_off TEXT,                   -- timestamp when returned
                        in_use INTEGER DEFAULT 0,        -- 0 = not in use, 1 = in use        
                        FOREIGN KEY (site_id) REFERENCES sites(site_id),
                        FOREIGN KEY (primary_canister_id) REFERENCES primary_canisters(primary_canister_id)
                    );
                    """
    
    def validate(self) -> None:
        """Validate site canister data."""
        if not self.site_canister_id or not self.site_canister_id.strip():
            raise ValueError("site_canister_id cannot be empty")
        
        if self.site_id <= 0:
            raise ValueError(f"site_id must be positive, got {self.site_id}")
        
        if not self.primary_canister_id or not self.primary_canister_id.strip():
            raise ValueError("primary_canister_id cannot be empty")
        
        if self.dilution_ratio <= 0:
            raise ValueError(f"dilution_ratio must be positive, got {self.dilution_ratio}")
        
        if self.in_use not in (0, 1):
            raise ValueError(f"in_use must be 0 or 1, got {self.in_use}")
        
        BaseModel.validate_date_format(self.blend_date, "blend_date")
        BaseModel.validate_date_format(self.date_on, "date_on")
        if self.date_off:
            BaseModel.validate_date_format(self.date_off, "date_off")
    
    @property
    def is_active(self) -> bool:
        """Check if canister is currently active."""
        return self.in_use == 1 and self.date_off is None
    