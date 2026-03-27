# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 11:45:40 2026

@author: aengstrom
"""
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from autogc_validation.database.enums import CanisterType, ConcentrationUnit
from typing import Optional
from autogc_validation.database.models.base import BaseModel
""" Calibration data model """

@dataclass
class Calibration(BaseModel):
    """
    Calibration with PLOT and BP RFs.

    Attributes:
        primary_canister_id: Unique canister identifier
        date_run
        plot_rf
        bp_rf
        
    """
    primary_canister_id: str
    date_run: str
    plot_rf: float
    bp_rf: float

    __tablename__ = "calibrations"

    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS calibrations (
                        primary_canister_id TEXT PRIMARY KEY,
                        date_run TEXT NOT NULL,
                        plot_rf REAL,
                        bp_rf REAL,
                        FOREIGN KEY(primary_canister_id) REFERENCES primary_canisters(primary_canister_id)
                    );
                    """

    @field_validator('primary_canister_id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("primary_canister_id cannot be empty")
        return v

    @field_validator('date_run')
    @classmethod
    def validate_expiration(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return BaseModel.validate_date_format(v)
        return v
