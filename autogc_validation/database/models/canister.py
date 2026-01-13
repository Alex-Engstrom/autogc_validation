# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:32 2026

@author: aengstrom
"""

"""Canister-related data models."""

from dataclasses import dataclass, field
from typing import Optional, List
from .base import BaseModel, validate_date_format
from .voc import VOCConcentration


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
    canister_type: str
    expiration_date: Optional[str] = None
    
    def validate(self) -> None:
        """Validate primary canister data."""
        if not self.primary_canister_id or not self.primary_canister_id.strip():
            raise ValueError("primary_canister_id cannot be empty")
        
        if not self.canister_type or not self.canister_type.strip():
            raise ValueError("canister_type cannot be empty")
        
        if self.expiration_date:
            validate_date_format(self.expiration_date, "expiration_date")
    
    def __repr__(self) -> str:
        return f"PrimaryCanister(id='{self.primary_canister_id}', type='{self.canister_type}')"


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
    canister_type: str
    
    def validate(self) -> None:
        """Validate canister concentration."""
        if not self.primary_canister_id:
            raise ValueError("primary_canister_id cannot be empty")
        
        if self.aqs_code <= 0:
            raise ValueError(f"aqs_code must be positive, got {self.aqs_code}")
        
        if self.concentration < 0:
            raise ValueError(f"concentration cannot be negative, got {self.concentration}")
    
    def __repr__(self) -> str:
        return f"CanisterConcentration(canister='{self.primary_canister_id}', aqs={self.aqs_code}, conc={self.concentration})"


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
        
        validate_date_format(self.blend_date, "blend_date")
        validate_date_format(self.date_on, "date_on")
        if self.date_off:
            validate_date_format(self.date_off, "date_off")
    
    @property
    def is_active(self) -> bool:
        """Check if canister is currently active."""
        return self.in_use == 1 and self.date_off is None
    
    def __repr__(self) -> str:
        return f"SiteCanister(id='{self.site_canister_id}', site={self.site_id}, active={self.is_active})"