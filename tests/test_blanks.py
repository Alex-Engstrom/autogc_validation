# -*- coding: utf-8 -*-
"""Tests for qc.blanks — blank MDL and threshold exceedance checks."""

import numpy as np
import pandas as pd
import pytest

from autogc_validation.database.enums import CompoundAQSCode, ConcentrationUnit, SampleType
from autogc_validation.qc.blanks import compounds_above_mdl


class TestCompoundsAboveMdl:

    # ------------------------------------------------------------------
    # Return type and structure
    # ------------------------------------------------------------------

    def test_returns_tuple_of_two_dataframes(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values)
        result = compounds_above_mdl(blanks, mdl_periods)
        assert isinstance(result, tuple)
        assert len(result) == 2
        mdl_fail, thresh_fail = result
        assert isinstance(mdl_fail, pd.DataFrame)
        assert isinstance(thresh_fail, pd.DataFrame)

    def test_filename_column_in_both_outputs(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        assert "filename" in mdl_fail.columns
        assert "filename" in thresh_fail.columns

    def test_index_is_date_time(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        assert mdl_fail.index.name == "date_time"
        assert thresh_fail.index.name == "date_time"

    # ------------------------------------------------------------------
    # MDL failure flags
    # ------------------------------------------------------------------

    def test_all_below_mdl_all_zeros(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, _ = compounds_above_mdl(blanks, mdl_periods)
        compound_cols = [c for c in mdl_fail.columns if isinstance(c, int)]
        assert (mdl_fail[compound_cols] == 0).all().all()

    def test_compound_above_mdl_flagged(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = 5.0  # well above MDL of 0.05
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, _ = compounds_above_mdl(blanks, mdl_periods)
        assert mdl_fail.iloc[0][benzene] == 1

    def test_other_compounds_not_flagged(self, make_typed_df, sample_mdls, mdl_periods):
        """Only benzene exceeds MDL — other compounds should remain 0."""
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = 5.0
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, _ = compounds_above_mdl(blanks, mdl_periods)
        for code in sample_mdls:
            if int(code) != benzene:
                assert mdl_fail.iloc[0][int(code)] == 0

    def test_exactly_at_mdl_not_flagged(self, make_typed_df, sample_mdls, mdl_periods):
        """Compound exactly equal to MDL is NOT flagged (strict >)."""
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = sample_mdls[CompoundAQSCode.C_BENZENE]
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, _ = compounds_above_mdl(blanks, mdl_periods)
        assert mdl_fail.iloc[0][benzene] == 0

    def test_multiple_compounds_above_mdl(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 5.0 for code in sample_mdls}  # all above MDL
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, _ = compounds_above_mdl(blanks, mdl_periods)
        compound_cols = [c for c in mdl_fail.columns if isinstance(c, int)]
        assert (mdl_fail[compound_cols] == 1).all().all()

    def test_nan_not_flagged_in_mdl(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): np.nan for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values)
        mdl_fail, _ = compounds_above_mdl(blanks, mdl_periods)
        compound_cols = [c for c in mdl_fail.columns if isinstance(c, int)]
        assert (mdl_fail[compound_cols] == 0).all().all()

    # ------------------------------------------------------------------
    # Threshold failure flags
    # ------------------------------------------------------------------

    def test_above_threshold_flagged(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = 0.6  # above 0.5 ppbC threshold
        blanks = make_typed_df(SampleType.BLANK, values=values)
        _, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        assert thresh_fail.iloc[0][benzene] == 1

    def test_below_threshold_not_flagged(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values)
        _, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        compound_cols = [c for c in thresh_fail.columns if isinstance(c, int)]
        assert (thresh_fail[compound_cols] == 0).all().all()

    def test_exactly_at_threshold_not_flagged(self, make_typed_df, sample_mdls, mdl_periods):
        """Compound exactly at 0.5 ppbC is NOT flagged (strict >)."""
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = 0.5
        blanks = make_typed_df(SampleType.BLANK, values=values)
        _, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        assert thresh_fail.iloc[0][benzene] == 0

    def test_nan_not_flagged_in_threshold(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): np.nan for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values)
        _, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        compound_cols = [c for c in thresh_fail.columns if isinstance(c, int)]
        assert (thresh_fail[compound_cols] == 0).all().all()

    # ------------------------------------------------------------------
    # Period alignment
    # ------------------------------------------------------------------

    def test_period_alignment_uses_correct_mdl(self, make_typed_df, sample_mdls):
        """Early sample uses period 1 MDLs; late sample uses period 2 MDLs."""
        benzene = int(CompoundAQSCode.C_BENZENE)

        # Period 1 (Jan 1): benzene MDL = 0.05
        # Period 2 (Jan 15): benzene MDL raised to 1.0
        p1 = {int(code): [val] for code, val in sample_mdls.items()}
        p2 = {int(code): [val] for code, val in sample_mdls.items()}
        p2[benzene] = [1.0]
        two_periods = pd.DataFrame(
            {code: [p1[code][0], p2[code][0]] for code in p1},
            index=pd.DatetimeIndex(["2026-01-01", "2026-01-15"]),
        )
        two_periods.attrs["units"] = ConcentrationUnit.PPBC

        # Benzene at 0.5: above period-1 MDL (0.05) but below period-2 MDL (1.0)
        values = {int(code): 0.01 for code in sample_mdls}
        values[benzene] = 0.5

        early = make_typed_df(SampleType.BLANK, values=values, start_time="2026-01-05 08:00")
        late = make_typed_df(SampleType.BLANK, values=values, start_time="2026-01-20 08:00")
        blanks = pd.concat([early, late])
        blanks.attrs["sample_type"] = SampleType.BLANK

        mdl_fail, _ = compounds_above_mdl(blanks, two_periods)
        assert mdl_fail.iloc[0][benzene] == 1  # Jan 5: fails against period-1 MDL
        assert mdl_fail.iloc[1][benzene] == 0  # Jan 20: passes against period-2 MDL

    def test_sample_on_exact_breakpoint_uses_new_period(self, make_typed_df, sample_mdls):
        """A sample collected exactly on a period boundary uses the new period."""
        benzene = int(CompoundAQSCode.C_BENZENE)

        p1 = {int(code): [val] for code, val in sample_mdls.items()}
        p2 = {int(code): [val] for code, val in sample_mdls.items()}
        p2[benzene] = [1.0]  # raised in period 2
        two_periods = pd.DataFrame(
            {code: [p1[code][0], p2[code][0]] for code in p1},
            index=pd.DatetimeIndex(["2026-01-01", "2026-01-15"]),
        )
        two_periods.attrs["units"] = ConcentrationUnit.PPBC

        values = {int(code): 0.01 for code in sample_mdls}
        values[benzene] = 0.5  # passes period-2 MDL of 1.0

        on_boundary = make_typed_df(
            SampleType.BLANK, values=values, start_time="2026-01-15 00:00"
        )
        on_boundary.attrs["sample_type"] = SampleType.BLANK

        mdl_fail, _ = compounds_above_mdl(on_boundary, two_periods)
        assert mdl_fail.iloc[0][benzene] == 0  # uses period-2 MDL

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_wrong_sample_type_raises(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        ambient = make_typed_df(SampleType.AMBIENT, values=values)
        with pytest.raises(ValueError, match="SampleType.BLANK"):
            compounds_above_mdl(ambient, mdl_periods)

    def test_missing_sample_type_attr_raises(self, make_dataset_df, sample_mdls, mdl_periods):
        """DataFrame without attrs['sample_type'] raises ValueError."""
        values = {int(code): 0.01 for code in sample_mdls}
        df = make_dataset_df(sample_type="b", values=values)
        # attrs not set — sample_type key absent
        with pytest.raises(ValueError):
            compounds_above_mdl(df, mdl_periods)

    def test_empty_df_returns_empty(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values).iloc[0:0]
        blanks.attrs["sample_type"] = SampleType.BLANK
        mdl_fail, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        assert len(mdl_fail) == 0
        assert len(thresh_fail) == 0

    def test_row_count_matches_input(self, make_typed_df, sample_mdls, mdl_periods):
        values = {int(code): 0.01 for code in sample_mdls}
        blanks = make_typed_df(SampleType.BLANK, values=values, n_rows=5)
        mdl_fail, thresh_fail = compounds_above_mdl(blanks, mdl_periods)
        assert len(mdl_fail) == 5
        assert len(thresh_fail) == 5
