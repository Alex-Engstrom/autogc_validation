# -*- coding: utf-8 -*-
"""
Retention time outlier detection using Median Absolute Deviation (MAD).
"""

import pandas as pd

from autogc_validation.database.enums import aqs_to_name
from autogc_validation.qc.utils import align_period_index


def detect_rt_outliers(
    df: pd.DataFrame,
    compound_cols: list[int],
    sample_type_col: str = "sample_type",
    filename_col: str = "filename",
    k: float = 10.0,
    direction: str = "both",
    min_abs_shift: float | None = None,
    min_group_size: int = 5,
    concentrations: pd.DataFrame | None = None,
    mdl_periods: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Detect retention time outliers using Median Absolute Deviation (MAD).

    For each sample type group and compound, computes the median RT and MAD,
    then flags samples whose deviation exceeds k * MAD (optionally also
    requiring a minimum absolute shift).

    When both concentrations and mdl_periods are provided, flagged rows are
    additionally filtered to only include samples where the compound
    concentration exceeds its period-aligned MDL. This suppresses RT outlier
    flags for samples near or below the detection limit where RT values are
    unreliable.

    Args:
        df: Dataset.rt DataFrame — DatetimeIndex, integer AQS code columns,
            sample_type and filename columns.
        compound_cols: List of integer AQS codes to check. Use
            get_compound_cols(ds.rt) to obtain this from the Dataset.
        sample_type_col: Column name for sample type grouping. Default
            'sample_type'.
        filename_col: Column name for sample filenames. Default 'filename'.
        k: MAD sensitivity multiplier. Higher values flag only larger
            deviations. Default 10.0.
        direction: 'both' to flag high and low outliers, 'high' for only
            positive deviations, 'low' for only negative. Default 'both'.
        min_abs_shift: Optional minimum absolute RT shift (same units as the
            RT values) required to flag a sample. Applied in addition to the
            MAD threshold.
        min_group_size: Minimum number of samples in a group before MAD is
            computed. Groups smaller than this are skipped. Default 5.
        concentrations: Optional concentration DataFrame (e.g. ds.data) with
            the same DatetimeIndex as df. When provided alongside mdl_periods,
            flagged rows are dropped if the compound concentration is at or
            below its period-aligned MDL.
        mdl_periods: Optional wide MDL DataFrame with DatetimeIndex (one row
            per MDL period) and AQS codes as columns, as returned by
            get_mdl_periods. Required alongside concentrations to enable the
            MDL filter.

    Returns:
        DataFrame of flagged outliers with columns:
            date_time, sample_type, filename, compound, compound_name,
            rt, median_rt, delta, mad, threshold.
        Empty DataFrame (same columns) if no outliers are found.

    Raises:
        ValueError: If direction is not 'both', 'high', or 'low'.
    """
    if direction not in ("both", "high", "low"):
        raise ValueError("direction must be 'both', 'high', or 'low'")

    above_mdl = None
    if concentrations is not None and mdl_periods is not None:
        period_indices = align_period_index(concentrations, mdl_periods)
        effective_mdl_df = mdl_periods.iloc[period_indices].set_index(concentrations.index)
        common_cols = [
            c for c in compound_cols
            if c in concentrations.columns and c in effective_mdl_df.columns
        ]
        above_mdl = concentrations[common_cols] > effective_mdl_df[common_cols]

    flagged_rows = []

    for sample_type, group in df.groupby(sample_type_col):
        if len(group) < min_group_size:
            continue

        for compound in compound_cols:
            values = group[compound].dropna()
            if len(values) < min_group_size:
                continue

            median_rt = values.median()
            mad = (values - median_rt).abs().median()

            if mad == 0:
                continue

            threshold = k * mad
            if min_abs_shift is not None:
                threshold = max(threshold, min_abs_shift)

            delta = values - median_rt

            if direction == "both":
                mask = delta.abs() > threshold
            elif direction == "high":
                mask = delta > threshold
            else:
                mask = delta < -threshold

            for idx in values[mask].index:
                if above_mdl is not None and compound in above_mdl.columns:
                    if idx not in above_mdl.index or not above_mdl.loc[idx, compound]:
                        continue
                flagged_rows.append({
                    "date_time": idx,
                    "sample_type": sample_type,
                    "filename": group.loc[idx, filename_col] if filename_col in group.columns else None,
                    "compound": compound,
                    "compound_name": aqs_to_name(compound),
                    "rt": values.loc[idx],
                    "median_rt": median_rt,
                    "delta": delta.loc[idx],
                    "mad": mad,
                    "threshold": threshold,
                })

    columns = [
        "date_time", "sample_type", "filename", "compound", "compound_name",
        "rt", "median_rt", "delta", "mad", "threshold",
    ]
    if not flagged_rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(flagged_rows).set_index("date_time")
