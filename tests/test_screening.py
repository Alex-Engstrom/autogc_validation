# -*- coding: utf-8 -*-
"""Tests for qc.screening — ambient data screening checks."""

import pandas as pd
import pytest

from autogc_validation.database.enums import CompoundAQSCode, VOCCategory, get_codes_by_category
from autogc_validation.qc.screening import (
    check_overrange_values,
    check_daily_max_tnmhc,
    check_ratios,
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
        result = check_overrange_values(df, upper_cal_point=30.0)
        assert benzene in result["compound"].values

    def test_tnmhc_excluded_by_default(self):
        tnmhc = int(CompoundAQSCode.C_TNMHC)
        df = _build_full_ambient_df({tnmhc: 500.0})
        result = check_overrange_values(df, upper_cal_point=30.0)
        assert tnmhc not in result["compound"].values

    def test_tnmtc_excluded_by_default(self):
        tnmtc = int(CompoundAQSCode.C_TNMTC)
        df = _build_full_ambient_df({tnmtc: 500.0})
        result = check_overrange_values(df, upper_cal_point=30.0)
        assert tnmtc not in result["compound"].values

    def test_no_exceedance_empty_result(self):
        df = _build_full_ambient_df()  # all values 1.0
        result = check_overrange_values(df, upper_cal_point=30.0)
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
