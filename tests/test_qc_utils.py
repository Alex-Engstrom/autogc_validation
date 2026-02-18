# -*- coding: utf-8 -*-
"""Tests for qc.utils — to_aqs_indexed_series and _safe_name_to_aqs."""

import math

import pytest
import pandas as pd

from autogc_validation.database.enums import CompoundAQSCode
from autogc_validation.qc.utils import to_aqs_indexed_series, _safe_name_to_aqs


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
