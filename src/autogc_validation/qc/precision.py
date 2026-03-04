# -*- coding: utf-8 -*-
"""
CVS precision check for AutoGC validation.

Identifies back-to-back CVS runs and computes the Relative Percent
Difference (RPD) between compound concentrations.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_PRECISION_THRESHOLD = 25.0  # percent


def check_cvs_precision(
    cvs_df: pd.DataFrame,
    threshold: float = _PRECISION_THRESHOLD,
    max_gap_hours: float = 1.0,
) -> tuple[pd.DataFrame, list[tuple[pd.Timestamp, pd.Timestamp]]]:
    """Find back-to-back CVS runs and flag compounds with RPD > threshold.

    Two consecutive CVS samples are considered "back-to-back" when the gap
    between them is ≤ max_gap_hours. Since AutoGC samples are collected
    hourly, back-to-back precision runs occupy consecutive hourly slots and
    will always be exactly 1 hour apart, so the default is 1 hour.

    For each pair the Relative Percent Difference (RPD) is computed per
    compound:

        RPD = |A − B| / ((A + B) / 2) × 100 %

    A compound is flagged (value = 1) when its RPD exceeds the threshold.
    Compounds where either sample is NaN, or where both values are zero,
    are left as 0 (not flagged).

    Args:
        cvs_df: Dataset.cvs DataFrame — DatetimeIndex, integer AQS code
            columns, 'sample_type', and 'filename' columns.
        threshold: RPD threshold in percent. Default 25.0.
        max_gap_hours: Maximum hours between consecutive CVS samples to be
            considered back-to-back. Default 1.0 (one hourly sample period).

    Returns:
        Tuple of:
            precision_failures: DataFrame indexed by the first-run timestamp
                of each back-to-back pair. Columns: 'filename' (first run) +
                integer AQS codes. Values: 1 if RPD > threshold, 0 otherwise.
            pairs: List of (t1, t2) Timestamp tuples, one per back-to-back
                pair, in chronological order.
    """
    compound_cols = [c for c in cvs_df.columns if isinstance(c, int)]
    timestamps = cvs_df.index.sort_values().tolist()

    # Identify back-to-back pairs.  Consume both timestamps when a pair is
    # found so that runs of 3+ consecutive samples form (T1,T2) with T3 left
    # as a potential start of the next pair.
    pairs: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    i = 0
    while i < len(timestamps) - 1:
        t1, t2 = timestamps[i], timestamps[i + 1]
        if (t2 - t1).total_seconds() / 3600 <= max_gap_hours:
            pairs.append((t1, t2))
            i += 2
        else:
            i += 1

    if not pairs:
        logger.info("No back-to-back CVS pairs found")
        empty = pd.DataFrame(columns=["filename"] + compound_cols)
        empty.index.name = "date_time"
        return empty, []

    logger.info("Found %d back-to-back CVS pair(s)", len(pairs))

    rows = []
    for t1, t2 in pairs:
        row1 = cvs_df.loc[t1]
        row2 = cvs_df.loc[t2]

        # Guard against a duplicate index returning a DataFrame instead of Series.
        if isinstance(row1, pd.DataFrame):
            row1 = row1.iloc[0]
        if isinstance(row2, pd.DataFrame):
            row2 = row2.iloc[0]

        fail_dict: dict = {"filename": row1["filename"]}
        for code in compound_cols:
            a = row1[code]
            b = row2[code]
            if pd.isna(a) or pd.isna(b) or (a + b) == 0:
                rpd = float("nan")
            else:
                rpd = abs(a - b) / ((a + b) / 2) * 100.0
            fail_dict[code] = 1 if (not pd.isna(rpd) and rpd > threshold) else 0

        rows.append(fail_dict)

    pair_timestamps = pd.DatetimeIndex([t1 for t1, _ in pairs], name="date_time")
    precision_failures = pd.DataFrame(rows, index=pair_timestamps)

    n_fail = int((precision_failures[compound_cols] == 1).any(axis=1).sum())
    logger.info(
        "CVS precision: %d/%d pair(s) have ≥1 compound exceeding %.1f%% RPD",
        n_fail, len(pairs), threshold,
    )
    return precision_failures, pairs
