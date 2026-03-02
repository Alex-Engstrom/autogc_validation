# -*- coding: utf-8 -*-
"""
QC recovery checks for CVS, RTS, and LCS samples.

Compares measured concentrations against expected canister concentrations
(dilution already applied by get_canister_periods) and flags compounds
outside the acceptable recovery window (70%–130%).
"""

import logging

import pandas as pd

from autogc_validation.database.enums import SampleType
from autogc_validation.qc.utils import get_compound_cols, align_period_index

_QC_SAMPLE_TYPES = {SampleType.CVS, SampleType.LCS, SampleType.RTS}

logger = logging.getLogger(__name__)

RECOVERY_LOWER_BOUND = 0.70
RECOVERY_UPPER_BOUND = 1.30


def check_qc_recovery(
    qc_samples: pd.DataFrame,
    canister_periods: pd.DataFrame,
) -> pd.DataFrame:
    """Check QC sample recovery against expected canister concentrations.

    Accepts a typed QC DataFrame (from Dataset.cvs, Dataset.rts, or
    Dataset.lcs) and a date-indexed wide canister concentrations DataFrame
    (from get_canister_periods). Internally aligns each sample to the
    canister period active on its collection date.

    Expected concentrations are the diluted canister concentrations as
    stored in the database (dilution ratio already applied by
    get_active_canister_concentrations).

    Recovery is calculated as: observed / expected.
    A compound fails if recovery < 70% or > 130%.

    Args:
        qc_samples: Typed QC DataFrame — DatetimeIndex, AQS code columns,
            filename column. Must have attrs["sample_type"] in
            {SampleType.CVS, SampleType.LCS, SampleType.RTS}.
        canister_periods: Wide DataFrame with DatetimeIndex (one row per
            canister period) and AQS codes as columns, as returned by
            get_canister_periods.

    Returns:
        Wide boolean DataFrame — 1 where recovery is outside [70%, 130%],
        0 otherwise. Columns: filename + AQS codes. Index: date_time.

    Raises:
        ValueError: If qc_samples.attrs["sample_type"] is not a recognised
            QC sample type.
    """
    sample_type = qc_samples.attrs.get("sample_type")
    if sample_type not in _QC_SAMPLE_TYPES:
        raise ValueError(
            f"Expected a QC samples DataFrame with attrs['sample_type'] in "
            f"{{{', '.join(str(t) for t in _QC_SAMPLE_TYPES)}}}, got {sample_type!r}"
        )

    if qc_samples.empty:
        logger.info("Recovery check (%s): no samples found", sample_type)
        return pd.DataFrame(columns=["filename"])

    compound_cols = get_compound_cols(qc_samples)
    period_indices = align_period_index(qc_samples, canister_periods)

    result_rows = []

    for i, (timestamp, row) in enumerate(qc_samples.iterrows()):
        effective_conc = canister_periods.iloc[period_indices[i]]

        flags = {"filename": row["filename"]}

        for code in compound_cols:
            observed = row[code]
            expected = effective_conc.get(code)

            if (pd.isna(observed)
                    or expected is None
                    or pd.isna(expected)
                    or float(expected) == 0):
                flags[code] = 0
                continue

            recovery = float(observed) / float(expected)
            flags[code] = int(
                recovery < RECOVERY_LOWER_BOUND or recovery > RECOVERY_UPPER_BOUND
            )

        result_rows.append(flags)

    result = pd.DataFrame(result_rows, index=qc_samples.index)
    result.index.name = "date_time"

    n_failures = (result.drop(columns="filename") > 0).any(axis=1).sum()
    logger.info(
        "Recovery check (%s): %d/%d samples had compound failures",
        sample_type, n_failures, len(qc_samples),
    )

    return result
