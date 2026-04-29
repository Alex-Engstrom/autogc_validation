# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:00:54 2026

@author: aengstrom
"""

from autogc_core import aqs_to_name, name_to_aqs
from .canister_type import CanisterType
from .qualifier_code import (
    QualifierCodeInfo,
    QUALIFIER_CODES,
    NULL_CODES,
    is_null_code,
    get_qualifier_description,
)
from .column_type import ColumnType
from .concentration_unit import ConcentrationUnit
from .priority import Priority
from .sample_type import SampleTypeLetter, SampleTypeLong, LETTER_TO_LONG_NAMES, LONG_NAME_CANONICAL
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

# Compounds present in LCS/CVS calibration canisters, mapped to the set of
# target compounds whose response factors they represent.  Each key is a
# calibrant AQS code; the value is a frozenset of non-calibrant AQS codes that
# should be calibrated using that calibrant's response factor.
#
# Assignment is based primarily on elution-order proximity within each GC
# column (PLOT or BP), with carbon count used as a secondary tiebreaker.
# These defaults are a reasonable starting point — adjust as needed.
#
# PLOT column calibrants (elution order in parentheses):
#   Ethane(1), Propane(3), N-butane(6), Acetylene(7)*, N-pentane(13),
#   1,3-butadiene(14), 2-methylpentane(20), 1-hexene(24)
#
# BP column calibrants:
#   N-hexane(1), Benzene(4), Toluene(13), M&p-xylene(18),
#   N-propylbenzene(24), 1,2,4-tri-m-benzene(30), P-diethylbenzene(34)*
#
# * Acetylene and P-diethylbenzene map to empty frozensets — present in the
#   LCS/CVS canisters but unreliable as QC calibrants.
CALIBRATION_GROUPS: dict[int, frozenset[int]] = {
    # --- PLOT column ---
    CompoundAQSCode.C_ETHANE.value: frozenset({          # elution 1
        CompoundAQSCode.C_ETHYLENE.value,                # elution 2, C2
    }),
    CompoundAQSCode.C_PROPANE.value: frozenset({         # elution 3
        CompoundAQSCode.C_PROPYLENE.value,               # elution 4, C3
    }),
    CompoundAQSCode.C_N_BUTANE.value: frozenset({        # elution 6
        CompoundAQSCode.C_ISO_BUTANE.value,              # elution 5, C4
        CompoundAQSCode.C_TRANS_2_BUTENE.value,          # elution 8, C4
        CompoundAQSCode.C_1_BUTENE.value,                # elution 9, C4
    }),
    CompoundAQSCode.C_ACETYLENE.value: frozenset(),      # elution 7 — unreliable in QC canisters
    CompoundAQSCode.C_N_PENTANE.value: frozenset({       # elution 13
        CompoundAQSCode.C_CIS_2_BUTENE.value,            # elution 10, C4 (equidist to Acetylene; lower C → Pentane)
        CompoundAQSCode.C_CYCLOPENTANE.value,            # elution 11, C5
        CompoundAQSCode.C_ISO_PENTANE.value,             # elution 12, C5
    }),
    CompoundAQSCode.C_1_3_BUTADIENE.value: frozenset({  # elution 14
        CompoundAQSCode.C_TRANS_2_PENTENE.value,         # elution 15, C5
        CompoundAQSCode.C_1_PENTENE.value,               # elution 16, C5
        CompoundAQSCode.C_CIS_2_PENTENE.value,           # elution 17, C5
    }),
    CompoundAQSCode.C_2_METHYLPENTANE.value: frozenset({ # elution 20
        CompoundAQSCode.C_2_2_DIMETHYLBUTANE.value,      # elution 18, C6
        CompoundAQSCode.C_2_3_DIMETHYLBUTANE.value,      # elution 19, C6
        CompoundAQSCode.C_3_METHYLPENTANE.value,         # elution 21, C6
        CompoundAQSCode.C_ISOPRENE.value,                # elution 22, C5 (equidist to 1-hexene; assigned here by convention)
    }),
    CompoundAQSCode.C_1_HEXENE.value: frozenset({        # elution 24
        CompoundAQSCode.C_2_METHYL_1_PENTENE.value,      # elution 23, C6
    }),
    # --- BP column ---
    CompoundAQSCode.C_N_HEXANE.value: frozenset({        # elution 1
        CompoundAQSCode.C_METHYLCYCLOPENTANE.value,      # elution 2, C6
    }),
    CompoundAQSCode.C_BENZENE.value: frozenset({         # elution 4
        CompoundAQSCode.C_2_4_DIMETHYLPENTANE.value,     # elution 3, C7
        CompoundAQSCode.C_CYCLOHEXANE.value,             # elution 5, C6
        CompoundAQSCode.C_2_METHYLHEXANE.value,          # elution 6, C7
        CompoundAQSCode.C_2_3_DIMETHYLPENTANE.value,     # elution 7, C7
        CompoundAQSCode.C_3_METHYLHEXANE.value,          # elution 8, C7
    }),
    CompoundAQSCode.C_TOLUENE.value: frozenset({         # elution 13
        CompoundAQSCode.C_2_2_4_TRIMETHYLPENTANE.value,  # elution 9, C8
        CompoundAQSCode.C_N_HEPTANE.value,               # elution 10, C7
        CompoundAQSCode.C_METHYLCYCLOHEXANE.value,       # elution 11, C7
        CompoundAQSCode.C_2_3_4_TRIMETHYLPENTANE.value,  # elution 12, C8
        CompoundAQSCode.C_2_METHYLHEPTANE.value,         # elution 14, C8
        CompoundAQSCode.C_3_METHYLHEPTANE.value,         # elution 15, C8
    }),
    CompoundAQSCode.C_M_P_XYLENE.value: frozenset({      # elution 18
        CompoundAQSCode.C_N_OCTANE.value,                # elution 16, C8
        CompoundAQSCode.C_ETHYLBENZENE.value,            # elution 17, C8
        CompoundAQSCode.C_STYRENE.value,                 # elution 19, C8
        CompoundAQSCode.C_O_XYLENE.value,                # elution 20, C8
    }),
    CompoundAQSCode.C_N_PROPYLBENZENE.value: frozenset({ # elution 24
        CompoundAQSCode.C_N_NONANE.value,                # elution 21, C9 (equidist to M&p-xylene; higher C → Propylbenzene)
        CompoundAQSCode.C_ISO_PROPYLBENZENE.value,       # elution 22, C9
        CompoundAQSCode.C_ALPHA_PINENE.value,            # elution 23, C10
        CompoundAQSCode.C_M_ETHYLTOLUENE.value,          # elution 25, C9
        CompoundAQSCode.C_P_ETHYLTOLUENE.value,          # elution 26, C9
        CompoundAQSCode.C_1_3_5_TRI_M_BENZENE.value,    # elution 27, C9 (equidist; same C as key → Propylbenzene)
    }),
       # elution 34 — unreliable in QC canisters
    CompoundAQSCode.C_1_2_4_TRI_M_BENZENE.value: frozenset({ # elution 30
        CompoundAQSCode.C_O_ETHYLTOLUENE.value,          # elution 28, C9
        CompoundAQSCode.C_BETA_PINENE.value,             # elution 29, C10
        CompoundAQSCode.C_N_DECANE.value,                # elution 31, C10
        CompoundAQSCode.C_1_2_3_TRI_M_BENZENE.value,    # elution 32, C9
        CompoundAQSCode.C_M_DIETHYLBENZENE.value,        # elution 33, C10
        CompoundAQSCode.C_N_UNDECANE.value,              # elution 35, C11
        CompoundAQSCode.C_N_DODECANE.value,              # elution 36, C12
    }),
    CompoundAQSCode.C_P_DIETHYLBENZENE.value: frozenset(),
}

CALIBRANT_COMPOUNDS = [key for key in CALIBRATION_GROUPS.keys()]
# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

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
    "SampleTypeLetter",
    "SampleTypeLong",
    "LETTER_TO_LONG_NAMES",
    "LONG_NAME_CANONICAL",
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
    "QualifierCodeInfo",
    "QUALIFIER_CODES",
    "NULL_CODES",
    "is_null_code",
    "get_qualifier_description",
    "aqs_to_name",
    "name_to_aqs",
    "get_column_type",
    "get_codes_by_category",
    "get_codes_by_column",
    "get_carbon_count",
]