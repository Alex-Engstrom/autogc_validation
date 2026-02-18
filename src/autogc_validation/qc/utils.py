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


def to_aqs_indexed_series(values: Dict[Union[str, int], float]) -> pd.Series:
    """Convert a dict keyed by compound name or AQS code to an AQS-indexed Series.

    QC functions receive MDL or canister concentration dicts that may be
    keyed by human-readable compound names (str) or AQS codes (int).
    This normalizes them to integer AQS code indices so they can be
    aligned with Dataset.data columns.

    Args:
        values: Dict mapping compound identifier to a numeric value.
            Keys can be compound name strings (e.g., "Benzene") or
            AQS code integers (e.g., 45201). Mixed keys are supported.

    Returns:
        Series with integer AQS code index, NaN values dropped.

    Raises:
        ValueError: If a string key does not match any known compound name.
    """
    series = pd.Series(values)
    if not all(isinstance(k, int) for k in series.index):
        series.index = series.index.map(_safe_name_to_aqs)
    return series.dropna()
