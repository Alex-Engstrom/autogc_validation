# -*- coding: utf-8 -*-
"""Tests for io.samples — filename parsing and SampleType enum."""

from pathlib import Path

import pytest

from autogc_validation.io.samples import SampleType, parse_filename_metadata


class TestParseFilenameMetadata:
    def test_valid_front_signal(self):
        result = parse_filename_metadata(Path("RBSJ01A something-Front Signal.cdf"))
        assert result is not None
        assert result["site"] == "RB"
        assert result["sample_type"] == "S"
        assert result["month"] == "J"
        assert result["day"] == "01"
        assert result["hour"] == "A"
        assert result["column"] == "Front Signal"

    def test_back_signal_detected(self):
        result = parse_filename_metadata(Path("RBSJ01A something-Back Signal.cdf"))
        assert result is not None
        assert result["column"] == "Back Signal"

    def test_invalid_filename_returns_none(self):
        result = parse_filename_metadata(Path("not_a_valid_file.cdf"))
        assert result is None

    def test_numeric_only_filename_returns_none(self):
        result = parse_filename_metadata(Path("12345.cdf"))
        assert result is None


class TestSampleType:
    def test_ambient_value(self):
        assert SampleType("s") == SampleType.AMBIENT

    def test_blank_value(self):
        assert SampleType("b") == SampleType.BLANK

    def test_cvs_value(self):
        assert SampleType("c") == SampleType.CVS

    def test_all_values_single_lowercase(self):
        for member in SampleType:
            assert len(member.value) == 1
            assert member.value == member.value.lower()
