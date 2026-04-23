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
        
    """
    primary_canister_id: str
    date_run: str
    dr1: float 
    dr2: float 
    dr3: float 
    dr4: float
    l1_area_PLOT: float 
    l1_conc_PLOT: float
    l2_area_PLOT: float 
    l2_conc_PLOT: float
    l3_area_PLOT: float 
    l3_conc_PLOT: float
    l4_area_PLOT: float 
    l4_conc_PLOT: float
    
    l1_area_BP: float 
    l1_conc_BP: float
    l2_area_BP: float 
    l2_conc_BP: float
    l3_area_BP: float 
    l3_conc_BP: float
    l4_area_BP: float 
    l4_conc_BP: float
    
    

    __tablename__ = "calibrations"

    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS calibrations (
                        primary_canister_id TEXT,
                        date_run TEXT NOT NULL PRIMARY KEY,
                        dr1 REAL,
                        dr2 REAL,
                        dr3 REAL,
                        dr4 REAL,
                        l1_area_PLOT REAL,
                        l1_conc_PLOT REAL,
                        l2_area_PLOT REAL,
                        l2_conc_PLOT REAL,
                        l3_area_PLOT REAL,
                        l3_conc_PLOT REAL,
                        l4_area_PLOT REAL,
                        l4_conc_PLOT REAL,
                        l1_area_BP REAL,
                        l1_conc_BP REAL,
                        l2_area_BP REAL,
                        l2_conc_BP REAL,
                        l3_area_BP REAL,
                        l3_conc_BP REAL,
                        l4_area_BP REAL,
                        l4_conc_BP REAL,
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
