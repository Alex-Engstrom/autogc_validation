# -*- coding: utf-8 -*-
"""
Blank QC checks.

Identifies compounds in blank samples that exceed their respective MDLs
or a fixed concentration threshold.
"""

import logging

import pandas as pd

from autogc_validation.database.enums import CompoundAQSCode, SampleTypeLetter, aqs_to_name
from autogc_validation.qc.utils import get_compound_cols, align_period_index

logger = logging.getLogger(__name__)

_THRESHOLD_PPBC = 0.5
_TNMHC_THRESHOLD_PPBC = 10.0
_TNMHC_CODE = int(CompoundAQSCode.C_TNMHC)


def compounds_above_mdl(
    blanks: pd.DataFrame,
    mdl_periods: pd.DataFrame,
    threshold_ppbc: float = _THRESHOLD_PPBC,
    tnmhc_threshold_ppbc: float = _TNMHC_THRESHOLD_PPBC,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Check blank samples against MDLs and a fixed concentration threshold.

    Accepts a typed blanks DataFrame (from Dataset.blanks) and a date-indexed
    wide MDL DataFrame (from get_mdl_periods). Internally aligns each sample
    to the MDL period that was active on its collection date.

    TNMHC is checked separately against tnmhc_threshold_ppbc (default 10.0
    ppbC). It is always 0 in mdl_failures (no MDL for a computed total) and
    flagged in threshold_failures when its value exceeds the threshold.

    Args:
        blanks: Dataset.blanks DataFrame — DatetimeIndex, AQS code columns,
            filename column. Must have attrs["sample_type"] == SampleTypeLetter.BLANK.
        mdl_periods: Wide DataFrame with DatetimeIndex (one row per MDL period)
            and AQS codes as columns, as returned by get_mdl_periods.
        threshold_ppbc: Fixed concentration threshold for individual compounds
            (ppbC). Default 0.5.
        tnmhc_threshold_ppbc: Threshold for TNMHC (ppbC). Default 10.0.

    Returns:
        Tuple of (mdl_failures, threshold_failures):
            mdl_failures: Wide boolean DataFrame — 1 where compound > MDL,
                0 otherwise. Columns: filename + AQS codes. Index: sample_hour.
                TNMHC is always 0 (no MDL applies).
            threshold_failures: Wide boolean DataFrame — 1 where compound
                > threshold_ppbc, 0 otherwise. Same shape as mdl_failures.
                TNMHC uses tnmhc_threshold_ppbc instead of threshold_ppbc.

    Raises:
        ValueError: If blanks.attrs["sample_type"] is not SampleTypeLetter.BLANK.
    """
    sample_type = blanks.attrs.get("sample_type")
    if sample_type != SampleTypeLetter.BLANK:
        raise ValueError(
            f"Expected blanks DataFrame with attrs['sample_type'] == SampleTypeLetter.BLANK, "
            f"got {sample_type!r}"
        )

    if blanks.empty:
        logger.info("Blank check: no blank samples found")
        empty = pd.DataFrame(columns=["filename"])
        return empty, empty

    compound_cols = get_compound_cols(blanks)  # excludes TNMHC
    has_tnmhc = _TNMHC_CODE in blanks.columns
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

        if has_tnmhc:
            tnmhc_val = row[_TNMHC_CODE]
            mdl_flags[_TNMHC_CODE] = 0
            threshold_flags[_TNMHC_CODE] = (
                0 if pd.isna(tnmhc_val) else int(tnmhc_val > tnmhc_threshold_ppbc)
            )

        mdl_rows.append(mdl_flags)
        threshold_rows.append(threshold_flags)

    mdl_failures = pd.DataFrame(mdl_rows, index=blanks.index)
    threshold_failures = pd.DataFrame(threshold_rows, index=blanks.index)

    n_mdl = (mdl_failures.drop(columns="filename") > 0).any(axis=1).sum()
    n_thresh = (threshold_failures.drop(columns="filename") > 0).any(axis=1).sum()
    n_tnmhc = int(threshold_failures[_TNMHC_CODE].sum()) if has_tnmhc else 0
    logger.info(
        "Blank check: %d/%d samples exceeded MDL; %d/%d exceeded %.1f ppbC threshold; "
        "%d/%d exceeded TNMHC threshold of %.1f ppbC",
        n_mdl, len(blanks), n_thresh, len(blanks), threshold_ppbc,
        n_tnmhc, len(blanks), tnmhc_threshold_ppbc,
    )

    return mdl_failures, threshold_failures


def blank_exceedance_counts(
    blanks: pd.DataFrame,
    mdl_periods: pd.DataFrame,
) -> pd.DataFrame:
    """Count per-compound MDL exceedances across a month of blank samples.

    Args:
        blanks: Typed blanks DataFrame (Dataset.blanks).
        mdl_periods: MDL values from get_mdl_periods.

    Returns:
        DataFrame with one row, 'above_mdl', and one column per compound
        (named, not AQS-coded), counting samples where the compound's
        concentration exceeded the MDL active for its collection date.
    """
    mdl_failures, _ = compounds_above_mdl(blanks, mdl_periods)
    mdl_failures = mdl_failures.drop(columns="filename")
    mdl_failures.columns = [aqs_to_name(c) for c in mdl_failures.columns]

    above_mdl = mdl_failures.sum(axis=0)
    return pd.DataFrame([above_mdl], index=["above_mdl"])
