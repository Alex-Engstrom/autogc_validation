
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:32 2026

@author: aengstrom
"""

"""Canister-related data models."""

from pydantic.dataclasses import dataclass
from pydantic import field_validator
from autogc_validation.database.enums import CanisterType, ConcentrationUnit
from typing import Optional
from autogc_validation.database.models.base import BaseModel

@dataclass
class CanisterTypes(BaseModel):
    """Table of valid canister types.

    Attributes:
        canister_type: Type of canister (CVS, RTS, LCS, etc.)
    """

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
                        expiration_date TEXT,
                        FOREIGN KEY(canister_type) REFERENCES canister_types(canister_type)
                    );
                    """

    @field_validator('primary_canister_id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("primary_canister_id cannot be empty")
        return v

    @field_validator('expiration_date')
    @classmethod
    def validate_expiration(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return BaseModel.validate_date_format(v)
        return v


@dataclass
class CanisterConcentration(BaseModel):
    """
    Concentration of a compound in a primary canister.

    Attributes:
        primary_canister_id: Canister identifier
        aqs_code: Compound AQS code
        concentration: Concentration in ppbv (stored in database)
        units: Concentration units
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

    @field_validator('primary_canister_id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("primary_canister_id cannot be empty")
        return v

    @field_validator('aqs_code')
    @classmethod
    def validate_aqs_code(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"aqs_code must be positive, got {v}")
        return v

    @field_validator('concentration')
    @classmethod
    def validate_concentration(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"concentration cannot be negative, got {v}")
        return v


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
                        date_off TEXT,
                        in_use INTEGER DEFAULT 0,
                        FOREIGN KEY (site_id) REFERENCES sites(site_id),
                        FOREIGN KEY (primary_canister_id) REFERENCES primary_canisters(primary_canister_id)
                    );
                    """

    @field_validator('site_canister_id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("site_canister_id cannot be empty")
        return v

    @field_validator('site_id')
    @classmethod
    def validate_site_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"site_id must be positive, got {v}")
        return v

    @field_validator('primary_canister_id')
    @classmethod
    def validate_primary_canister_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("primary_canister_id cannot be empty")
        return v

    @field_validator('dilution_ratio')
    @classmethod
    def validate_dilution_ratio(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"dilution_ratio must be positive, got {v}")
        return v

    @field_validator('in_use')
    @classmethod
    def validate_in_use(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"in_use must be 0 or 1, got {v}")
        return v

    @field_validator('blend_date', 'date_on')
    @classmethod
    def validate_dates(cls, v: str) -> str:
        return BaseModel.validate_date_format(v)

    @field_validator('date_off')
    @classmethod
    def validate_date_off(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return BaseModel.validate_date_format(v)
        return v

    @property
    def is_active(self) -> bool:
        """Check if canister is currently active."""
        return self.in_use == 1 and self.date_off is None
