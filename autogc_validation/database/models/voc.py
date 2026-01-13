# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:19 2026

@author: aengstrom
"""

"""VOC (Volatile Organic Compound) data models."""

from dataclasses import dataclass
from typing import Optional
from .base import BaseModel
from .enums import VOCCategory, ColumnType, Priority, ConcentrationUnit


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
    aqs_code: int
    compound: str
    category: VOCCategory
    carbon_count: int
    molecular_weight: float
    column: ColumnType
    elution_order: int
    priority: Priority
    
    def validate(self) -> None:
        """Validate VOC info."""
        if self.aqs_code <= 0:
            raise ValueError(f"aqs_code must be positive, got {self.aqs_code}")
        if len(self.aqs_code) != 5:
            raise ValueError(f"aqs_code must be 5 digits long, got {self.aqs_code}")
        
        if self.carbon_count <= 0:
            raise ValueError(f"carbon_count must be positive, got {self.carbon_count}")
        
        if self.molecular_weight <= 0:
            raise ValueError(f"molecular_weight must be positive, got {self.molecular_weight}")
        
        if self.elution_order < 0:
            raise ValueError(f"elution_order must be non-negative, got {self.elution_order}")
        
        if self.priority not in (0, 1):
            raise ValueError(f"priority must be 0 or 1, got {self.priority}")
    
    def __repr__(self) -> str:
        return f"VOCInfo(aqs_code={self.aqs_code}, compound='{self.compound}')"


@dataclass
class VOCConcentration(BaseModel):
    """
    Concentration of a specific VOC compound.
    
    Used as a building block for canister and measurement data.
    """
    aqs_code: int
    concentration: float
    unit: ConcentrationUnit
    
    def validate(self) -> None:
        """Validate concentration."""
        if self.concentration < 0:
            raise ValueError(f"concentration cannot be negative, got {self.concentration}")
    
    def to_ppbv(self, carbon_count: int) -> float:
        """
        Convert concentration to ppbv.
        
        Args:
            carbon_count: Number of carbon atoms (needed for ppbC conversions)
        
        Returns:
            Concentration in ppbv
        """
        unit = self.unit.lower()
        
        if unit == "ppbv":
            return self.concentration
        elif unit == "ppmv":
            return self.concentration * 1000
        elif unit == "ppbc":
            if carbon_count <= 0:
                raise ValueError("carbon_count required for ppbC conversion")
            return self.concentration / carbon_count
        elif unit == "ppmc":
            if carbon_count <= 0:
                raise ValueError("carbon_count required for ppmC conversion")
            return (self.concentration / carbon_count) * 1000
        else:
            raise ValueError(f"Unknown unit: {unit}")