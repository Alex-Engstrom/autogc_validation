# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:02:07 2026

@author: aengstrom
"""

from enum import StrEnum

class VOCCategory(StrEnum):
    """VOC compound categories."""
    ALKANE = "Alkane"
    ALKENE = "Alkene"
    ALKYNE = "Alkyne"
    AROMATIC = "Aromatic"
    TERPENE = "Terpene"