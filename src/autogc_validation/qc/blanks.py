# -*- coding: utf-8 -*-
"""
Blank QC checks.

Identifies compounds in blank samples that exceed their respective MDLs
or a fixed concentration threshold.
"""

import logging

import pandas as pd

from autogc_validation.database.enums import SampleType
from autogc_validation.qc.utils import get_compound_cols, align_period_index

logger = logging.getLogger(__name__)

_THRESHOLD_PPBC = 0.5


def compounds_above_mdl(
    blanks: pd.DataFrame,
    mdl_periods: pd.DataFrame,
    threshold_ppbc: float = _THRESHOLD_PPBC,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Check blank samples against MDLs and a fixed concentration threshold.

    Accepts a typed blanks DataFrame (from Dataset.blanks) and a date-indexed
    wide MDL DataFrame (from get_mdl_periods). Internally aligns each sample
    to the MDL period that was active on its collection date.

    Args:
        blanks: Dataset.blanks DataFrame — DatetimeIndex, AQS code columns,
            filename column. Must have attrs["sample_type"] == SampleType.BLANK.
        mdl_periods: Wide DataFrame with DatetimeIndex (one row per MDL period)
            and AQS codes as columns, as returned by get_mdl_periods.
        threshold_ppbc: Fixed concentration threshold (ppbC). Default 0.5.

    Returns:
        Tuple of (mdl_failures, threshold_failures):
            mdl_failures: Wide boolean DataFrame — 1 where compound > MDL,
                0 otherwise. Columns: filename + AQS codes. Index: date_time.
            threshold_failures: Wide boolean DataFrame — 1 where compound
                > threshold_ppbc, 0 otherwise. Same shape as mdl_failures.

    Raises:
        ValueError: If blanks.attrs["sample_type"] is not SampleType.BLANK.
    """
    sample_type = blanks.attrs.get("sample_type")
    if sample_type != SampleType.BLANK:
        raise ValueError(
            f"Expected blanks DataFrame with attrs['sample_type'] == SampleType.BLANK, "
            f"got {sample_type!r}"
        )

    if blanks.empty:
        logger.info("Blank check: no blank samples found")
        empty = pd.DataFrame(columns=["filename"])
        return empty, empty

    compound_cols = get_compound_cols(blanks)
    period_indices = align_period_index(blanks, mdl_periods)

    mdl_rows = []
    threshold_rows = []

    for i, (timestamp, row) in enumerate(blanks.iterrows()):
        effective_mdls = mdl_periods.iloc[period_indices[i]]

        mdl_flags = {"filename": row["filename"]}
        threshold_flags = {"filename": row["filename"]}

        for code in compound_cols:
            value = row[code]
            if pd.isna(value):
                mdl_flags[code] = 0
                threshold_flags[code] = 0
                continue

            mdl_val = effective_mdls.get(code)
            mdl_flags[code] = int(
                mdl_val is not None and not pd.isna(mdl_val) and value > mdl_val
            )
            threshold_flags[code] = int(value > threshold_ppbc)

        mdl_rows.append(mdl_flags)
        threshold_rows.append(threshold_flags)

    mdl_failures = pd.DataFrame(mdl_rows, index=blanks.index)
    threshold_failures = pd.DataFrame(threshold_rows, index=blanks.index)
    mdl_failures.index.name = "date_time"
    threshold_failures.index.name = "date_time"

    n_mdl = (mdl_failures.drop(columns="filename") > 0).any(axis=1).sum()
    n_thresh = (threshold_failures.drop(columns="filename") > 0).any(axis=1).sum()
    logger.info(
        "Blank check: %d/%d samples exceeded MDL; %d/%d exceeded %.1f ppbC threshold",
        n_mdl, len(blanks), n_thresh, len(blanks), threshold_ppbc,
    )

    return mdl_failures, threshold_failures
