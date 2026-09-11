# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 09:22:17 2026

@author: aengstrom &
Claude ai  
"""

from autogc_validation.database.enums import PLOT_CODES, BP_CODES
import logging
from pathlib import Path
import os

import pandas as pd
from aqs_tools import generate_aqs_df, combine_quals
from autogc_validation.database.enums import aqs_to_name
from autogc_validation.qc.utils import align_period_index
logger = logging.getLogger(__name__)

_FORMAT = "%Y%m%d %H:%M"


def _aqs_timestamp(aqs_df: pd.DataFrame, date_col: str = "Sample Date", time_col: str = "Sample Begin Time") -> pd.DataFrame:
    aqs_df_ts = aqs_df.copy()
    aqs_df_ts["date_time"] = aqs_df_ts[date_col] + " " + aqs_df_ts[time_col]
    aqs_df_ts["date_time"] = pd.to_datetime(aqs_df_ts["date_time"], format=_FORMAT)
    aqs_df_ts.set_index("date_time", inplace=True)
    return aqs_df_ts


def _compare_aqs_to_dataset(
    aqs_upload_file: str,
    dataset: pd.DataFrame,
    transaction_type: str,
    date_col: str,
    time_col: str,
    value_col: str,
) -> pd.DataFrame:
    if not Path(aqs_upload_file).is_file():
        raise FileNotFoundError(f"AQS upload file not found: {aqs_upload_file}")

    dataset = dataset.copy()

    aqs_df = generate_aqs_df(aqs_upload_file, transaction_type=transaction_type)
    aqs_df = _aqs_timestamp(aqs_df, date_col=date_col, time_col=time_col)
    aqs_df = aqs_df[["Parameter", value_col]].apply(pd.to_numeric, errors="coerce")
    aqs_df.rename(columns={value_col: "AQS"}, inplace=True)
    aqs_df.dropna(how="any", inplace=True)
    aqs_df = aqs_df.reset_index()

    # Drop metadata columns. reset_index() promotes the sample_hour index to a
    # column; rename it to date_time to match the AQS DataFrame's join key.
    dataset.drop(columns=["date_time", "sample_type", "sample_type_long", "filename"], inplace=True)
    dataset = (
        dataset.apply(pd.to_numeric, errors="coerce")
        .reset_index()
        .rename(columns={"sample_hour": "date_time"})
        .melt(id_vars="date_time", var_name="Parameter", value_name="dataset")
    )

    combined = pd.merge(aqs_df, dataset, on=["date_time", "Parameter"], how="inner")
    combined = combined.round({"AQS": 3, "dataset": 3})
    combined["diff"] = combined["dataset"] - combined["AQS"]

    threshold = 0.001
    mask = combined["diff"].abs().round(3) > threshold
    return combined[mask]


def compare_aqs_to_dataset(aqs_upload_file: str, dataset: pd.DataFrame) -> pd.DataFrame:
    """Compare an AQS upload file against the dataset to find value discrepancies.

    Args:
        aqs_upload_file: Path to the AQS RD transaction upload file.
        dataset: Ambient-only DataFrame (e.g. ds.ambient) with integer AQS code
            columns, a sample_hour DatetimeIndex, and date_time / sample_type /
            filename columns. Pass through resolve_duplicate_sample_hours() first
            if the month contains any duplicate sample hours.

    Returns:
        DataFrame of rows where |dataset - AQS| > 0.001, with columns:
        date_time, Parameter, AQS, dataset, diff.

    Raises:
        FileNotFoundError: If aqs_upload_file does not exist.
    """
    return _compare_aqs_to_dataset(
        aqs_upload_file,
        dataset,
        transaction_type="RD",
        date_col="Sample Date",
        time_col="Sample Begin Time",
        value_col="Reported Sample Value",
    )


def compare_aqs_blanks_to_dataset(aqs_blank_file: str, dataset: pd.DataFrame) -> pd.DataFrame:
    """Compare an AQS field-blank upload file against the dataset to find value discrepancies.

    Args:
        aqs_blank_file: Path to the AQS RB (field blank) transaction upload file.
        dataset: Blank-only DataFrame (e.g. ds.blanks) with integer AQS code
            columns, a sample_hour DatetimeIndex, and date_time / sample_type /
            filename columns. Pass through resolve_duplicate_sample_hours() first
            if the month contains any duplicate sample hours.

    Returns:
        DataFrame of rows where |dataset - AQS| > 0.001, with columns:
        date_time, Parameter, AQS, dataset, diff.

    Raises:
        FileNotFoundError: If aqs_blank_file does not exist.
    """
    return _compare_aqs_to_dataset(
        aqs_blank_file,
        dataset,
        transaction_type="RB",
        date_col="Blank Date",
        time_col="Blank Time",
        value_col="Blank Value",
    )

TIME_FMT = '%Y%m%d%H:%M'

def check_eh(aqs_upload_file: os.PathLike, upper_cal_point_plot: float, upper_cal_point_bp: float) -> dict:
    aqs_df = generate_aqs_df(aqs_upload_file, "RD")
    aqs_df = combine_quals(aqs_df)

    false_positive = aqs_df.loc[
        (aqs_df['quals'].apply(lambda x: "EH" in x)) &
        (((aqs_df["Reported Sample Value"].astype(float) < upper_cal_point_plot) & aqs_df["Parameter"].astype(int).isin(PLOT_CODES)) |
        ((aqs_df["Reported Sample Value"].astype(float) < upper_cal_point_bp) & aqs_df["Parameter"].astype(int).isin(BP_CODES)))
    ].copy()

    false_negative = aqs_df.loc[
        (aqs_df['quals'].apply(lambda x: "EH" not in x)) &
        (((aqs_df["Reported Sample Value"].astype(float) > upper_cal_point_plot) & aqs_df["Parameter"].astype(int).isin(PLOT_CODES)) |
        ((aqs_df["Reported Sample Value"].astype(float) > upper_cal_point_bp) & aqs_df["Parameter"].astype(int).isin(BP_CODES)))
    ].copy()

    for df in [false_positive, false_negative]:
        df["date"] = pd.to_datetime(
            df["Sample Date"] + df["Sample Begin Time"],
            format=TIME_FMT
        )

    return {
        "false_positive": false_positive[["date", "Parameter", "Reported Sample Value"]],
        "false_negative": false_negative[["date", "Parameter", "Reported Sample Value"]],
    }

def check_nd(aqs_upload_file: os.PathLike) -> dict:
    aqs_df = generate_aqs_df(aqs_upload_file, "RD")
    aqs_df = combine_quals(aqs_df)

    false_positive = aqs_df.loc[
        (aqs_df['quals'].apply(lambda x: "ND" in x)) &
        (aqs_df["Reported Sample Value"].astype(float) > 0)
    ].copy()

    false_negative = aqs_df.loc[
        (aqs_df['quals'].apply(lambda x: "ND" not in x)) &
        (aqs_df["Null Data Code"].isna()) &
        (aqs_df["Reported Sample Value"].astype(float) <= 0)     
    ].copy()

    for df in [false_positive, false_negative]:
        df["date"] = pd.to_datetime(
            df["Sample Date"] + df["Sample Begin Time"],
            format=TIME_FMT
        )

    return {
        "false_positive": false_positive[["date", "Parameter", "Reported Sample Value"]],
        "false_negative": false_negative[["date", "Parameter", "Reported Sample Value"]],
    }

def check_md(aqs_upload_file: os.PathLike, mdl_periods: pd.DataFrame) -> dict:
    """Check whether "MD" (below detection limit) qualifiers are correctly applied.

    Compares each sample value against the MDL active at that timestamp to
    identify false positives (flagged MD but value >= MDL) and false negatives
    (not flagged MD, not nulled, positive value, but value < MDL).

    Args:
        aqs_upload_file: Path to the AQS RD transaction upload file.
        mdl_periods: Wide DataFrame of MDLs indexed by date with integer AQS
            code columns, as returned by get_mdl_periods. Parameters absent
            from mdl_periods (e.g. totals) receive NaN for effective_mdl and
            are excluded from the false-negative check automatically.

    Returns:
        Dict with keys "false_positive" and "false_negative", each a DataFrame
        with columns: date, Parameter, Reported Sample Value, effective_mdl.
    """
    aqs_df = generate_aqs_df(aqs_upload_file, "RD")
    aqs_df = combine_quals(aqs_df)
    aqs_df["date"] = pd.to_datetime(
        aqs_df["Sample Date"] + aqs_df["Sample Begin Time"],
        format=TIME_FMT
    )
    aqs_df = aqs_df.set_index("date")

    period_indices = align_period_index(aqs_df, mdl_periods)

    mdl_long = (
        mdl_periods.stack()
        .rename_axis(["period_date", "Parameter"])
        .reset_index(name="effective_mdl")
    )
    mdl_long["Parameter"] = mdl_long["Parameter"].astype(str)

    aqs_df = aqs_df.reset_index()
    aqs_df["period_date"] = mdl_periods.index[period_indices]

    merged = aqs_df.merge(mdl_long, on=["period_date", "Parameter"], how="left")

    val = merged["Reported Sample Value"].astype(float)

    false_positive = merged.loc[
        (merged["quals"].apply(lambda x: "MD" in x)) &
        (val >= merged["effective_mdl"])
    ].copy()

    false_negative = merged.loc[
        (merged["quals"].apply(lambda x: "MD" not in x)) &
        (merged["Null Data Code"].isna()) &
        (val > 0) &
        (val < merged["effective_mdl"])
    ].copy()

    out_cols = ["date", "Parameter", "Reported Sample Value", "effective_mdl"]
    return {
        "false_positive": false_positive[out_cols],
        "false_negative": false_negative[out_cols],
    }


_SQL_MULTIPLIER = 3.18


def check_sq(aqs_upload_file: os.PathLike, mdl_periods: pd.DataFrame) -> dict:
    """Check whether "SQ" (below sample quantitation limit) qualifiers are correctly applied.

    The SQL is defined as 3.18 × MDL. Values in the range [MDL, SQL) should
    carry the SQ qualifier.

    Args:
        aqs_upload_file: Path to the AQS RD transaction upload file.
        mdl_periods: Wide DataFrame of MDLs indexed by date with integer AQS
            code columns, as returned by get_mdl_periods.

    Returns:
        Dict with keys "false_positive" and "false_negative", each a DataFrame
        with columns: date, Parameter, Reported Sample Value, effective_mdl, effective_sql.
    """
    aqs_df = generate_aqs_df(aqs_upload_file, "RD")
    aqs_df = combine_quals(aqs_df)
    aqs_df["date"] = pd.to_datetime(
        aqs_df["Sample Date"] + aqs_df["Sample Begin Time"],
        format=TIME_FMT
    )
    aqs_df = aqs_df.set_index("date")

    period_indices = align_period_index(aqs_df, mdl_periods)

    mdl_long = (
        mdl_periods.stack()
        .rename_axis(["period_date", "Parameter"])
        .reset_index(name="effective_mdl")
    )
    mdl_long["Parameter"] = mdl_long["Parameter"].astype(str)
    mdl_long["effective_sql"] = mdl_long["effective_mdl"] * _SQL_MULTIPLIER

    aqs_df = aqs_df.reset_index()
    aqs_df["period_date"] = mdl_periods.index[period_indices]

    merged = aqs_df.merge(mdl_long, on=["period_date", "Parameter"], how="left")

    val = merged["Reported Sample Value"].astype(float)

    false_positive = merged.loc[
        (merged["quals"].apply(lambda x: "SQ" in x)) &
        ((val < merged["effective_mdl"]) | (val >= merged["effective_sql"]))
    ].copy()

    false_negative = merged.loc[
        (merged["quals"].apply(lambda x: "SQ" not in x)) &
        (merged["Null Data Code"].isna()) &
        (val >= merged["effective_mdl"]) &
        (val < merged["effective_sql"])
    ].copy()

    out_cols = ["date", "Parameter", "Reported Sample Value", "effective_mdl", "effective_sql"]
    return {
        "false_positive": false_positive[out_cols],
        "false_negative": false_negative[out_cols],
    }
