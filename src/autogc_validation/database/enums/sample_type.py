# -*- coding: utf-8 -*-
"""Sample type codes from AutoGC filename convention."""

from enum import StrEnum


class SampleType(StrEnum):
    """Sample type codes from AutoGC filename convention."""
    AMBIENT = "s"
    BLANK = "b"
    CVS = "c"
    RTS = "q"
    LCS = "e"
    MDL_POINT = "d"
    CALIBRATION_POINT = "m"
    EXPERIMENTAL = "x"
