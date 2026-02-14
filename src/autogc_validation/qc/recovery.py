# -*- coding: utf-8 -*-
"""
QC recovery checks for CVS, RTS, and LCS samples.

Compares measured concentrations against expected values (canister
concentration * blend ratio) and flags compounds outside the
acceptable recovery window (70%–130%).
"""

import logging
from typing import Dict, Union

import pandas as pd

from autogc_validation.database.enums import CompoundAQSCode, name_to_aqs
from autogc_validation.io.cdf import UNID_CODES

logger = logging.getLogger(__name__)

TOTAL_CODES = {CompoundAQSCode.C_TNMHC, CompoundAQSCode.C_TNMTC}

RECOVERY_LOWER_BOUND = 0.70
RECOVERY_UPPER_BOUND = 1.30


def _to_aqs_indexed_series(values: Dict[Union[str, int], float]) -> pd.Series:
    """Convert a dict keyed by compound name or AQS code to an AQS-indexed Series."""
    series = pd.Series(values)
    if not all(isinstance(k, int) for k in series.index):
        series.index = series.index.map(
            lambda k: name_to_aqs(k) if isinstance(k, str) else k
        )
    return series.dropna()


def check_qc_recovery(
    data: pd.DataFrame,
    qc_type: str,
    canister_conc: Dict[Union[str, int], float],
    blend_ratio: float,
) -> pd.DataFrame:
    """Check QC sample recovery against expected concentrations.

    Args:
        data: Dataset.data DataFrame.
        qc_type: Sample type code — 'c' (CVS), 'e' (LCS), or 'q' (RTS).
        canister_conc: Expected canister concentrations (before dilution).
        blend_ratio: Dilution factor applied to canister concentrations.

    Returns:
        DataFrame indexed by date_time with column 'failing_qc'
        (list of AQS codes outside recovery bounds).

    Raises:
        ValueError: If qc_type is not 'c', 'e', or 'q'.
    """
    if qc_type not in ("c", "e", "q"):
        raise ValueError("qc_type must be 'c', 'e', or 'q'")

    qc_df = data[data["sample_type"] == qc_type].sort_index()

    compound_columns = [
        c for c in data.columns
        if isinstance(c, int) and c not in UNID_CODES | TOTAL_CODES
    ]

    expected = _to_aqs_indexed_series(canister_conc) * blend_ratio

    results = []
    for timestamp, row in qc_df.iterrows():
        failing = [
            code for code in compound_columns
            if (code in expected.index
                and pd.notna(row[code])
                and (row[code] / float(expected[code]) > RECOVERY_UPPER_BOUND
                     or row[code] / float(expected[code]) < RECOVERY_LOWER_BOUND))
        ]
        if not failing:
            failing = ["__NONE__"]

        results.append({
            "date_time": timestamp,
            "failing_qc": failing,
        })

    return pd.DataFrame(results).set_index("date_time")


def check_qc_recovery_wide(
    data: pd.DataFrame,
    qc_type: str,
    canister_conc: Dict[Union[str, int], float],
    blend_ratio: float,
) -> pd.DataFrame:
    """Wide-format QC recovery failure table (one column per compound, values 0/1).

    Args:
        data: Dataset.data DataFrame.
        qc_type: Sample type code — 'c', 'e', or 'q'.
        canister_conc: Expected canister concentrations.
        blend_ratio: Dilution factor.

    Returns:
        DataFrame indexed by date_time, columns are AQS codes, values 0 or 1.
    """
    df = check_qc_recovery(data, qc_type, canister_conc, blend_ratio)

    exploded = df.explode("failing_qc")
    exploded["value"] = (exploded["failing_qc"] != "__NONE__").astype(int)
    wide = exploded.pivot_table(
        index=exploded.index,
        columns="failing_qc",
        values="value",
        aggfunc="first",
        fill_value=0,
    )
    if "__NONE__" in wide.columns:
        wide = wide.drop(columns="__NONE__")

    return wide
