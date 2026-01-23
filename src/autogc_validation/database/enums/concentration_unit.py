# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:06:28 2026

@author: aengstrom
"""
from enum import StrEnum

class ConcentrationUnit(StrEnum):
    """Supported concentration units."""
    PPBV = "ppbv"  # Parts per billion by volume
    PPMV = "ppmv"  # Parts per million by volume
    PPBC = "ppbc"  # Parts per billion by carbon
    PPMC = "ppmc"  # Parts per million by carbon