# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:05:44 2026

@author: aengstrom
"""
from enum import StrEnum

class CanisterType(StrEnum):
    """Standard canister types."""
    CVS = "CVS"  # Calibration Verification Standard
    RTS = "RTS"  # Round Trip Standard
    LCS = "LCS"  # Laboratory Control Standard