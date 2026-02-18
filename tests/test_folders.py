# -*- coding: utf-8 -*-
"""Tests for workspace.folders — folder structure generation."""

import pytest

from autogc_validation.workspace.folders import (
    _next_version,
    generate_monthly_folder_structure,
)


class TestNextVersion:
    def test_returns_1_when_empty(self, tmp_path):
        assert _next_version(tmp_path, "RB202601") == 1

    def test_returns_2_when_v1_exists(self, tmp_path):
        (tmp_path / "RB202601v1").mkdir()
        assert _next_version(tmp_path, "RB202601") == 2

    def test_returns_3_when_v1_v2_exist(self, tmp_path):
        (tmp_path / "RB202601v1").mkdir()
        (tmp_path / "RB202601v2").mkdir()
        assert _next_version(tmp_path, "RB202601") == 3


class TestGenerateMonthlyFolderStructure:
    def test_creates_expected_subdirs(self, tmp_path):
        result = generate_monthly_folder_structure(tmp_path, "RB", 2026, 1)
        assert result.name == "RB202601v1"
        assert (result / "AQS").is_dir()
        assert (result / "FINAL").is_dir()
        assert (result / "MDVR").is_dir()
        assert (result / "Original").is_dir()
        assert (result / "temp").is_dir()

    def test_final_contains_weeks(self, tmp_path):
        result = generate_monthly_folder_structure(tmp_path, "RB", 2026, 1)
        for i in range(1, 5):
            assert (result / "FINAL" / f"week {i}").is_dir()

    def test_auto_increments_version(self, tmp_path):
        v1 = generate_monthly_folder_structure(tmp_path, "RB", 2026, 1)
        v2 = generate_monthly_folder_structure(tmp_path, "RB", 2026, 1)
        assert v1.name == "RB202601v1"
        assert v2.name == "RB202601v2"
