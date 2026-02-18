# -*- coding: utf-8 -*-
"""
Dataset — the central data container for AutoGC validation.

Loads chromatogram samples from a folder of CDF files and builds
concentration and retention time DataFrames for downstream QC analysis.
"""

import logging
from pathlib import Path
from typing import List

import pandas as pd

from autogc_validation.database.enums import CompoundAQSCode, SampleType, UNID_CODES, TOTAL_CODES
from autogc_validation.io.samples import Sample, load_samples_from_folder

logger = logging.getLogger(__name__)


class Dataset:
    """Collection of chromatogram samples with concentration and retention time tables.

    Attributes:
        folder: Path to the directory of CDF files.
        samples: List of Sample objects (paired front/back chromatograms).
        data: DataFrame of concentrations (ppbC) indexed by datetime.
        rt: DataFrame of retention times indexed by datetime.
    """

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.samples = load_samples_from_folder(self.folder)
        self._data = None
        self._rt = None

    @property
    def data(self) -> pd.DataFrame:
        """Concentration data, lazily generated on first access."""
        if self._data is None:
            self._data = self._generate_data()
        return self._data

    @property
    def rt(self) -> pd.DataFrame:
        """Retention time data, lazily generated on first access."""
        if self._rt is None:
            self._rt = self._generate_rt()
        return self._rt

    def filter_by_type(self, sample_type: SampleType) -> pd.DataFrame:
        """Return rows of the data DataFrame matching a sample type."""
        return self.data[self.data["sample_type"] == sample_type.value]

    def _get_chem_cols(self) -> List[int]:
        """AQS codes to use as DataFrame columns (excludes UnID)."""
        return [code for code in CompoundAQSCode if code not in UNID_CODES]

    def _filter_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove UnID and total codes from a peak table."""
        return df[~df['peak_name'].isin(UNID_CODES | TOTAL_CODES)]

    def _filter_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select only TNMHC/TNMTC rows from a peak table."""
        return df[df['peak_name'].isin(TOTAL_CODES)]

    def _sum_totals(
        self, front_totals: pd.DataFrame, back_totals: pd.DataFrame
    ) -> pd.DataFrame:
        """Sum TNMHC and TNMTC values from front and back chromatograms."""
        merged = front_totals.merge(
            back_totals, on="peak_name", suffixes=("_front", "_back")
        )
        merged["peak_amount"] = (
            merged["peak_amount_front"] + merged["peak_amount_back"]
        )
        return merged[["peak_name", "peak_amount"]]

    def _build_amount_dict(
        self, front_df: pd.DataFrame, back_df: pd.DataFrame
    ) -> dict:
        """Build a dict mapping AQS code -> peak amount (ppbC)."""
        front_target = self._filter_targets(front_df)
        back_target = self._filter_targets(back_df)

        front_totals = self._filter_totals(front_df)
        back_totals = self._filter_totals(back_df)

        summed = self._sum_totals(front_totals, back_totals)

        voc_amounts = pd.concat(
            [front_target, back_target, summed], ignore_index=True
        )
        return voc_amounts.set_index("peak_name")["peak_amount"].to_dict()

    def _build_rt_dict(
        self, front_df: pd.DataFrame, back_df: pd.DataFrame
    ) -> dict:
        """Build a dict mapping AQS code -> retention time."""
        front_target = self._filter_targets(front_df)
        back_target = self._filter_targets(back_df)

        voc_rt = pd.concat([front_target, back_target], ignore_index=True)
        return voc_rt.set_index("peak_name")["peak_retention_time"].to_dict()

    def _validate_peak_df(self, df: pd.DataFrame, filename) -> None:
        """Raise if a peakamounts DataFrame is missing required columns."""
        if "peak_name" not in df or "peak_amount" not in df:
            raise ValueError(f"Malformed peakamounts table in {filename}")

    def _generate_frame(self, attr: str, builder) -> pd.DataFrame:
        """Generate a DataFrame by extracting an attribute from each sample.

        Args:
            attr: Chromatogram property name ('peakamounts' or 'peaklocations').
            builder: Method that converts front/back DataFrames into a
                {AQS code: value} dict (e.g. _build_amount_dict or _build_rt_dict).
        """
        chem_cols = self._get_chem_cols()
        rows = []
        errors = 0

        for sample in self.samples:
            try:
                dt = sample.front.datetime
                if abs((dt - sample.back.datetime).total_seconds()) > 1:
                    logger.warning(
                        "%s: front/back datetime mismatch", sample.filename_base
                    )
                    continue

                front_df = getattr(sample.front, attr)
                back_df = getattr(sample.back, attr)

                if attr == "peakamounts":
                    self._validate_peak_df(front_df, sample.front.filename)
                    self._validate_peak_df(back_df, sample.back.filename)

                value_dict = builder(front_df, back_df)

                row = {
                    "date_time": dt,
                    "sample_type": sample.sample_type.value,
                    "filename": sample.filename_base,
                    **{code: value_dict.get(code) for code in chem_cols},
                }
                rows.append(row)
            except (ValueError, KeyError, TypeError, OSError):
                logger.exception("Error processing %s", sample.filename_base)
                errors += 1
                continue

        if errors:
            logger.warning(
                "%d of %d samples failed to process", errors, len(self.samples)
            )

        return pd.DataFrame(rows).set_index("date_time")

    def _generate_data(self) -> pd.DataFrame:
        """Generate a DataFrame of VOC concentrations for all samples."""
        return self._generate_frame("peakamounts", self._build_amount_dict)

    def _generate_rt(self) -> pd.DataFrame:
        """Generate a DataFrame of retention times for all samples."""
        return self._generate_frame("peaklocations", self._build_rt_dict)

    def __repr__(self):
        return f"Dataset({self.folder}, n_samples={len(self.samples)})"
