# -*- coding: utf-8 -*-
"""Tests for dataset.Dataset helper methods (using synthetic DataFrames, no CDF)."""

import pytest
import pandas as pd

from autogc_validation.database.enums import (
    CompoundAQSCode,
    UNID_CODES,
    TOTAL_CODES,
)
from autogc_validation.dataset import Dataset
from autogc_validation.database.enums import SampleType


@pytest.fixture
def dataset_instance(tmp_path):
    """Create a Dataset pointing at an empty folder (no CDF files)."""
    return Dataset(tmp_path)


class TestFilterTargets:
    def test_removes_unid_and_total_codes(self, dataset_instance):
        df = pd.DataFrame({
            "peak_name": [
                int(CompoundAQSCode.C_ETHANE),
                int(CompoundAQSCode.C_BENZENE),
                10000,  # PLOT_UNID
                20000,  # BP_UNID
                int(CompoundAQSCode.C_TNMHC),
                int(CompoundAQSCode.C_TNMTC),
            ],
            "peak_amount": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        })
        result = dataset_instance._filter_targets(df)
        remaining = set(result["peak_name"])
        assert 10000 not in remaining
        assert 20000 not in remaining
        assert int(CompoundAQSCode.C_TNMHC) not in remaining
        assert int(CompoundAQSCode.C_ETHANE) in remaining
        assert int(CompoundAQSCode.C_BENZENE) in remaining


class TestFilterTotals:
    def test_keeps_only_totals(self, dataset_instance):
        df = pd.DataFrame({
            "peak_name": [
                int(CompoundAQSCode.C_ETHANE),
                int(CompoundAQSCode.C_TNMHC),
                int(CompoundAQSCode.C_TNMTC),
            ],
            "peak_amount": [1.0, 50.0, 55.0],
        })
        result = dataset_instance._filter_totals(df)
        remaining = set(result["peak_name"])
        assert remaining == {int(CompoundAQSCode.C_TNMHC), int(CompoundAQSCode.C_TNMTC)}


class TestSumTotals:
    def test_sums_front_back(self, dataset_instance):
        front = pd.DataFrame({
            "peak_name": [int(CompoundAQSCode.C_TNMHC), int(CompoundAQSCode.C_TNMTC)],
            "peak_amount": [10.0, 20.0],
        })
        back = pd.DataFrame({
            "peak_name": [int(CompoundAQSCode.C_TNMHC), int(CompoundAQSCode.C_TNMTC)],
            "peak_amount": [5.0, 8.0],
        })
        result = dataset_instance._sum_totals(front, back)
        assert set(result.columns) == {"peak_name", "peak_amount"}
        tnmhc_row = result[result["peak_name"] == int(CompoundAQSCode.C_TNMHC)]
        assert tnmhc_row["peak_amount"].iloc[0] == 15.0


class TestValidatePeakDf:
    def test_raises_on_missing_columns(self, dataset_instance):
        df = pd.DataFrame({"wrong_col": [1, 2]})
        with pytest.raises(ValueError, match="Malformed peakamounts"):
            dataset_instance._validate_peak_df(df, "test.cdf")

    def test_passes_with_correct_columns(self, dataset_instance):
        df = pd.DataFrame({"peak_name": [1], "peak_amount": [1.0]})
        dataset_instance._validate_peak_df(df, "test.cdf")  # should not raise


class TestGetChemCols:
    def test_excludes_unid_codes(self, dataset_instance):
        cols = dataset_instance._get_chem_cols()
        for unid in UNID_CODES:
            assert unid not in cols

    def test_includes_target_compounds(self, dataset_instance):
        cols = dataset_instance._get_chem_cols()
        assert int(CompoundAQSCode.C_ETHANE) in cols
        assert int(CompoundAQSCode.C_BENZENE) in cols

    def test_includes_totals(self, dataset_instance):
        cols = dataset_instance._get_chem_cols()
        assert int(CompoundAQSCode.C_TNMHC) in cols


class TestFilterByType:
    def test_returns_matching_rows(self, make_dataset_df):
        df_blank = make_dataset_df(sample_type="b", n_rows=2)
        df_ambient = make_dataset_df(
            sample_type="s", n_rows=3, start_time="2026-01-15 10:00:00"
        )
        combined = pd.concat([df_blank, df_ambient])

        # Create a minimal Dataset and inject data
        ds = Dataset.__new__(Dataset)
        ds._data = combined

        result = ds.filter_by_type(SampleType.BLANK)
        assert len(result) == 2
        assert all(result["sample_type"] == "b")
