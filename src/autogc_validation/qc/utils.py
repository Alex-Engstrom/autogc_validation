# -*- coding: utf-8 -*-
"""
Shared utilities for QC analysis modules.
"""

from typing import Dict, Union

import pandas as pd

from autogc_validation.database.enums import name_to_aqs


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
    """
    series = pd.Series(values)
    if not all(isinstance(k, int) for k in series.index):
        series.index = series.index.map(
            lambda k: name_to_aqs(k) if isinstance(k, str) else k
        )
    return series.dropna()
