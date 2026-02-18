# -*- coding: utf-8 -*-
"""Tests for qc.recovery — QC recovery checks."""

import pytest
import pandas as pd

from autogc_validation.database.enums import CompoundAQSCode
from autogc_validation.qc.recovery import check_qc_recovery, check_qc_recovery_wide


class TestCheckQcRecovery:
    def test_all_within_bounds(self, make_dataset_df, sample_canister_conc):
        """All compounds within 70-130% → ['__NONE__']."""
        blend_ratio = 1.0
        expected = {int(k): v * blend_ratio for k, v in sample_canister_conc.items()}
        # Measured == expected → 100% recovery
        df = make_dataset_df(sample_type="c", values=expected)
        result = check_qc_recovery(df, "c", sample_canister_conc, blend_ratio)
        assert result.iloc[0]["failing_qc"] == ["__NONE__"]

    def test_high_recovery_flagged(self, make_dataset_df, sample_canister_conc):
        """Compound at 140% recovery → flagged."""
        blend_ratio = 1.0
        expected = {int(k): v * blend_ratio for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        expected[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * 1.4
        df = make_dataset_df(sample_type="c", values=expected)
        result = check_qc_recovery(df, "c", sample_canister_conc, blend_ratio)
        assert benzene in result.iloc[0]["failing_qc"]

    def test_low_recovery_flagged(self, make_dataset_df, sample_canister_conc):
        """Compound at 60% recovery → flagged."""
        blend_ratio = 1.0
        expected = {int(k): v * blend_ratio for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        expected[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * 0.6
        df = make_dataset_df(sample_type="c", values=expected)
        result = check_qc_recovery(df, "c", sample_canister_conc, blend_ratio)
        assert benzene in result.iloc[0]["failing_qc"]

    def test_exactly_70_not_flagged(self, make_dataset_df, sample_canister_conc):
        """Compound at exactly 70% → NOT flagged (boundary inclusive)."""
        blend_ratio = 1.0
        expected = {int(k): v * blend_ratio for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        expected[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * 0.70
        df = make_dataset_df(sample_type="c", values=expected)
        result = check_qc_recovery(df, "c", sample_canister_conc, blend_ratio)
        assert benzene not in result.iloc[0]["failing_qc"]

    def test_exactly_130_not_flagged(self, make_dataset_df, sample_canister_conc):
        """Compound at exactly 130% → NOT flagged (boundary inclusive)."""
        blend_ratio = 1.0
        expected = {int(k): v * blend_ratio for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        expected[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * 1.30
        df = make_dataset_df(sample_type="c", values=expected)
        result = check_qc_recovery(df, "c", sample_canister_conc, blend_ratio)
        assert benzene not in result.iloc[0]["failing_qc"]

    def test_invalid_qc_type_raises(self, make_dataset_df, sample_canister_conc):
        """Invalid qc_type raises ValueError."""
        df = make_dataset_df(sample_type="c", values={})
        with pytest.raises(ValueError, match="qc_type must be"):
            check_qc_recovery(df, "z", sample_canister_conc, 1.0)

    def test_compounds_not_in_canister_skipped(self, make_dataset_df):
        """Compounds not in canister dict → skipped (partial canister)."""
        # Only provide canister conc for benzene
        partial_canister = {CompoundAQSCode.C_BENZENE: 10.0}
        blend_ratio = 1.0
        # Ethane has a measured value but no expected → should not be flagged
        values = {
            int(CompoundAQSCode.C_BENZENE): 10.0,
            int(CompoundAQSCode.C_ETHANE): 999.0,  # would fail if checked
        }
        df = make_dataset_df(sample_type="c", values=values)
        result = check_qc_recovery(df, "c", partial_canister, blend_ratio)
        failing = result.iloc[0]["failing_qc"]
        assert int(CompoundAQSCode.C_ETHANE) not in failing


class TestCheckQcRecoveryWide:
    def test_wide_format_matrix(self, make_dataset_df, sample_canister_conc):
        """Wide format produces correct 0/1 matrix."""
        blend_ratio = 1.0
        expected = {int(k): v * blend_ratio for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        expected[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * 1.5  # fail
        df = make_dataset_df(sample_type="c", values=expected)
        result = check_qc_recovery_wide(df, "c", sample_canister_conc, blend_ratio)
        assert benzene in result.columns
        assert result.iloc[0][benzene] == 1
