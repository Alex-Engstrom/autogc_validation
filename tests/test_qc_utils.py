# -*- coding: utf-8 -*-
"""Tests for qc.utils — shared utilities for QC analysis."""

import math

import numpy as np
import pytest
import pandas as pd

from autogc_validation.database.enums import (
    CompoundAQSCode, ColumnType, TOTAL_CODES, UNID_CODES, get_codes_by_column,
)
from autogc_validation.qc.utils import (
    to_aqs_indexed_series,
    _safe_name_to_aqs,
    get_compound_cols,
    get_ordered_codes,
    align_period_index,
)


class TestSafeNameToAqs:
    def test_int_passthrough(self):
        assert _safe_name_to_aqs(45201) == 45201

    def test_valid_string(self):
        assert _safe_name_to_aqs("Benzene") == 45201

    def test_unknown_string_raises(self):
        with pytest.raises(ValueError, match="Unknown compound name"):
            _safe_name_to_aqs("FakeCompound")


class TestToAqsIndexedSeries:
    def test_string_keys(self):
        result = to_aqs_indexed_series({"Benzene": 1.5, "Ethane": 2.0})
        assert result[CompoundAQSCode.C_BENZENE] == 1.5
        assert result[CompoundAQSCode.C_ETHANE] == 2.0

    def test_int_keys(self):
        result = to_aqs_indexed_series({45201: 1.5, 43202: 2.0})
        assert result[45201] == 1.5
        assert result[43202] == 2.0

    def test_mixed_keys(self):
        result = to_aqs_indexed_series({"Benzene": 1.5, 43202: 2.0})
        assert result[CompoundAQSCode.C_BENZENE] == 1.5
        assert result[CompoundAQSCode.C_ETHANE] == 2.0

    def test_nan_values_dropped(self):
        result = to_aqs_indexed_series({45201: 1.5, 43202: float("nan")})
        assert 43202 not in result.index
        assert len(result) == 1

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown compound name"):
            to_aqs_indexed_series({"NotReal": 1.0})

    def test_empty_dict(self):
        result = to_aqs_indexed_series({})
        assert len(result) == 0

    def test_wide_dataframe_single_row(self):
        """Single-row wide DataFrame with int columns → correct Series."""
        df = pd.DataFrame({45201: [1.5], 43202: [2.0]})
        result = to_aqs_indexed_series(df)
        assert result[45201] == pytest.approx(1.5)
        assert result[43202] == pytest.approx(2.0)

    def test_wide_dataframe_nan_dropped(self):
        """NaN values in wide DataFrame are dropped."""
        df = pd.DataFrame({45201: [1.5], 43202: [float("nan")]})
        result = to_aqs_indexed_series(df)
        assert 43202 not in result.index
        assert len(result) == 1


class TestGetCompoundCols:
    def test_returns_integer_columns(self):
        df = pd.DataFrame({45201: [1.0], 43202: [2.0], "sample_type": ["b"]})
        result = get_compound_cols(df)
        assert 45201 in result
        assert 43202 in result
        assert "sample_type" not in result

    def test_excludes_total_codes(self):
        total_code = next(iter(TOTAL_CODES))
        df = pd.DataFrame({total_code: [1.0], 43202: [2.0]})
        result = get_compound_cols(df)
        assert total_code not in result
        assert 43202 in result

    def test_excludes_unid_codes(self):
        unid_code = next(iter(UNID_CODES))
        df = pd.DataFrame({unid_code: [1.0], 43202: [2.0]})
        result = get_compound_cols(df)
        assert unid_code not in result
        assert 43202 in result

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame({"sample_type": ["b"]})
        result = get_compound_cols(df)
        assert result == []


class TestAlignPeriodIndex:
    def _make_periods(self, dates):
        return pd.DataFrame(
            {45201: [1.0] * len(dates)},
            index=pd.DatetimeIndex(dates),
        )

    def test_single_period_all_map_to_zero(self):
        periods = self._make_periods(["2026-01-01"])
        samples = pd.DataFrame(index=pd.DatetimeIndex([
            "2026-01-05", "2026-01-15", "2026-01-25",
        ]))
        result = align_period_index(samples, periods)
        assert list(result) == [0, 0, 0]

    def test_two_periods_correct_split(self):
        periods = self._make_periods(["2026-01-01", "2026-01-15"])
        samples = pd.DataFrame(index=pd.DatetimeIndex([
            "2026-01-05",   # period 0
            "2026-01-15",   # period 1 (exact boundary → new period)
            "2026-01-20",   # period 1
        ]))
        result = align_period_index(samples, periods)
        assert list(result) == [0, 1, 1]

    def test_sample_before_first_period_clips_to_zero(self):
        periods = self._make_periods(["2026-01-10"])
        samples = pd.DataFrame(index=pd.DatetimeIndex(["2026-01-05"]))
        result = align_period_index(samples, periods)
        assert result[0] == 0

    def test_returns_ndarray(self):
        periods = self._make_periods(["2026-01-01"])
        samples = pd.DataFrame(index=pd.DatetimeIndex(["2026-01-05"]))
        result = align_period_index(samples, periods)
        assert isinstance(result, np.ndarray)

    def test_values_within_valid_range(self):
        periods = self._make_periods(["2026-01-01", "2026-01-15", "2026-01-25"])
        samples = pd.DataFrame(index=pd.date_range("2026-01-01", periods=30, freq="D"))
        result = align_period_index(samples, periods)
        assert result.min() >= 0
        assert result.max() <= len(periods) - 1


class TestGetOrderedCodes:
    def test_returns_list(self):
        codes = {int(CompoundAQSCode.C_ETHANE), int(CompoundAQSCode.C_BENZENE)}
        result = get_ordered_codes(codes)
        assert isinstance(result, list)

    def test_empty_set_returns_empty(self):
        assert get_ordered_codes(set()) == []

    def test_unknown_code_excluded(self):
        """A code not in PLOT or BP column is not returned."""
        result = get_ordered_codes({9999999})
        assert 9999999 not in result

    def test_only_available_codes_returned(self):
        """Only codes present in the input set appear in the result."""
        plot_codes = get_codes_by_column(ColumnType.PLOT)
        # Use just the first two PLOT codes
        subset = set(plot_codes[:2])
        result = get_ordered_codes(subset)
        assert set(result) == subset

    def test_plot_codes_before_bp_codes(self):
        """PLOT-column codes precede BP-column codes in the result."""
        plot_set = set(get_codes_by_column(ColumnType.PLOT))
        bp_set = set(get_codes_by_column(ColumnType.BP))
        # Pick one code from each column
        plot_code = next(iter(plot_set))
        bp_code = next(iter(bp_set))
        result = get_ordered_codes({plot_code, bp_code})
        assert len(result) == 2
        assert result.index(plot_code) < result.index(bp_code)

    def test_all_standard_codes_returned_when_all_available(self):
        """Passing every PLOT+BP code returns all of them."""
        plot_codes = get_codes_by_column(ColumnType.PLOT)
        bp_codes = get_codes_by_column(ColumnType.BP)
        all_codes = set(plot_codes + bp_codes)
        result = get_ordered_codes(all_codes)
        assert set(result) == all_codes
