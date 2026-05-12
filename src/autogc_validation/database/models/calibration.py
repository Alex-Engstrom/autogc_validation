# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 11:45:40 2026

@author: aengstrom
"""
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from autogc_validation.database.enums import (
    CanisterType, ConcentrationUnit, ColumnType,
    COLUMN_CALIBRANTS, COLUMN_CALIBRANTS_ED, CALIBRANT_COMPOUNDS
)
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
    site_id: int
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
                        site_id INTEGER,
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
                        FOREIGN KEY(primary_canister_id) REFERENCES primary_canisters(primary_canister_id),
                        FOREIGN KEY(site_id) REFERENCES sites(site_id)
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
    def validate_rundate(cls, v: Optional[str]) -> Optional[str]:
        return BaseModel.validate_date_format(v)


def generate_cal_obj(
    primary_canister_id: str,
    date_run: str,
    site_id: int,
    dilution_ratios: list[float],
    plot_areas: list[float],
    bp_areas: list[float],
    plot_canister_conc: float,
    bp_canister_conc: float,
    site: str = None,
) -> Calibration:
    """Generate a Calibration object from lists of dilution ratios and peak areas.

    Concentrations are calculated as the primary canister concentration for the
    column calibrant multiplied by the corresponding dilution ratio at each level.
    Uses COLUMN_CALIBRANTS_ED (n-Butane / Toluene) for site 'ED', and
    COLUMN_CALIBRANTS (Propane / Toluene) for all other sites.

    Args:
        primary_canister_id: Canister identifier.
        date_run: Date the calibration was run (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS).
        site_id: Integer site ID referencing the sites table.
        dilution_ratios: List of 4 dilution ratios [dr1, dr2, dr3, dr4] in level order.
        plot_areas: List of 4 PLOT column peak areas in level order.
        bp_areas: List of 4 BP column peak areas in level order.
        plot_canister_conc: Undiluted primary canister concentration for the PLOT calibrant.
        bp_canister_conc: Undiluted primary canister concentration for the BP calibrant.
        site: Site code (e.g. 'ED'). Determines which calibrant dict is used. Defaults to None.

    Returns:
        Calibration dataclass instance.

    Raises:
        ValueError: If the resolved calibrant AQS codes are not in CALIBRANT_COMPOUNDS.
    """
    calibrants = COLUMN_CALIBRANTS_ED if site == "ED" else COLUMN_CALIBRANTS
    plot_calibrant = calibrants[ColumnType.PLOT]
    bp_calibrant = calibrants[ColumnType.BP]

    if plot_calibrant not in CALIBRANT_COMPOUNDS:
        raise ValueError(f"PLOT calibrant AQS {plot_calibrant} not in CALIBRANT_COMPOUNDS")
    if bp_calibrant not in CALIBRANT_COMPOUNDS:
        raise ValueError(f"BP calibrant AQS {bp_calibrant} not in CALIBRANT_COMPOUNDS")

    dr1, dr2, dr3, dr4 = dilution_ratios

    return Calibration(
        primary_canister_id=primary_canister_id,
        date_run=date_run,
        site_id=site_id,
        dr1=dr1, dr2=dr2, dr3=dr3, dr4=dr4,
        l1_area_PLOT=plot_areas[0], l1_conc_PLOT=plot_canister_conc * dr1,
        l2_area_PLOT=plot_areas[1], l2_conc_PLOT=plot_canister_conc * dr2,
        l3_area_PLOT=plot_areas[2], l3_conc_PLOT=plot_canister_conc * dr3,
        l4_area_PLOT=plot_areas[3], l4_conc_PLOT=plot_canister_conc * dr4,
        l1_area_BP=bp_areas[0], l1_conc_BP=bp_canister_conc * dr1,
        l2_area_BP=bp_areas[1], l2_conc_BP=bp_canister_conc * dr2,
        l3_area_BP=bp_areas[2], l3_conc_BP=bp_canister_conc * dr3,
        l4_area_BP=bp_areas[3], l4_conc_BP=bp_canister_conc * dr4,
    )

