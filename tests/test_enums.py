# -*- coding: utf-8 -*-
"""Tests for database.enums — domain vocabulary and lookup helpers."""

import pytest

from autogc_validation.database.enums import (
    CompoundAQSCode,
    CompoundName,
    ColumnType,
    VOCCategory,
    PLOT_CODES,
    BP_CODES,
    TARGET_CODES,
    TOTAL_CODES,
    UNID_CODES,
    aqs_to_name,
    name_to_aqs,
    get_column_type,
    get_codes_by_category,
)


class TestAqsNameRoundtrip:
    def test_roundtrip_benzene(self):
        code = name_to_aqs("Benzene")
        assert aqs_to_name(code) == "Benzene"

    def test_roundtrip_ethane(self):
        code = name_to_aqs("Ethane")
        assert aqs_to_name(code) == "Ethane"

    def test_name_to_aqs_benzene(self):
        assert name_to_aqs("Benzene") == 45201

    def test_aqs_to_name_benzene(self):
        assert aqs_to_name(45201) == "Benzene"

    def test_unknown_name_raises(self):
        with pytest.raises((KeyError, ValueError)):
            name_to_aqs("NotACompound")

    def test_unknown_code_raises(self):
        with pytest.raises(ValueError):
            aqs_to_name(99999)


class TestGetColumnType:
    def test_ethane_is_plot(self):
        assert get_column_type(CompoundAQSCode.C_ETHANE) == ColumnType.PLOT

    def test_benzene_is_bp(self):
        assert get_column_type(CompoundAQSCode.C_BENZENE) == ColumnType.BP

    def test_unknown_code_raises(self):
        with pytest.raises(ValueError):
            get_column_type(99999)


class TestCodeGroupings:
    def test_plot_and_bp_disjoint(self):
        assert PLOT_CODES & BP_CODES == set()

    def test_plot_codes_non_empty(self):
        assert len(PLOT_CODES) > 0

    def test_bp_codes_non_empty(self):
        assert len(BP_CODES) > 0

    def test_target_codes_excludes_totals(self):
        for code in TOTAL_CODES:
            assert code not in TARGET_CODES

    def test_target_codes_non_empty(self):
        assert len(TARGET_CODES) > 0

    def test_unid_codes_exact(self):
        assert UNID_CODES == frozenset({10000, 20000})

    def test_total_codes_contains_tnmhc_tnmtc(self):
        assert CompoundAQSCode.C_TNMHC in TOTAL_CODES
        assert CompoundAQSCode.C_TNMTC in TOTAL_CODES


class TestGetCodesByCategory:
    def test_alkane_non_empty(self):
        codes = get_codes_by_category(VOCCategory.ALKANE)
        assert len(codes) > 0
        assert all(isinstance(c, int) for c in codes)

    def test_aromatic_contains_benzene(self):
        codes = get_codes_by_category(VOCCategory.AROMATIC)
        assert CompoundAQSCode.C_BENZENE in codes

    def test_alkene_contains_ethylene(self):
        codes = get_codes_by_category(VOCCategory.ALKENE)
        assert CompoundAQSCode.C_ETHYLENE in codes
