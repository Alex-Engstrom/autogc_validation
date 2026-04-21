# -*- coding: utf-8 -*-
"""Sample type codes from AutoGC filename convention."""

from enum import StrEnum


class SampleTypeLetter(StrEnum):
    """Single-letter sample type codes from the AutoGC filename convention.

    Several letters are shared by multiple logical sub-types (e.g. all four
    calibration levels use "m"; PT canister and ambient spike both use "x").
    Python's StrEnum makes the later duplicates aliases of the first, so
    ``SampleTypeLetter("m").name`` always returns ``"CALIBRATION_POINT"``.
    Use ``SampleTypeLong`` (from the CDF ``sample_id`` attribute) to
    distinguish within these groups.
    """
    AMBIENT           = "s"
    BLANK             = "b"
    CVS               = "c"
    RTS               = "q"
    LCS               = "e"
    MDL_POINT         = "d"
    CALIBRATION_POINT = "m"   # canonical name for all cal levels
    CAL_POINT_1       = "m"   # alias → CALIBRATION_POINT
    CAL_POINT_2       = "m"   # alias → CALIBRATION_POINT
    CAL_POINT_3       = "m"   # alias → CALIBRATION_POINT
    CAL_POINT_4       = "m"   # alias → CALIBRATION_POINT
    EXPERIMENTAL      = "x"   # canonical name for all experimental sub-types
    PT                = "x"   # alias → EXPERIMENTAL
    AMBIENTSPIKE      = "x"   # alias → EXPERIMENTAL


class SampleTypeLong(StrEnum):
    """Long-form sample type codes from the EZChrom ``sample_id`` attribute."""
    AMBIENT    = "Ambient Air"
    BLANK      = "Blank"
    CVS        = "Standard"
    RTS        = "IQ - RTS"
    LCS        = "CS - LCS"
    MDL_POINT  = "MDL"
    CAL_POINT_1 = "Curve LVL 1"
    CAL_POINT_2 = "Curve LVL 2"
    CAL_POINT_3 = "Curve LVL 3"
    CAL_POINT_4 = "Curve LVL 4"
    PT          = "PT canister"
    AMBIENTSPIKE = "Ambient Spike"


# Maps each canonical SampleTypeLetter name to the set of SampleTypeLong
# names that are considered compatible with it.  Used by
# Dataset.check_long_and_letter_sample_types() to handle the ambiguous
# letters "m" (any cal level) and "x" (any experimental sub-type).
LETTER_TO_LONG_NAMES: dict[str, frozenset[str]] = {
    "AMBIENT":           frozenset({"AMBIENT"}),
    "BLANK":             frozenset({"BLANK"}),
    "CVS":               frozenset({"CVS"}),
    "RTS":               frozenset({"RTS"}),
    "LCS":               frozenset({"LCS"}),
    "MDL_POINT":         frozenset({"MDL_POINT"}),
    "CALIBRATION_POINT": frozenset({"CAL_POINT_1", "CAL_POINT_2", "CAL_POINT_3", "CAL_POINT_4"}),
    "EXPERIMENTAL":      frozenset({"PT", "AMBIENTSPIKE"}),
}
    
    
