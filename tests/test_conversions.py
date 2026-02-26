# -*- coding: utf-8 -*-
"""Tests for concentration unit conversions."""

import pytest
import pandas as pd

from autogc_validation.database.enums import (
    CompoundAQSCode,
    ConcentrationUnit,
    get_carbon_count,
)
from autogc_validation.conversions import (
    ppbc_to_ppbv,
    ppbv_to_ppbc,
    ppmc_to_ppmv,
    ppmv_to_ppmc,
    ppbv_to_ppmv,
    ppmv_to_ppbv,
    ppbc_to_ppmc,
    ppmc_to_ppbc,
    convert,
)


class TestGetCarbonCount:
    def test_benzene_has_6_carbons(self):
        assert get_carbon_count(int(CompoundAQSCode.C_BENZENE)) == 6

    def test_ethane_has_2_carbons(self):
        assert get_carbon_count(int(CompoundAQSCode.C_ETHANE)) == 2

    def test_toluene_has_7_carbons(self):
        assert get_carbon_count(int(CompoundAQSCode.C_TOLUENE)) == 7

    def test_unknown_code_raises(self):
        with pytest.raises(ValueError, match="not a known target compound"):
            get_carbon_count(99999)


class TestLowLevelConversions:
    def test_ppbc_to_ppbv(self):
        # 6 ppbC benzene (6 carbons) = 1 ppbV
        assert ppbc_to_ppbv(6.0, 6) == 1.0

    def test_ppbv_to_ppbc(self):
        assert ppbv_to_ppbc(1.0, 6) == 6.0

    def test_ppmc_to_ppmv(self):
        assert ppmc_to_ppmv(6.0, 6) == 1.0

    def test_ppmv_to_ppmc(self):
        assert ppmv_to_ppmc(1.0, 6) == 6.0

    def test_ppbv_to_ppmv(self):
        assert ppbv_to_ppmv(1000.0) == 1.0

    def test_ppmv_to_ppbv(self):
        assert ppmv_to_ppbv(1.0) == 1000.0

    def test_ppbc_to_ppmc(self):
        assert ppbc_to_ppmc(1000.0) == 1.0

    def test_ppmc_to_ppbc(self):
        assert ppmc_to_ppbc(1.0) == 1000.0

    def test_works_with_pandas_series(self):
        s = pd.Series([6.0, 12.0, 18.0])
        result = ppbc_to_ppbv(s, 6)
        expected = pd.Series([1.0, 2.0, 3.0])
        pd.testing.assert_series_equal(result, expected)


class TestConvert:
    def test_same_unit_returns_unchanged(self):
        result = convert(6.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPBC, ConcentrationUnit.PPBC)
        assert result == 6.0

    def test_ppbc_to_ppbv(self):
        # Benzene: 6 ppbC / 6 carbons = 1 ppbV
        result = convert(6.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPBC, ConcentrationUnit.PPBV)
        assert result == 1.0

    def test_ppbv_to_ppbc(self):
        result = convert(1.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPBV, ConcentrationUnit.PPBC)
        assert result == 6.0

    def test_ppbc_to_ppmv(self):
        # Benzene: 6000 ppbC / 6 carbons / 1000 = 1 ppmV
        result = convert(6000.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPBC, ConcentrationUnit.PPMV)
        assert result == 1.0

    def test_ppmv_to_ppbc(self):
        result = convert(1.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPMV, ConcentrationUnit.PPBC)
        assert result == 6000.0

    def test_ppbv_to_ppmc(self):
        # Benzene: 1000 ppbV * 6 carbons / 1000 = 6 ppmC
        result = convert(1000.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPBV, ConcentrationUnit.PPMC)
        assert result == 6.0

    def test_ppmc_to_ppbv(self):
        result = convert(6.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPMC, ConcentrationUnit.PPBV)
        assert result == 1000.0

    def test_ppbc_to_ppmc(self):
        result = convert(1000.0, int(CompoundAQSCode.C_BENZENE),
                         ConcentrationUnit.PPBC, ConcentrationUnit.PPMC)
        assert result == 1.0

    def test_roundtrip_ppbc_ppbv(self):
        original = 12.0
        code = int(CompoundAQSCode.C_ETHANE)
        intermediate = convert(original, code, ConcentrationUnit.PPBC, ConcentrationUnit.PPBV)
        result = convert(intermediate, code, ConcentrationUnit.PPBV, ConcentrationUnit.PPBC)
        assert result == pytest.approx(original)

    def test_unknown_aqs_code_raises(self):
        with pytest.raises(ValueError):
            convert(1.0, 99999, ConcentrationUnit.PPBC, ConcentrationUnit.PPBV)
