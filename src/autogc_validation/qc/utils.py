# -*- coding: utf-8 -*-
"""
Shared utilities for QC analysis modules.
"""

from typing import Dict, Union

import pandas as pd

from autogc_validation.database.enums import name_to_aqs


def _safe_name_to_aqs(key):
    """Convert a compound name to AQS code with a clear error on failure."""
    if isinstance(key, int):
        return key
    try:
        return name_to_aqs(key)
    except (KeyError, ValueError):
        raise ValueError(
            f"Unknown compound name: '{key}'. Check spelling against "
            f"CompoundName enum values (e.g., 'Benzene', 'Ethane')."
        ) from None


def to_aqs_indexed_series(
    values: Union[Dict[Union[str, int], float], pd.DataFrame],
) -> pd.Series:
    """Convert compound concentrations to an AQS-indexed Series.

    Accepts either a dict (keyed by compound name or AQS code) or a
    DataFrame with 'aqs_code' and 'concentration' columns (as returned
    by get_active_canister_concentrations).

    Args:
        values: Dict mapping compound identifier to a numeric value, or
            a DataFrame with 'aqs_code' (int) and 'concentration' (float)
            columns.

    Returns:
        Series with integer AQS code index, NaN values dropped.

    Raises:
        ValueError: If a string key does not match any known compound name.
    """
    if isinstance(values, pd.DataFrame):
        series = values.set_index("aqs_code")["concentration"]
        return series.dropna()

    series = pd.Series(values)
    if not all(isinstance(k, int) for k in series.index):
        series.index = series.index.map(_safe_name_to_aqs)
    return series.dropna()
