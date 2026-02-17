# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:00:54 2026

@author: aengstrom
"""

from .canister_type import CanisterType
from .column_type import ColumnType
from .concentration_unit import ConcentrationUnit
from .priority import Priority
from .voc_category import VOCCategory
from .compound_code import CompoundAQSCode
from .compound_name import CompoundName

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


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def aqs_to_name(code: int) -> str:
    """Convert an AQS code integer to a compound name string."""
    return CompoundName[CompoundAQSCode(code).name].value


def name_to_aqs(name: str) -> int:
    """Convert a compound name string to an AQS code integer."""
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
        List of AQS code integers.
    """
    return [v["aqs_code"] for v in _VOC_DATA if v["category"] == category.value]


__all__ = [
    "CanisterType",
    "ColumnType",
    "ConcentrationUnit",
    "Priority",
    "VOCCategory",
    "CompoundAQSCode",
    "CompoundName",
    "PLOT_UNID_CODE",
    "BP_UNID_CODE",
    "UNID_CODES",
    "TOTAL_CODES",
    "TARGET_CODES",
    "PLOT_CODES",
    "BP_CODES",
    "aqs_to_name",
    "name_to_aqs",
    "get_column_type",
    "get_codes_by_category",
]