# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:19 2026

@author: aengstrom
"""

"""VOC (Volatile Organic Compound) data models."""

from pydantic.dataclasses import dataclass
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
    
    def validate(self) -> None:
        """Validate VOC info."""
        if self.aqs_code <= 0:
            raise ValueError(f"aqs_code must be positive, got {self.aqs_code}")
        if len(str(self.aqs_code)) != 5:
            raise ValueError(f"aqs_code must be 5 digits long, got {self.aqs_code}")
        
        if self.carbon_count <= 0:
            raise ValueError(f"carbon_count must be positive, got {self.carbon_count}")
        
        if self.molecular_weight <= 0:
            raise ValueError(f"molecular_weight must be positive, got {self.molecular_weight}")
        
        if self.elution_order < 0:
            raise ValueError(f"elution_order must be non-negative, got {self.elution_order}")
        
        if self.priority not in (0, 1):
            raise ValueError(f"priority must be 0 or 1, got {self.priority}")
    