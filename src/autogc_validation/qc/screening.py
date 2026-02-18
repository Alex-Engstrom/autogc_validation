# -*- coding: utf-8 -*-
"""
Ambient data screening checks.

Implements EPA TAD Table 10-1 compound ratio screening, overrange
detection, and daily maximum TNMHC reporting.
"""

import logging
from typing import Dict, Set, Union

import pandas as pd

from autogc_validation.database.enums import (
    CompoundAQSCode,
    VOCCategory,
    aqs_to_name,
    name_to_aqs,
    get_codes_by_category,
)
from autogc_validation.qc.utils import to_aqs_indexed_series

logger = logging.getLogger(__name__)


def check_ratios(
    data: pd.DataFrame,
    mdls: Dict[Union[str, int], float],
) -> pd.DataFrame:
    """Screen ambient samples for suspicious compound ratios per EPA TAD Table 10-1.

    Each condition compares two or more compounds (converted from ppbC to
    ppb using carbon count) and only flags when the primary compound
    exceeds 3x its MDL.

    Args:
        data: Dataset.data DataFrame.
        mdls: MDL values keyed by compound name or AQS code.

    Returns:
        DataFrame with columns: screen_reason, compounds (list of names).
    """
    mdl_series = to_aqs_indexed_series(mdls)
    mdl_series.index = mdl_series.index.map(int)

    ambient_df = data[data["sample_type"] == "s"].sort_index().copy()

    compound_cols = [c for c in ambient_df.columns if isinstance(c, int)]
    ambient_df[compound_cols] = ambient_df[compound_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    alkanes = get_codes_by_category(VOCCategory.ALKANE)
    alkenes = get_codes_by_category(VOCCategory.ALKENE)

    # Shorthand aliases
    C = CompoundAQSCode
    m = mdl_series
    a = ambient_df

    conditions = [
        (
            (a[C.C_BENZENE] / 6 > a[C.C_TOLUENE] / 7)
            & (a[C.C_BENZENE] > 3 * m[C.C_BENZENE]),
            "benzene_gt_toluene",
            [C.C_BENZENE, C.C_TOLUENE],
        ),
        (
            (a[C.C_BENZENE] / 6 > a[C.C_ETHANE] / 2)
            & (a[C.C_BENZENE] > 3 * m[C.C_BENZENE]),
            "benzene_gt_ethane",
            [C.C_BENZENE, C.C_ETHANE],
        ),
        (
            (a[C.C_ETHYLENE] / 2 > a[C.C_ETHANE] / 2)
            & (a[C.C_ETHYLENE] > 3 * m[C.C_ETHYLENE]),
            "ethylene_gt_ethane",
            [C.C_ETHYLENE, C.C_ETHANE],
        ),
        (
            (a[C.C_PROPYLENE] / 3 > a[C.C_PROPANE] / 3)
            & (a[C.C_PROPYLENE] > 3 * m[C.C_PROPYLENE]),
            "propylene_gt_propane",
            [C.C_PROPYLENE, C.C_PROPANE],
        ),
        (
            (a[C.C_O_XYLENE] / 8 > a[C.C_M_P_XYLENE] / 8)
            & (a[C.C_O_XYLENE] > 3 * m[C.C_O_XYLENE]),
            "oxylene_gt_mpxylene",
            [C.C_O_XYLENE, C.C_M_P_XYLENE],
        ),
        (
            (a[C.C_2_3_DIMETHYLPENTANE] > a[C.C_2_METHYLHEXANE])
            & (a[C.C_2_3_DIMETHYLPENTANE] > 3 * m[C.C_2_3_DIMETHYLPENTANE]),
            "23dimethylpentane_gt_2methylhexane",
            [C.C_2_METHYLHEXANE, C.C_2_3_DIMETHYLPENTANE],
        ),
        (
            (a[C.C_2_4_DIMETHYLPENTANE] > a[C.C_METHYLCYCLOPENTANE])
            & (a[C.C_2_4_DIMETHYLPENTANE] > 3 * m[C.C_2_4_DIMETHYLPENTANE]),
            "24dimethylpentane_gt_methylcyclopentane",
            [C.C_METHYLCYCLOPENTANE, C.C_2_4_DIMETHYLPENTANE],
        ),
        (
            (a[C.C_ISO_BUTANE] > a[C.C_N_BUTANE])
            & (a[C.C_ISO_BUTANE] > 3 * m[C.C_ISO_BUTANE]),
            "isobutane_gt_nbutane",
            [C.C_ISO_BUTANE, C.C_N_BUTANE],
        ),
        (
            (a[C.C_3_METHYLPENTANE] / 6 > 0.6 * a[C.C_2_METHYLPENTANE] / 6)
            & (a[C.C_3_METHYLPENTANE] > 3 * m[C.C_3_METHYLPENTANE]),
            "3methylpentane_gt_2methylpentane",
            [C.C_3_METHYLPENTANE, C.C_2_METHYLPENTANE],
        ),
        (
            (a[C.C_N_UNDECANE] / 11 > a[C.C_N_DECANE] / 10)
            & (a[C.C_N_UNDECANE] > 3 * m[C.C_N_UNDECANE]),
            "nundecane_gt_ndecane",
            [C.C_N_UNDECANE, C.C_N_DECANE],
        ),
        (
            ~(
                (a[C.C_ISO_PENTANE] > a[C.C_N_PENTANE])
                & (a[C.C_N_PENTANE] > a[C.C_CYCLOPENTANE])
            )
            & (a[C.C_ISO_PENTANE] > 3 * m[C.C_ISO_PENTANE])
            & (a[C.C_N_PENTANE] > 3 * m[C.C_N_PENTANE])
            & (a[C.C_CYCLOPENTANE] > 3 * m[C.C_CYCLOPENTANE]),
            "not_isopentane_gt_npentane_gt_cyclopentane",
            [C.C_ISO_PENTANE, C.C_N_PENTANE, C.C_CYCLOPENTANE],
        ),
        (
            a[alkenes].sum(axis=1) > a[alkanes].sum(axis=1),
            "alkenes_gt_alkanes",
            [],
        ),
    ]

    flagged = []
    for cond, label, compounds in conditions:
        subset = ambient_df.loc[cond].copy()
        if subset.empty:
            continue
        subset["screen_reason"] = label
        subset["compounds"] = [
            [aqs_to_name(c) for c in compounds] if compounds else ["alkanes", "alkenes"]
        ] * len(subset)
        flagged.append(subset)

    if not flagged:
        return pd.DataFrame(columns=["screen_reason", "compounds"])

    ratios_check = pd.concat(flagged, ignore_index=False)
    return ratios_check[["screen_reason", "compounds"]].copy()


def check_overrange_values(
    data: pd.DataFrame,
    upper_cal_point: float = 30.0,
    exclude_compounds: Set[str] = None,
) -> pd.DataFrame:
    """Flag ambient samples where compounds exceed the upper calibration limit.

    Args:
        data: Dataset.data DataFrame.
        upper_cal_point: Upper calibration concentration (ppbC).
        exclude_compounds: Compound names to exclude (default: TNMTC, TNMHC).

    Returns:
        DataFrame with columns: compound (AQS code), value, compound_name.
    """
    if exclude_compounds is None:
        exclude_compounds = {"TNMTC", "TNMHC"}

    exclude_codes = set()
    for name in exclude_compounds:
        try:
            exclude_codes.add(name_to_aqs(name))
        except (KeyError, ValueError):
            logger.warning("Unknown compound name for exclusion: %s", name)

    ambient_df = data[data["sample_type"] == "s"].copy()

    compound_cols = [c for c in ambient_df.columns if isinstance(c, int)]
    ambient_df[compound_cols] = ambient_df[compound_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    long_df = ambient_df.melt(
        id_vars=[],
        value_vars=compound_cols,
        var_name="compound",
        value_name="value",
        ignore_index=False,
    )

    mask = (long_df["value"] > upper_cal_point) & (
        ~long_df["compound"].isin(exclude_codes)
    )
    exceedances = long_df[mask].copy()

    exceedances["compound_name"] = exceedances["compound"].map(aqs_to_name)

    return exceedances


def check_daily_max_tnmhc(data: pd.DataFrame) -> pd.Series:
    """Find the daily maximum TNMHC value for ambient samples.

    Args:
        data: Dataset.data DataFrame.

    Returns:
        Series indexed by the timestamp of each daily max, values are TNMHC (ppbC).
    """
    ambient_df = data[data["sample_type"] == "s"].sort_index()

    s = ambient_df[CompoundAQSCode.C_TNMHC]

    timestamps_of_daily_max = s.groupby(s.index.date).idxmax()

    return s.loc[timestamps_of_daily_max]
