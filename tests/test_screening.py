# -*- coding: utf-8 -*-
"""Tests for qc.screening — ambient data screening checks."""

import pandas as pd
import pytest

import numpy as np

from autogc_validation.database.enums import CompoundAQSCode, VOCCategory, get_codes_by_category, TOTAL_CODES
from autogc_validation.qc.screening import (
    check_overrange_values,
    check_daily_max_tnmhc,
    check_ratios,
    check_lognormal_outliers,
)


def _build_full_ambient_df(overrides=None, n_rows=1, start="2026-01-15 08:00:00"):
    """Build an ambient DataFrame with all CompoundAQSCode columns."""
    all_codes = list(CompoundAQSCode)
    timestamps = pd.date_range(start, periods=n_rows, freq="h")
    rows = []
    for i, ts in enumerate(timestamps):
        row = {"date_time": ts, "sample_type": "s", "filename": f"TESTS{i:02d}A"}
        for code in all_codes:
            row[int(code)] = 1.0  # safe default
        if overrides:
            row.update(overrides)
        rows.append(row)
    return pd.DataFrame(rows).set_index("date_time")


class TestCheckOverrangeValues:
    def test_value_above_upper_cal_flagged(self):
        benzene = int(CompoundAQSCode.C_BENZENE)
        df = _build_full_ambient_df({benzene: 50.0})
        result = check_overrange_values(df, upper_cal_point_plot=30.0, upper_cal_point_bp=30.0)
        assert benzene in result["compound"].values

    def test_tnmhc_excluded_by_default(self):
        tnmhc = int(CompoundAQSCode.C_TNMHC)
        df = _build_full_ambient_df({tnmhc: 500.0})
        result = check_overrange_values(df, upper_cal_point_plot=30.0, upper_cal_point_bp=30.0)
        assert tnmhc not in result["compound"].values

    def test_tnmtc_excluded_by_default(self):
        tnmtc = int(CompoundAQSCode.C_TNMTC)
        df = _build_full_ambient_df({tnmtc: 500.0})
        result = check_overrange_values(df, upper_cal_point_plot=30.0, upper_cal_point_bp=30.0)
        assert tnmtc not in result["compound"].values

    def test_no_exceedance_empty_result(self):
        df = _build_full_ambient_df()  # all values 1.0
        result = check_overrange_values(df, upper_cal_point_plot=30.0, upper_cal_point_bp=30.0)
        assert len(result) == 0


    def test_empty_dataframe_returns_empty(self):
        """Empty DataFrame (no ambient rows) → empty result."""
        all_codes = list(CompoundAQSCode)
        df = pd.DataFrame(
            columns=["sample_type", "filename"] + [int(c) for c in all_codes]
        )
        df.index.name = "date_time"
        result = check_overrange_values(df, upper_cal_point_plot=30.0, upper_cal_point_bp=30.0)
        assert len(result) == 0


class TestCheckDailyMaxTnmhc:
    def test_returns_correct_daily_max(self):
        tnmhc = int(CompoundAQSCode.C_TNMHC)
        df = _build_full_ambient_df({tnmhc: 100.0}, n_rows=3)
        # Override second row to be higher
        df.iloc[1, df.columns.get_loc(tnmhc)] = 200.0
        result = check_daily_max_tnmhc(df)
        assert len(result) == 1  # all same day
        assert result.iloc[0] == 200.0

    def test_multiple_days(self):
        tnmhc = int(CompoundAQSCode.C_TNMHC)
        df1 = _build_full_ambient_df({tnmhc: 100.0}, n_rows=1, start="2026-01-15 08:00")
        df2 = _build_full_ambient_df({tnmhc: 200.0}, n_rows=1, start="2026-01-16 08:00")
        df = pd.concat([df1, df2])
        result = check_daily_max_tnmhc(df)
        assert len(result) == 2


class TestCheckRatios:
    def _full_mdls(self):
        """Build MDLs for all compounds (low values so conditions can trigger)."""
        return {int(code): 0.05 for code in CompoundAQSCode}

    def test_benzene_gt_toluene_triggers(self):
        """benzene > toluene condition triggers when benzene is high and above 3x MDL."""
        C = CompoundAQSCode
        overrides = {
            int(C.C_BENZENE): 60.0,   # benzene/6 = 10
            int(C.C_TOLUENE): 7.0,    # toluene/7 = 1  → benzene > toluene in ppb
        }
        df = _build_full_ambient_df(overrides)
        result = check_ratios(df, self._full_mdls())
        assert "benzene_gt_toluene" in result["screen_reason"].values

    def test_no_flag_below_3x_mdl(self):
        """Condition NOT triggered when primary compound below 3x MDL threshold."""
        C = CompoundAQSCode
        mdls = self._full_mdls()
        mdls[int(C.C_BENZENE)] = 100.0  # MDL so high that 3*MDL is never exceeded
        overrides = {
            int(C.C_BENZENE): 60.0,
            int(C.C_TOLUENE): 7.0,
        }
        df = _build_full_ambient_df(overrides)
        result = check_ratios(df, mdls)
        assert "benzene_gt_toluene" not in result.get("screen_reason", pd.Series()).values

    def test_empty_dataframe_returns_empty(self):
        """Empty DataFrame (no ambient rows) → empty result."""
        all_codes = list(CompoundAQSCode)
        df = pd.DataFrame(
            columns=["sample_type", "filename"] + [int(c) for c in all_codes]
        )
        df.index.name = "date_time"
        result = check_ratios(df, self._full_mdls())
        assert len(result) == 0
        assert "screen_reason" in result.columns

    def test_empty_result_when_no_conditions_met(self):
        """Empty DataFrame returned when no conditions are met."""
        # All values equal and low → no ratio flags
        df = _build_full_ambient_df()  # all 1.0
        mdls = self._full_mdls()
        # Set all MDLs high so 3x threshold is never met
        mdls = {code: 10.0 for code in mdls}
        result = check_ratios(df, mdls)
        assert len(result) == 0
        assert "screen_reason" in result.columns
        assert "compounds" in result.columns


def _build_lognormal_ambient_df(code, normal_values, outlier_value=None, start="2026-01-15 08:00"):
    """Build a minimal ambient DataFrame for lognormal outlier tests.

    All compounds except *code* are set to 1.0. *code* gets *normal_values*
    (list) and optionally one appended *outlier_value* at the next timestamp.
    """
    all_codes = list(CompoundAQSCode)
    n = len(normal_values) + (1 if outlier_value is not None else 0)
    timestamps = pd.date_range(start, periods=n, freq="h")
    rows = []
    all_v = normal_values + ([outlier_value] if outlier_value is not None else [])
    for i, (ts, v) in enumerate(zip(timestamps, all_v)):
        row = {"date_time": ts, "sample_type": "s", "filename": f"TEST{i:02d}A"}
        for c in all_codes:
            row[int(c)] = 1.0
        row[int(code)] = v
        rows.append(row)
    return pd.DataFrame(rows).set_index("date_time")


class TestCheckLognormalOutliers:
    _CODE = CompoundAQSCode.C_BENZENE

    def _normal_values(self):
        return [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

    def test_clear_outlier_detected(self):
        """A value far above the rest is flagged as an outlier."""
        df = _build_lognormal_ambient_df(self._CODE, self._normal_values(), outlier_value=1000.0)
        result = check_lognormal_outliers(df)
        assert int(self._CODE) in result["compound"].values

    def test_no_outliers_returns_empty(self):
        """Values within normal range → empty result."""
        df = _build_lognormal_ambient_df(self._CODE, self._normal_values())
        result = check_lognormal_outliers(df)
        assert result.empty

    def test_result_has_required_columns(self):
        """Result DataFrame always has compound, compound_name, value, threshold columns."""
        df = _build_lognormal_ambient_df(self._CODE, self._normal_values())
        result = check_lognormal_outliers(df)
        for col in ("compound", "compound_name", "value", "threshold"):
            assert col in result.columns

    def test_non_ambient_rows_excluded(self):
        """Blank rows with extreme values are not flagged."""
        code = self._CODE
        all_codes = list(CompoundAQSCode)
        timestamps = pd.date_range("2026-01-15 08:00", periods=13, freq="h")
        rows = []
        normal = self._normal_values()
        for i, (ts, v) in enumerate(zip(timestamps[:12], normal)):
            row = {"date_time": ts, "sample_type": "s", "filename": f"TEST{i:02d}A"}
            for c in all_codes:
                row[int(c)] = 1.0
            row[int(code)] = v
            rows.append(row)
        # 13th row: blank with extreme value
        row = {"date_time": timestamps[12], "sample_type": "b", "filename": "TESTBLK"}
        for c in all_codes:
            row[int(c)] = 1.0
        row[int(code)] = 1000.0
        rows.append(row)
        df = pd.DataFrame(rows).set_index("date_time")
        result = check_lognormal_outliers(df)
        # The extreme blank value should NOT be flagged
        assert result.empty

    def test_total_codes_excluded(self):
        """TNMHC/TNMTC columns are never flagged."""
        tnmhc = CompoundAQSCode.C_TNMHC
        df = _build_lognormal_ambient_df(tnmhc, self._normal_values(), outlier_value=9999.0)
        result = check_lognormal_outliers(df)
        assert int(tnmhc) not in result.get("compound", pd.Series()).values

    def test_compound_with_fewer_than_3_values_skipped(self):
        """Compounds with fewer than 3 non-null values are silently skipped."""
        code = self._CODE
        all_codes = list(CompoundAQSCode)
        timestamps = pd.date_range("2026-01-15 08:00", periods=2, freq="h")
        rows = []
        for i, ts in enumerate(timestamps):
            row = {"date_time": ts, "sample_type": "s", "filename": f"TEST{i:02d}A"}
            for c in all_codes:
                row[int(c)] = 1.0
            row[int(code)] = 1000.0  # extreme but only 2 rows
            rows.append(row)
        df = pd.DataFrame(rows).set_index("date_time")
        result = check_lognormal_outliers(df)
        assert int(code) not in result.get("compound", pd.Series()).values

    def test_mdls_provided_does_not_raise(self):
        """Providing MDLs runs without error and produces the same outlier."""
        df = _build_lognormal_ambient_df(self._CODE, self._normal_values(), outlier_value=1000.0)
        mdls = {int(self._CODE): 0.5}
        result = check_lognormal_outliers(df, mdls=mdls)
        assert int(self._CODE) in result["compound"].values

    def test_custom_k_affects_threshold(self):
        """Higher k means fewer outliers (stricter threshold)."""
        df = _build_lognormal_ambient_df(self._CODE, self._normal_values(), outlier_value=3.0)
        result_loose = check_lognormal_outliers(df, k=1.0)
        result_strict = check_lognormal_outliers(df, k=10.0)
        # k=10 should flag fewer (or equal) samples than k=1
        assert len(result_strict) <= len(result_loose)

    def test_result_indexed_by_timestamp(self):
        """Result index contains the timestamp of the flagged sample."""
        df = _build_lognormal_ambient_df(self._CODE, self._normal_values(), outlier_value=1000.0)
        result = check_lognormal_outliers(df)
        assert not result.empty
        # Index should be a DatetimeIndex
        assert isinstance(result.index, pd.DatetimeIndex)
