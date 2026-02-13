# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:19 2026

@author: aengstrom
"""

"""VOC (Volatile Organic Compound) data models."""

from pydantic.dataclasses import dataclass
from pydantic import field_validator
from autogc_validation.database.models.base import BaseModel
from autogc_validation.database.enums import VOCCategory, ColumnType, Priority, CompoundAQSCode, CompoundName


@dataclass
class VOCInfo(BaseModel):
    """
    Reference information for a VOC compound.

    Attributes:
        aqs_code: EPA Air Quality System parameter code
        compound: Compound name (e.g., "Benzene", "Ethane")
        category: Compound category (Alkane, Aromatic, etc.)
        carbon_count: Number of carbon atoms in the molecule
        molecular_weight: Molecular weight in g/mol
        column: GC column used for analysis (PLOT or BP)
        elution_order: Order of elution from the column
        priority: Analysis priority (0=low, 1=high)
    """
    aqs_code: CompoundAQSCode
    compound: CompoundName
    category: VOCCategory
    carbon_count: int
    molecular_weight: float
    column: ColumnType
    elution_order: int
    priority: Priority

    __tablename__ = "voc_info"

    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS voc_info (
                        aqs_code INTEGER PRIMARY KEY,
                        compound TEXT,
                        category TEXT,
                        carbon_count INTEGER,
                        molecular_weight REAL,
                        column TEXT,
                        elution_order INTEGER,
                        priority BOOLEAN
                    );
                    """

    @field_validator('carbon_count')
    @classmethod
    def validate_carbon_count(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"carbon_count must be positive, got {v}")
        return v

    @field_validator('molecular_weight')
    @classmethod
    def validate_molecular_weight(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"molecular_weight must be positive, got {v}")
        return v

    @field_validator('elution_order')
    @classmethod
    def validate_elution_order(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"elution_order must be non-negative, got {v}")
        return v
