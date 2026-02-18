# -*- coding: utf-8 -*-
"""
Blank QC checks.

Identifies compounds in blank samples that exceed their respective MDLs.
"""

import logging
from typing import Dict, Union

import pandas as pd

from autogc_validation.database.enums import UNID_CODES, TOTAL_CODES, SampleType
from autogc_validation.qc.utils import to_aqs_indexed_series

logger = logging.getLogger(__name__)


def compounds_above_mdl(
    data: pd.DataFrame,
    mdls: Dict[Union[str, int], float],
) -> pd.DataFrame:
    """Check which compounds exceed MDLs in blank samples.

    Args:
        data: Dataset.data DataFrame with 'sample_type' column.
        mdls: Dict mapping compound name or AQS code to MDL value (ppbC).

    Returns:
        DataFrame indexed by date_time with columns:
        filename, compounds_above_mdl (list of AQS codes).
    """
    blank_df = data[data["sample_type"] == SampleType.BLANK].sort_index()

    compound_columns = [
        c for c in data.columns
        if isinstance(c, int) and c not in UNID_CODES | TOTAL_CODES
    ]

    mdl_series = to_aqs_indexed_series(mdls)

    results = []
    for timestamp, row in blank_df.iterrows():
        above = [
            code for code in compound_columns
            if (code in mdl_series.index
                and pd.notna(row[code])
                and row[code] > mdl_series[code])
        ]
        if not above:
            above = ["__NONE__"]

        results.append({
            "date_time": timestamp,
            "filename": row["filename"],
            "compounds_above_mdl": above,
        })

    return pd.DataFrame(results).set_index("date_time")


def compounds_above_mdl_wide(
    data: pd.DataFrame,
    mdls: Dict[Union[str, int], float],
) -> pd.DataFrame:
    """Wide-format blank exceedance table (one column per compound, values 0/1).

    Args:
        data: Dataset.data DataFrame.
        mdls: Dict mapping compound name or AQS code to MDL value.

    Returns:
        DataFrame indexed by date_time, columns are AQS codes, values are 0 or 1.
    """
    df = compounds_above_mdl(data, mdls)

    exploded = df.explode("compounds_above_mdl")
    exploded["value"] = (exploded["compounds_above_mdl"] != "__NONE__").astype(int)
    wide = exploded.pivot_table(
        index=exploded.index,
        columns="compounds_above_mdl",
        values="value",
        aggfunc="first",
        fill_value=0,
    )
    if "__NONE__" in wide.columns:
        wide = wide.drop(columns="__NONE__")

    return wide
