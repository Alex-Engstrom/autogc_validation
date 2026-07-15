# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 10:52:20 2026

@author: aengstrom
"""

from autogc_core.max import figure_to_df
from autogc_validation.database.enums import aqs_to_name, name_to_aqs
from autogc_validation.qc import compute_recovery
from pathlib import Path
import pandas as pd
import os

def compare_qc_recovery(qc_df: pd.DataFrame, canister_periods: pd.DataFrame, orsat_csv: os.PathLike, thresh: float = 0.005)-> pd.DataFrame:
    """Compare locally-computed QC recovery against an independent ORSAT audit.

    Recomputes recovery percentages from ``qc_df`` and diffs them, hour by
    hour and compound by 
    compound, against the recovery percentages reported
    in an ORSAT-exported recovery figure CSV. Both sides are indexed by
    sample hour, so rows are matched by exact timestamp.

    Args:
        qc_df: Typed QC DataFrame (Dataset.cvs, Dataset.lcs, etc.), indexed
            by sample hour.
        canister_periods: Expected concentrations from get_canister_periods,
            used to compute local recovery via compute_recovery.
        orsat_csv: Path to an ORSAT-exported recovery figure CSV (columns
            named like "{compound} (SITE-XX ...) Recovery (%)"), indexed by
            "DATE TIME".
        thresh: Maximum allowed absolute difference (in recovery
            percentage-points) between the ORSAT and locally-computed
            values before a row is flagged.

    Returns:
        Long-format DataFrame with one row per (sample hour, compound) pair
        where |ORSAT recovery - local recovery| > thresh, with columns
        "DATE TIME", "Parameter" (AQS code), and "diff".
    """
    local = compute_recovery(qc_df, canister_periods)
    orsat = figure_to_df(orsat_csv, "recovery")
    cols = [name_to_aqs(col) for col in orsat.columns]
    orsat.columns = cols
    local = local[cols]
    diff = orsat - local
    diff = diff.reset_index().melt(id_vars = "DATE TIME", var_name="Parameter", value_name="diff")
    mask = diff["diff"].apply(abs) > thresh
    
    return diff[mask]         