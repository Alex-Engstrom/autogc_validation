# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:00:54 2026

@author: aengstrom
"""

from .canister_type import CanisterType
from .column_type import ColumnType
from .concentration_unit import ConcentrationUnit
from .priority import Priority
from .sample_type import SampleType
from .voc_category import VOCCategory
from .compound_code import CompoundAQSCode
from .compound_name import CompoundName
from .sites import Sites

# ---------------------------------------------------------------------------
# Synthetic codes for unidentified peaks
# ---------------------------------------------------------------------------
# These are NOT real AQS parameter codes. They are arbitrary 5-digit integers
# chosen to fit the same format as CompoundAQSCode values, so that unidentified
# peaks can flow through the same DataFrame columns and filtering logic.
# Each corresponds to one GC column: PLOT (light gases) and BP (heavier compounds).
PLOT_UNID_CODE = 10000
BP_UNID_CODE = 20000
UNID_CODES = frozenset({PLOT_UNID_CODE, BP_UNID_CODE})

# ---------------------------------------------------------------------------
# Compound code groupings
# ---------------------------------------------------------------------------
# AQS codes that represent computed totals, not individual target compounds.
TOTAL_CODES = frozenset({CompoundAQSCode.C_TNMHC, CompoundAQSCode.C_TNMTC})

# All real AQS target compound codes (excludes totals).
TARGET_CODES = frozenset(code for code in CompoundAQSCode if code not in TOTAL_CODES)


# ---------------------------------------------------------------------------
# Column-type groupings (derived from VOC_DATA)
# ---------------------------------------------------------------------------
# Importing here is safe — config.py has no dependencies on this package.
from autogc_validation.database.config import VOC_DATA as _VOC_DATA

# AQS codes for compounds that elute on each GC column.
PLOT_CODES = frozenset(v["aqs_code"] for v in _VOC_DATA if v["column"] == "PLOT")
BP_CODES = frozenset(v["aqs_code"] for v in _VOC_DATA if v["column"] == "BP")

# Calibrant compound for each GC column.  Used by QC qualifier generation to
# determine whether a whole-column LL/LK qualifier applies.
COLUMN_CALIBRANTS: dict[ColumnType, int] = {
    ColumnType.PLOT: CompoundAQSCode.C_PROPANE.value,  # Propane
    ColumnType.BP:   CompoundAQSCode.C_TOLUENE.value,  # Toluene
}

# Reference compounds used for retention time outlier detection.  Other
# compound RTs are locked relative to these, so a misidentification here
# implies a systematic shift across the column.
RT_REFERENCE_CODES: frozenset[int] = frozenset({
    CompoundAQSCode.C_PROPANE.value,    # Propane   — PLOT anchor
    CompoundAQSCode.C_N_PENTANE.value,  # n-Pentane — PLOT anchor
    CompoundAQSCode.C_BENZENE.value,    # Benzene   — BP anchor
    CompoundAQSCode.C_TOLUENE.value,    # Toluene   — BP anchor
})


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def aqs_to_name(code: int) -> str:
    """Convert an AQS code integer to a compound name string."""
    return CompoundName[CompoundAQSCode(code).name].value


def name_to_aqs(name: str) -> int:
    """Convert a compound name string to an AQS code integer.

    The first character of *name* is automatically uppercased before lookup
    so that e.g. ``"propane"`` and ``"Propane"`` both resolve correctly.
    """
    name = name.capitalize()
    return CompoundAQSCode[CompoundName(name).name].value


def get_column_type(code: int) -> ColumnType:
    """Return the GC column type (PLOT or BP) for a given AQS code.

    Args:
        code: An AQS code integer.

    Returns:
        ColumnType.PLOT or ColumnType.BP.

    Raises:
        ValueError: If the code is not a known target compound.
    """
    if code in PLOT_CODES:
        return ColumnType.PLOT
    if code in BP_CODES:
        return ColumnType.BP
    raise ValueError(f"AQS code {code} is not a known target compound")


def get_codes_by_category(category: VOCCategory) -> list[int]:
    """Return AQS codes for all compounds in the given VOC category.

    Derived from the static VOC_DATA config — does not require a database.

    Args:
        category: A VOCCategory enum member (e.g., VOCCategory.ALKANE).

    Returns:
        List of AQS code integers in elution order.
    """
    return [v["aqs_code"] for v in _VOC_DATA if v["category"] == category.value]


def get_codes_by_column(column: ColumnType) -> list[int]:
    """Return AQS codes for all compounds on the given GC column, in elution order.

    Derived from the static VOC_DATA config — does not require a database.

    Args:
        column: A ColumnType enum member (ColumnType.PLOT or ColumnType.BP).

    Returns:
        List of AQS code integers in elution order.
    """
    return [v["aqs_code"] for v in _VOC_DATA if v["column"] == column.value]


def get_carbon_count(code: int) -> int:
    """Return the carbon count for a given AQS code.

    Args:
        code: An AQS code integer.

    Returns:
        Carbon count as an integer.

    Raises:
        ValueError: If the code is not a known target compound.
    """
    for v in _VOC_DATA:
        if v["aqs_code"] == code:
            return v["carbon_count"]
    raise ValueError(f"AQS code {code} is not a known target compound")


__all__ = [
    "CanisterType",
    "ColumnType",
    "ConcentrationUnit",
    "Priority",
    "SampleType",
    "VOCCategory",
    "CompoundAQSCode",
    "CompoundName",
    "Sites",
    "PLOT_UNID_CODE",
    "BP_UNID_CODE",
    "UNID_CODES",
    "TOTAL_CODES",
    "TARGET_CODES",
    "PLOT_CODES",
    "BP_CODES",
    "COLUMN_CALIBRANTS",
    "RT_REFERENCE_CODES",
    "aqs_to_name",
    "name_to_aqs",
    "get_column_type",
    "get_codes_by_category",
    "get_codes_by_column",
    "get_carbon_count",
]