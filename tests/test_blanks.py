# -*- coding: utf-8 -*-
"""Tests for qc.blanks — blank MDL exceedance checks."""

import numpy as np
import pandas as pd
import pytest

from autogc_validation.database.enums import CompoundAQSCode
from autogc_validation.qc.blanks import compounds_above_mdl, compounds_above_mdl_wide


class TestCompoundsAboveMdl:
    def test_all_below_mdl(self, make_dataset_df, sample_mdls):
        """All compounds below MDL → ['__NONE__'] in result."""
        values = {int(code): 0.01 for code in sample_mdls}
        df = make_dataset_df(sample_type="b", values=values)
        result = compounds_above_mdl(df, sample_mdls)
        assert result.iloc[0]["compounds_above_mdl"] == ["__NONE__"]

    def test_one_above_mdl(self, make_dataset_df, sample_mdls):
        """One compound above MDL → that code appears in result."""
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = 5.0  # well above MDL of 0.05
        df = make_dataset_df(sample_type="b", values=values)
        result = compounds_above_mdl(df, sample_mdls)
        assert benzene in result.iloc[0]["compounds_above_mdl"]

    def test_multiple_above_mdl(self, make_dataset_df, sample_mdls):
        """Multiple compounds above MDL → all appear in result."""
        values = {int(code): 5.0 for code in sample_mdls}  # all above MDL
        df = make_dataset_df(sample_type="b", values=values)
        result = compounds_above_mdl(df, sample_mdls)
        above = result.iloc[0]["compounds_above_mdl"]
        for code in sample_mdls:
            assert int(code) in above

    def test_exactly_at_mdl_not_flagged(self, make_dataset_df, sample_mdls):
        """Compound exactly at MDL → NOT flagged (must exceed, not equal)."""
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = sample_mdls[CompoundAQSCode.C_BENZENE]  # exactly at MDL
        df = make_dataset_df(sample_type="b", values=values)
        result = compounds_above_mdl(df, sample_mdls)
        assert result.iloc[0]["compounds_above_mdl"] == ["__NONE__"]

    def test_nan_values_skipped(self, make_dataset_df, sample_mdls):
        """NaN values → silently skipped, not flagged."""
        values = {int(code): np.nan for code in sample_mdls}
        df = make_dataset_df(sample_type="b", values=values)
        result = compounds_above_mdl(df, sample_mdls)
        assert result.iloc[0]["compounds_above_mdl"] == ["__NONE__"]

    def test_only_blank_rows_processed(self, make_dataset_df, sample_mdls):
        """Non-blank rows are ignored."""
        values_blank = {int(code): 0.01 for code in sample_mdls}
        values_ambient = {int(code): 50.0 for code in sample_mdls}  # high
        df_blank = make_dataset_df(sample_type="b", values=values_blank, n_rows=1)
        df_ambient = make_dataset_df(
            sample_type="s", values=values_ambient, n_rows=1,
            start_time="2026-01-15 09:00:00",
        )
        df = pd.concat([df_blank, df_ambient])
        result = compounds_above_mdl(df, sample_mdls)
        # Only 1 row (the blank), ambient row is excluded
        assert len(result) == 1
        assert result.iloc[0]["compounds_above_mdl"] == ["__NONE__"]


class TestCompoundsAboveMdlWide:
    def test_wide_format_01_matrix(self, make_dataset_df, sample_mdls):
        """Wide format produces 0/1 matrix."""
        values = {int(code): 0.01 for code in sample_mdls}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = 5.0
        df = make_dataset_df(sample_type="b", values=values)
        result = compounds_above_mdl_wide(df, sample_mdls)
        assert benzene in result.columns
        assert result.iloc[0][benzene] == 1

    def test_none_column_removed(self, make_dataset_df, sample_mdls):
        """__NONE__ column is removed from wide output."""
        values = {int(code): 0.01 for code in sample_mdls}
        df = make_dataset_df(sample_type="b", values=values)
        result = compounds_above_mdl_wide(df, sample_mdls)
        assert "__NONE__" not in result.columns
