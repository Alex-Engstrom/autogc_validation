# -*- coding: utf-8 -*-
"""Tests for qc.mdvr — failure interval computation."""

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("openpyxl", reason="openpyxl required for mdvr module")

from autogc_validation.qc.mdvr import compute_failure_intervals


def _make_series(values, start="2026-01-15 08:00:00", freq="h"):
    """Build a failure series (0/1) with hourly timestamps."""
    idx = pd.date_range(start, periods=len(values), freq=freq)
    return pd.Series(values, index=idx)


def _make_all_data(start="2026-01-15 08:00:00", periods=10, freq="h"):
    """Build a minimal all_data DataFrame with a datetime index."""
    idx = pd.date_range(start, periods=periods, freq=freq)
    return pd.DataFrame({"dummy": 0}, index=idx)


class TestComputeFailureIntervals:
    def test_no_failures_returns_empty(self):
        """All-pass series → empty array."""
        all_data = _make_all_data(periods=5)
        series = _make_series([0, 0, 0, 0, 0])
        result = compute_failure_intervals(all_data, series)
        assert result.shape == (0, 2)

    def test_all_failures(self):
        """All-fail series → single interval spanning the full range."""
        all_data = _make_all_data(periods=5)
        series = _make_series([1, 1, 1, 1, 1])
        result = compute_failure_intervals(all_data, series)
        assert result.shape[0] == 1
        # Bounds should be the min and max of all_data index
        assert result[0, 0] == all_data.index.min()
        assert result[0, 1] == all_data.index.max()

    def test_single_failure_bounded_by_passes(self):
        """Single failure bounded by passes on each side."""
        all_data = _make_all_data(periods=5)
        series = _make_series([0, 0, 1, 0, 0])
        result = compute_failure_intervals(all_data, series)
        assert result.shape[0] == 1
        # Left bound = last pass before failure, right bound = first pass after
        expected_left = series.index[1]   # the pass at index 1
        expected_right = series.index[3]  # the pass at index 3
        assert result[0, 0] == expected_left
        assert result[0, 1] == expected_right

    def test_multiple_disjoint_failures(self):
        """Two separated failures → two intervals."""
        all_data = _make_all_data(periods=7)
        series = _make_series([0, 1, 0, 0, 0, 1, 0])
        result = compute_failure_intervals(all_data, series)
        assert result.shape[0] == 2

    def test_adjacent_failures_merge(self):
        """Consecutive failures → single merged interval."""
        all_data = _make_all_data(periods=6)
        series = _make_series([0, 1, 1, 1, 0, 0])
        result = compute_failure_intervals(all_data, series)
        assert result.shape[0] == 1
