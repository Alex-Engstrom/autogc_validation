# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:02:37 2026

@author: aengstrom
"""

from enum import StrEnum

class ColumnType(StrEnum):
    """GC column types."""
    PLOT = "PLOT"
    BP = "BP"