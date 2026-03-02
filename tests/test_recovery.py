# -*- coding: utf-8 -*-
"""Tests for qc.recovery — QC recovery checks."""

import pandas as pd
import pytest

from autogc_validation.database.enums import CompoundAQSCode, ConcentrationUnit, SampleType
from autogc_validation.qc.recovery import check_qc_recovery, RECOVERY_LOWER_BOUND, RECOVERY_UPPER_BOUND


class TestCheckQcRecovery:

    # ------------------------------------------------------------------
    # Return type and structure
    # ------------------------------------------------------------------

    def test_returns_dataframe(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert isinstance(result, pd.DataFrame)

    def test_filename_column_in_output(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert "filename" in result.columns

    def test_index_is_date_time(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert result.index.name == "date_time"

    def test_row_count_matches_input(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.CVS, values=values, n_rows=4)
        result = check_qc_recovery(qc, canister_periods)
        assert len(result) == 4

    # ------------------------------------------------------------------
    # Recovery flag logic
    # ------------------------------------------------------------------

    def test_100_percent_recovery_all_zeros(self, make_typed_df, sample_canister_conc, canister_periods):
        """Observed == expected → 100% recovery → all compound flags 0."""
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        compound_cols = [c for c in result.columns if isinstance(c, int)]
        assert (result[compound_cols] == 0).all().all()

    def test_high_recovery_flagged(self, make_typed_df, sample_canister_conc, canister_periods):
        """Compound at 140% recovery → flag = 1."""
        values = {int(k): v for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * 1.4
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert result.iloc[0][benzene] == 1

    def test_low_recovery_flagged(self, make_typed_df, sample_canister_conc, canister_periods):
        """Compound at 60% recovery → flag = 1."""
        values = {int(k): v for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * 0.6
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert result.iloc[0][benzene] == 1

    def test_exactly_at_lower_bound_not_flagged(self, make_typed_df, sample_canister_conc, canister_periods):
        """Compound at exactly 70% recovery → NOT flagged (boundary inclusive)."""
        values = {int(k): v for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * RECOVERY_LOWER_BOUND
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert result.iloc[0][benzene] == 0

    def test_exactly_at_upper_bound_not_flagged(self, make_typed_df, sample_canister_conc, canister_periods):
        """Compound at exactly 130% recovery → NOT flagged (boundary inclusive)."""
        values = {int(k): v for k, v in sample_canister_conc.items()}
        benzene = int(CompoundAQSCode.C_BENZENE)
        values[benzene] = sample_canister_conc[CompoundAQSCode.C_BENZENE] * RECOVERY_UPPER_BOUND
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert result.iloc[0][benzene] == 0

    def test_zero_expected_not_flagged(self, make_typed_df, sample_canister_conc):
        """Zero expected concentration → skipped, no ZeroDivisionError."""
        zero_periods = pd.DataFrame(
            {int(CompoundAQSCode.C_BENZENE): [0.0]},
            index=pd.DatetimeIndex(["2026-01-01"]),
        )
        zero_periods.attrs["units"] = ConcentrationUnit.PPBC
        values = {int(CompoundAQSCode.C_BENZENE): 5.0}
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, zero_periods)
        assert result.iloc[0][int(CompoundAQSCode.C_BENZENE)] == 0

    def test_compound_not_in_periods_not_flagged(self, make_typed_df, sample_canister_conc):
        """Compound present in samples but absent from canister periods → not flagged."""
        # Periods only contain benzene
        partial_periods = pd.DataFrame(
            {int(CompoundAQSCode.C_BENZENE): [10.0]},
            index=pd.DatetimeIndex(["2026-01-01"]),
        )
        partial_periods.attrs["units"] = ConcentrationUnit.PPBC
        values = {
            int(CompoundAQSCode.C_BENZENE): 10.0,
            int(CompoundAQSCode.C_ETHANE): 999.0,  # would fail if checked
        }
        qc = make_typed_df(SampleType.CVS, values=values)
        result = check_qc_recovery(qc, partial_periods)
        assert result.iloc[0][int(CompoundAQSCode.C_ETHANE)] == 0

    # ------------------------------------------------------------------
    # Accepted sample types
    # ------------------------------------------------------------------

    def test_lcs_sample_type_accepted(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.LCS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert isinstance(result, pd.DataFrame)

    def test_rts_sample_type_accepted(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.RTS, values=values)
        result = check_qc_recovery(qc, canister_periods)
        assert isinstance(result, pd.DataFrame)

    # ------------------------------------------------------------------
    # Period alignment
    # ------------------------------------------------------------------

    def test_period_alignment_uses_correct_concentrations(self, make_typed_df, sample_canister_conc):
        """Early sample uses period-1 concentrations; late sample uses period-2."""
        benzene = int(CompoundAQSCode.C_BENZENE)

        # Period 1 (Jan 1): expected benzene = 10.0
        # Period 2 (Jan 15): expected benzene raised to 20.0
        two_periods = pd.DataFrame(
            {int(code): [val, val] for code, val in sample_canister_conc.items()},
            index=pd.DatetimeIndex(["2026-01-01", "2026-01-15"]),
        )
        two_periods[benzene] = [10.0, 20.0]
        two_periods.attrs["units"] = ConcentrationUnit.PPBC

        # Observed benzene = 8.0
        # Recovery vs period-1 (10.0): 80% → pass
        # Recovery vs period-2 (20.0): 40% → fail
        values = {int(code): val for code, val in sample_canister_conc.items()}
        values[benzene] = 8.0

        early = make_typed_df(SampleType.CVS, values=values, start_time="2026-01-05 08:00")
        late = make_typed_df(SampleType.CVS, values=values, start_time="2026-01-20 08:00")
        qc = pd.concat([early, late])
        qc.attrs["sample_type"] = SampleType.CVS

        result = check_qc_recovery(qc, two_periods)
        assert result.iloc[0][benzene] == 0  # Jan 5: 80% against period-1 → pass
        assert result.iloc[1][benzene] == 1  # Jan 20: 40% against period-2 → fail

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_wrong_sample_type_raises(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        ambient = make_typed_df(SampleType.AMBIENT, values=values)
        with pytest.raises(ValueError):
            check_qc_recovery(ambient, canister_periods)

    def test_blank_sample_type_raises(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        blank = make_typed_df(SampleType.BLANK, values=values)
        with pytest.raises(ValueError):
            check_qc_recovery(blank, canister_periods)

    def test_empty_df_returns_empty(self, make_typed_df, sample_canister_conc, canister_periods):
        values = {int(k): v for k, v in sample_canister_conc.items()}
        qc = make_typed_df(SampleType.CVS, values=values).iloc[0:0]
        qc.attrs["sample_type"] = SampleType.CVS
        result = check_qc_recovery(qc, canister_periods)
        assert len(result) == 0
