# -*- coding: utf-8 -*-
"""
Shared utilities for QC analysis modules.
"""

from typing import Dict, Union

import numpy as np
import pandas as pd

from autogc_validation.database.enums import name_to_aqs, UNID_CODES, TOTAL_CODES


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
    wide single-row DataFrame with AQS codes as column names (as returned
    by get_active_mdls or get_active_canister_concentrations).

    Args:
        values: Dict mapping compound identifier to a numeric value, or
            a single-row wide DataFrame with integer AQS code column names.

    Returns:
        Series with integer AQS code index, NaN values dropped.

    Raises:
        ValueError: If a string key does not match any known compound name.
    """
    if isinstance(values, pd.DataFrame):
        series = values.iloc[0]
        series.index = series.index.map(int)
        return series.dropna()

    series = pd.Series(values)
    if not all(isinstance(k, int) for k in series.index):
        series.index = series.index.map(_safe_name_to_aqs)
    return series.dropna()


def get_compound_cols(df: pd.DataFrame) -> list[int]:
    """Return AQS code columns from a DataFrame, excluding UnID and total codes."""
    return [
        c for c in df.columns
        if isinstance(c, int) and c not in UNID_CODES | TOTAL_CODES
    ]


def align_period_index(samples: pd.DataFrame, periods: pd.DataFrame) -> np.ndarray:
    """Return integer array mapping each sample row to its applicable period row.

    For each sample timestamp, finds the most recent period row whose index
    is <= the sample timestamp (backward fill).

    Args:
        samples: DataFrame with DatetimeIndex.
        periods: Date-indexed wide concentrations DataFrame (sorted ascending).

    Returns:
        Integer array of length len(samples), values in [0, len(periods)-1].
    """
    period_dates = periods.index.sort_values()
    positions = period_dates.searchsorted(samples.index, side="right") - 1
    return np.clip(positions, 0, len(periods) - 1)
