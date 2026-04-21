# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 09:22:17 2026

@author: aengstrom
"""

import logging
from pathlib import Path

import pandas as pd
from aqs_tools import generate_aqs_df

logger = logging.getLogger(__name__)

_FORMAT = "%Y%m%d %H:%M"


def _aqs_timestamp(aqs_df: pd.DataFrame) -> pd.DataFrame:
    aqs_df_ts = aqs_df.copy()
    aqs_df_ts["date_time"] = aqs_df_ts["Sample Date"] + " " + aqs_df_ts["Sample Begin Time"]
    aqs_df_ts["date_time"] = pd.to_datetime(aqs_df_ts["date_time"], format=_FORMAT)
    aqs_df_ts.set_index("date_time", inplace=True)
    return aqs_df_ts


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
    if not Path(aqs_upload_file).is_file():
        raise FileNotFoundError(f"AQS upload file not found: {aqs_upload_file}")

    dataset = dataset.copy()

    aqs_df = generate_aqs_df(aqs_upload_file, transaction_type="RD")
    aqs_df = _aqs_timestamp(aqs_df)
    aqs_df = aqs_df[["Parameter", "Reported Sample Value"]].apply(pd.to_numeric, errors="coerce")
    aqs_df.rename(columns={"Reported Sample Value": "AQS"}, inplace=True)
    aqs_df.dropna(how="any", inplace=True)
    aqs_df = aqs_df.reset_index()

    # Drop metadata columns. reset_index() promotes the sample_hour index to a
    # column; rename it to date_time to match the AQS DataFrame's join key.
    dataset.drop(columns=["date_time", "sample_type", "filename"], inplace=True)
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
    
    
