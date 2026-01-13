# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:45 2026

@author: aengstrom
"""

"""Enumerations and constants for PAMS VOC system."""

from enum import Enum, IntEnum


class VOCCategory(str, Enum):
    """VOC compound categories."""
    ALKANE = "Alkane"
    ALKENE = "Alkene"
    ALKYNE = "Alkyne"
    AROMATIC = "Aromatic"
    TERPENE = "Terpene"


class ColumnType(str, Enum):
    """GC column types."""
    PLOT = "PLOT"
    BP = "BP"


class CanisterType(str, Enum):
    """Standard canister types."""
    CVS = "CVS"  # Calibration Verification Standard
    RTS = "RTS"  # Round Trip Standard
    LCS = "LCS"  # Laboratory Control Standard



class ConcentrationUnit(str, Enum):
    """Supported concentration units."""
    PPBV = "ppbv"  # Parts per billion by volume
    PPMV = "ppmv"  # Parts per million by volume
    PPBC = "ppbc"  # Parts per billion by carbon
    PPMC = "ppmc"  # Parts per million by carbon



class Priority(IntEnum):
    """Compound priority levels."""
    LOW = 0
    HIGH = 1